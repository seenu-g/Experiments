# code_harness

A local-model **Python** code-generation harness: you describe what you
want, a local Ollama model writes the Python code, and a fixed pipeline of
checks (syntax, static analysis, a real bytecode compile, runtime
prerequisites, and actually executing it) decides whether to trust it --
retrying with the failure fed back in until it passes or the attempt budget
runs out.

## Requirements

- [Ollama](https://ollama.com) running locally
- The model in `config.py`'s `LOCAL_MODEL` pulled (`ollama pull qwen2.5-coder:7b`)

## Running it

```bash
cd llm_examples/harness
python code_harness.py
```

It's fully interactive: it'll ask you to describe the task, confirm the
restated spec, confirm permission to save attempts to disk, and -- if the
generated code needs something you haven't given it (a library, a real
credential) -- ask for that too.

**Tests are optional, not assumed.** If your description doesn't ask for
tests, verification, or a test client/script, DEFINE detects that (`Tests
needed: No`) and the harness only ever runs the source round -- you get
back plain Python code with no test file generated at all. Nothing extra
happens unless you actually asked for it.

## The pipeline

```
DEFINE -> GENERATE (source) -> [ GENERATE (test) ] -> LINT -> RESOLVE -> COMPILE -> VALIDATE -> EXECUTE
```

Each stage is its own file. `code_harness.py` is pure orchestration -- it
calls each stage, records the result, and decides what happens next; it
doesn't implement any stage's logic itself.

GENERATE is two ordered calls per attempt, not one:

- **Source round** writes the production code.
- **Test round** (only if `Tests needed: Yes`) writes tests grounded in the
  *actual saved source content* -- not a guess at what it might look like.

This mirrors how a person writes code-then-test, and eliminates the whole
"test references something that was never actually written" bug class.

| Stage | File | What it does |
|---|---|---|
| DEFINE | `define.py` | Restates your free-text description as a structured spec (`Input` / `Output` / `Steps` / `Test Steps` / `External System called` / `Tests needed`) via the model, and loops until you confirm it's correct. Also applies deterministic keyword-based overrides on top of the model's own `External System called:` and `Tests needed:` classifications -- see below. |
| GENERATE (source) | `generate.py` | Asks the model to write the production code. Gets a test-free spec (`Test Steps` stripped out -- see below), and AWS/MySQL-specific rules only when relevant. |
| autofix | `resolve.py` (`autofix_stdlib_module_imports`) | Auto-patches one narrow bug before anything is saved: a missing `import` for a bare stdlib name (e.g. `time.time()` without `import time`). Deterministic, so it doesn't cost a retry the way an ambiguous bug would. |
| GENERATE (test) | `generate.py` | Only runs if `Tests needed: Yes`. Asks the model to write test(s), showing it the real, already-saved source files as context (not a description of them) plus just the spec's `Test Steps`. |
| SAVE | `save.py` | Writes every attempt -- pass or fail -- to `output/<run_id>/` under a flat, version-suffixed name (`main_v1.py`, `main_v2.py`, ...), so a failed attempt stays inspectable instead of being discarded. Runs once after the source round, and again (source + test files together) after the test round. |
| STAGE | `save.py` (`stage_attempt`) | Writes a second, *unversioned*-filename copy into `output/<run_id>/stage_v<N>/`. Every check from here on runs against this staged copy, not the versioned save -- the generated code's own `import sibling_module` statements only resolve against the original filenames, not `sibling_module_v3.py`. |
| LINT | `lint.py` | `ast.parse()` on every staged `.py` file -- pure syntax check, no imports touched. Runs once for the source round's own files (stage-result name `lint`), and again for the combined source+test files after the test round (`test_lint`). |
| RESOLVE | `resolve.py` | Catches references that syntax checks can't: a call to something never actually defined anywhere, or a config file the code reads but was never generated. Purely AST-based, no execution -- see below for the three specific things it checks. Same source/test-round split as LINT (`resolve` / `test_resolve`). |
| COMPILE | `compile.py` | `py_compile` on every staged `.py` file -- bytecode-level check, still doesn't execute or import anything third-party. Same split (`compile` / `test_compile`). |
| VALIDATE | `validate.py` | Runs once, on the final combined file set. Checks what LINT/RESOLVE/COMPILE can't: is every third-party library actually installed (prompts you to `pip install` it if not), and does any credential value look real or still a placeholder the model invented (prompts you for the real value if so) -- see below. |
| EXECUTE | `execute.py` | Runs the entrypoint in a subprocess (10s timeout) against the staged `stage_v<N>/` copy and captures exit code / stdout / stderr. |

### Why the spec is split before GENERATE ever sees it

DEFINE's own restated spec can bury a test-writing step inside the `Steps`
section (e.g. "3. Write a test script named X that..."). That's a direct
conflict for the source round:

- Its **system prompt** says "don't write tests."
- Its **user message** (the spec) names a test file to write, right there
  in the same content.

A 7B local model tends to follow the concrete instruction in the user
message over the abstract one in the system message -- one real run had the
source round write a full test file itself (with its own missing `import
mysql.connector` bug) because of exactly this.

Telling the source round to "ignore" that step wasn't the fix -- a
contradiction still physically present in the prompt is still a
contradiction. Instead the spec is split before either GENERATE call ever
runs:

- `define.strip_test_content(spec)` removes the `Test Steps:` section and
  the `Tests needed:` line entirely -- the source round's prompt describes
  nothing about tests at all, not even a step to disregard.
- `define.extract_test_steps(spec)` pulls just the `Test Steps:` section's
  content -- the test round's prompt is grounded in the real source code
  (rendered via `generate._format_source_code_context`) plus only the
  test-specific part of the spec, not a repeat of the whole thing.

Both are computed once per run in `code_harness.py` and logged explicitly
(`"Source-round spec (test content stripped):"` / `"Test-round spec (Test
Steps only):"`) so the split is directly visible in `run.log`.

### DEFINE's deterministic overrides

The model's own classification of two spec fields is unreliable on this
small local model, so `define.py` corrects both with a plain keyword check
against your *raw* description rather than trusting the model's restatement
of it:

- **`External System called:`** -- has returned `None` for a prompt that
  opened with "mySQL database is on the machine". Since that field gates
  whether GENERATE gets any AWS/MySQL-specific instructions at all, a wrong
  classification silently strips all of that guidance, with real
  consequences (one run picked a different, wrong database driver --
  `sqlite3`, then `psycopg2` -- on every retry, never `mysql.connector`,
  because `MYSQL_INSTRUCTION` never got included). `_apply_external_system_override`
  scans for a keyword match (`mysql`, `aws`/service names like `ec2`/`s3`,
  case-insensitive) and corrects the spec's field if it missed something
  the raw text says outright.
- **`Tests needed:`** -- has returned `Yes` for prompts that never mention
  testing at all, silently doubling generation time/scope for tests nobody
  asked for. `_apply_needs_tests_override` scans for `test`/`testing`/
  `pytest`/`unittest` in the raw description and corrects the field in
  either direction (also catches the model under-claiming `No` when the
  user did ask for tests).

### AWS/MySQL config-completeness requirements

`AWS_INSTRUCTION`/`MYSQL_INSTRUCTION` in `generate.py` require one shared
`app_config.ini` (never split across separate files, even when a task needs
both AWS and a database) with exact, non-negotiable key names -- the values
are placeholders a human fills in later, but the keys must exist so nothing
downstream silently has no credential to read:

- **AWS**: `region`, `aws_access_key_id`, `aws_secret_access_key` -- all
  three read from config and passed explicitly into every
  `boto3.client(...)`/`boto3.resource(...)` call, never hardcoded and never
  omitted. There's no `~/.aws/config`, `AWS_DEFAULT_REGION`, or default
  credentials configured in this environment, so boto3 raises
  `NoRegionError`/`NoCredentialsError` before a call even reaches AWS (or
  moto, under test) if any of the three is missing.
- **MySQL**: `user` and `password`, named exactly that (matching
  `mysql.connector.connect()`'s keyword arguments) so the config section can
  be passed straight into `connect(**config)` without renaming keys.

VALIDATE additionally flags `aws_access_key_id`/`aws_secret_access_key` (and
MySQL's `user`/`password`) **unconditionally**, regardless of whether the
value looks like an obvious placeholder -- see below.

### AWS test-writing hardening

`AWS_TEST_INSTRUCTION` in `generate.py` accumulated several rules from real
`moto`-based test failures, each one narrowly targeting a specific observed
bug:

- **`@mock_aws` takes no arguments** -- the model has written the old,
  removed per-service API (`@mock_aws('s3')`, `mock_s3`/`mock_ec2`) which no
  longer exists in current `moto` and raises `ImportError`.
- **Tests must be self-contained** -- one run had `test_get_all_s3` fail
  because a *different* test (`test_create_delete_s3`) had already created
  and deleted the only bucket that existed; `unittest`'s alphabetical test
  order means nothing about resource lifetime should be assumed across
  tests. A test may only create the resources it needs and only ever
  delete/terminate what it itself created.
- **Resource names must be unique per test** -- a fixed literal like
  `'test-bucket'` reused across multiple test methods collides; names must
  be built from a timestamp (`f'test-bucket-{int(time.time())}'`), with an
  explicit reminder that using `time.time()` requires `import time` (the
  model has forgotten this import specifically -- now also caught
  automatically by the RESOLVE autofix above).

### Why RESOLVE and VALIDATE exist, and why LINT/COMPILE don't need them

`ast.parse()` and `py_compile` only look at syntax -- neither one actually
resolves names across files, imports third-party modules, or opens the
config files code reads. RESOLVE catches the first kind of gap (a
reference that's syntactically valid but still wrong); VALIDATE catches the
second (an environment problem, not a code problem).

**RESOLVE's three checks** (all purely AST-based, no execution; a failure
here retries like a LINT/COMPILE failure since regenerated code *can* fix
it):

- **A cross-file (or self-) reference to something never defined** -- e.g.
  an entrypoint that does `import test_database_manager` and then calls
  `test_database_manager.TestDatabaseManager()`, where `TestDatabaseManager`
  was never defined in that file or any sibling file.
- **A bare name used but never imported/defined** -- e.g. `time.time()`
  called without `import time` (this specific case is now also auto-fixed
  before RESOLVE even runs -- see "autofix" in the pipeline table above).
- **A config file referenced but never generated** -- e.g. code calls
  `configparser`'s `.read('app_config.ini')`, but no `app_config.ini` FILE
  block was ever actually output this attempt. `configparser.read()`
  doesn't raise for a missing file, it silently does nothing, so this would
  otherwise only surface as a confusing `KeyError` deep inside EXECUTE.

**VALIDATE's two checks** (an environment problem, not a code problem, so
it gets fundamentally different treatment -- see below):

- **Missing libraries** (`find_missing_libraries`): walks each file's AST for
  top-level imports, filters out sibling generated files, and checks the
  rest against `importlib.util.find_spec`. For each one missing, you're
  asked whether to `pip install` it.
- **Placeholder credentials** (`find_placeholder_config_values` for `.ini`
  files, `find_placeholder_credentials_in_py` as a fallback for `.py`
  config): flags empty values, values matching markers like `password`,
  `changeme`, `your_`, `example`, and -- unconditionally, regardless of
  marker match -- MySQL's `user`/`password` and AWS's
  `aws_access_key_id`/`aws_secret_access_key`, since a fake-but-plausible
  value like `abc123` or a made-up access key ID won't match any marker,
  and there's no point letting EXECUTE run against a real database or AWS
  with a credential nobody actually supplied. You're prompted for the real
  value, which gets written into the **staged** `stage_v<N>/` copy only --
  the versioned `output/<run_id>/` save stays an untouched record of
  exactly what the model produced.

Every prompt in VALIDATE has a timeout (`config.VALIDATE_TIMEOUT_SECONDS`,
default 300s):

- No response in time is treated the same as declining.
- The **whole run** stops, not just the current attempt -- unlike a
  LINT/RESOLVE/COMPILE failure, a missing library or absent credential is
  an environment problem regenerating code can't fix on its own.
- A log message tells you what to fix; rerun once it's addressed.

### The retry loop

`code_harness.py` runs up to `config.MAX_STAGE_ATTEMPTS` versions (default
3). Retry granularity is now 3-tiered instead of "any failure regenerates
everything":

- **Source round's own LINT/RESOLVE/COMPILE fails** -> only the source round
  regenerates next version; the test round never even runs that version.
- **Test round's own LINT/RESOLVE/COMPILE fails** -> only the test round
  regenerates next version; the already-passing source files are reused
  as-is (cached across versions, not regenerated).
- **VALIDATE or EXECUTE fails** (only reachable once both rounds' static
  checks already passed) -> ambiguous which side is actually wrong, so both
  rounds regenerate fresh next version.

A VALIDATE failure stops the whole run instead of retrying, for the reason
above. The run ends in one of:

- **SUCCESS** -- some version's EXECUTE passed.
- **FAILED** -- no version passed within the attempt budget.
- **Stopped early** -- VALIDATE couldn't be satisfied.

## Output layout

```
output/<run_id>/
    main_v1.py              # versioned save of attempt 1's source round (or app_config_v1.ini, etc.
    lint_v1.result           #  -- one file per (filename, code) pair GENERATE returned)
    resolve_v1.result
    compile_v1.result
    test_main_v1.py          # versioned save of attempt 1's test round (only if tests were needed)
    test_lint_v1.result
    test_resolve_v1.result
    test_compile_v1.result
    validate_v1.result
    execute_v1.result
    stage_v1/                 # unversioned-filename staging copy every check runs against --
        main.py                # a complete snapshot of source+test together, even on a
        app_config.ini          # test-only retry where the source files didn't change
                                # this version (credentials here may be edited by VALIDATE;
                                # the versioned save above is never touched)
    main_v2.py
    ...
    run.log                  # full narrative of the run, mirrored to console
```

`output/` is gitignored.

## Evals

`eval_generate.py`, `eval_code_harness.py`, `eval_validate.py`,
`eval_resolve.py`, `eval_lint.py`, and `eval_input_capture.py` are plain
pass/fail scripts (no framework) covering the deterministic parsing/detection
logic -- run them directly:

```bash
python eval_generate.py
python eval_code_harness.py
python eval_validate.py
python eval_resolve.py
python eval_lint.py
python eval_input_capture.py
```

`eval_code_harness.py` is the one exception to "pure unit tests" -- it runs
the real `run_harness()` end to end (real SAVE/STAGE/LINT/RESOLVE/COMPILE/
VALIDATE/EXECUTE against real files on disk) with only DEFINE, the
save-permission confirm, and the two GENERATE calls faked/injected, to prove
the retry-granularity guarantees actually hold: a test-only failure doesn't
regenerate the source round, and a source failure doesn't let the test round
run at all that version.

The rest are regression checks accumulated from real failures seen during
development (malformed model output, credentials in the wrong file format,
a misclassified external system, a hallucinated cross-file reference, a
missing stdlib import, a referenced-but-never-generated config file, an
unrequested command dispatcher, a test file that never runs its own tests,
a source round writing tests despite being told not to, missing AWS
credential keys, etc.) -- see the comments at the top of each for what
specific run each case came from.

## Possible extensions

- **Other languages.** The pipeline's *shape* (spec -> generate -> static
  checks -> runtime checks -> execute, retrying with the failure fed back
  in) is language-agnostic -- DEFINE, SAVE/STAGE, and the retry loop already
  don't care what language the output is. LINT/RESOLVE/COMPILE/VALIDATE/
  EXECUTE are the parts that would need real rework, since they're built
  directly on Python-only tooling (`ast`, `py_compile`, `importlib`,
  `sys.executable`) with no drop-in equivalent -- e.g. Roslyn for C#'s
  AST/compile checks, `libclang`/`gcc` for C's. The model itself
  (`qwen2.5-coder:7b`) already writes reasonable C/C++/C#, so it wouldn't
  need to change.
- **Per-file GENERATE rounds.** Today's two-round split (source, then test)
  only grounds the *test* round in real saved code -- multiple source files
  in the same round can still hallucinate references to each other, caught
  only after the fact by RESOLVE's `check_undefined_module_references`,
  which retries the whole source round. A stricter per-file round (each
  file's GENERATE call sees every sibling file already written before it)
  would close that gap the same way the source/test split closed its own,
  at the cost of dependency-ordering multiple production files instead of
  just two categories.
- **A real symbol-resolution tool in place of RESOLVE's hand-rolled checks.**
  `resolve.py`'s undefined-name/undefined-reference checks are a manual
  approximation built on `ast` alone -- `ast` only gives a syntax tree, no
  symbol table, so RESOLVE has to walk it and collect "every name bound
  anywhere in this file" itself (explicitly documented as a "scope-blind
  union," not real per-function/per-class scoping). Tools like **Pyflakes**
  (the closest direct swap-in -- same job, but with a real scope stack),
  **Pyright** (the closest Python equivalent to what Roslyn gives C#: a
  real binder/semantic model with cross-file resolution and type
  inference), **mypy** (real semantic analysis too, but packaged as a type
  checker first -- an awkward fit for symbol resolution alone), and
  **Jedi** (an importable Python *library* rather than a CLI, callable
  in-process from `resolve.py` directly) already solve this properly.
