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

Every `ollama.chat()` call across DEFINE/PLAN/GENERATE passes an explicit
`keep_alive` (`config.OLLAMA_KEEP_ALIVE`, default `"30m"`) instead of relying
on Ollama's own 5-minute idle default -- one full iteration makes several
separate calls, and without this, a longer generation or a slow confirmation
pause between them risks the model being unloaded and paying a full reload
cost on the next call.

## Running it

```bash
cd llm_examples/harness
python code_harness.py
```

You're always asked to describe the task, and -- if the generated code needs
something you haven't given it (a library, a real credential) -- VALIDATE
still asks for that too (see below; those prompts genuinely need a real
answer, so they're unaffected by the flag below).

**Non-interactive by default otherwise.** The DEFINE spec, PLAN's file
manifest, and the SAVE-permission checkpoint all auto-confirm rather than
waiting on real y/N input, so one full DEFINE -> PLAN -> GENERATE -> ... ->
EXECUTE iteration runs straight through instead of pausing for a human at
each stage. The confirmed spec/plan text is still written to `run.log`
either way -- only the wait is skipped. Pass `--interactive` to get real
confirmation prompts back (useful while you're still learning how a stage's
output looks, less useful once you trust the loop):

```bash
python code_harness.py --interactive
```

**Tests are optional, not assumed.** If your description doesn't ask for
tests, verification, or a test client/script, DEFINE detects that (`Tests
needed: No`) and the harness only ever runs the source round -- you get
back plain Python code with no test file generated at all. Nothing extra
happens unless you actually asked for it.

## The pipeline

```
DEFINE -> PLAN -> GENERATE (source) -> [ GENERATE (test) ] -> LINT -> RESOLVE -> COMPILE -> VALIDATE -> EXECUTE
```

Each stage is its own file. `code_harness.py` is pure orchestration -- it
calls each stage, records the result, and decides what happens next; it
doesn't implement any stage's logic itself.

**Per-system knowledge lives in its own module, not in the pipeline files.**
`generate.py`, `resolve.py`, and `plan.py` are generic Python/architecture
tooling -- they know nothing about AWS, MySQL, or Ollama specifically. Each
external system's prompt instructions and deterministic autofixes live in
`systems/<name>.py` instead (`systems/aws.py`, `systems/mysql.py`,
`systems/ollama.py`, `systems/langchain.py`), each exposing the same shape
(`NAME`, `matches(external_system)`, `NEEDS_CONFIG_FILE`, `SOURCE_INSTRUCTION`,
`TEST_INSTRUCTION`, `AUTOFIXES`). The pipeline files dispatch generically over
`systems.ALL_SYSTEMS` instead of hardcoding `if "aws" in external_system.lower()`
branches everywhere -- adding a new system means adding one new module under
`systems/` and one line in `systems/__init__.py`, not touching GENERATE,
RESOLVE, or PLAN at all. Evals mirror the same split: system-specific eval
cases live in `systems/eval_<name>.py`, run via `python -m systems.eval_<name>`
(needs `-m` so both `harness/` and `systems/` resolve on `sys.path`); the
pipeline files' own evals (`eval_generate.py`, `eval_resolve.py`, `eval_plan.py`)
only cover generic, system-agnostic behavior.

GENERATE is two ordered calls per attempt, not one:

- **Source round** writes the production code.
- **Test round** (only if `Tests needed: Yes`) writes tests grounded in the
  *actual saved source content* -- not a guess at what it might look like.

This mirrors how a person writes code-then-test, and eliminates the whole
"test references something that was never actually written" bug class.

| Stage | File | What it does |
|---|---|---|
| DEFINE | `define.py` | Restates your free-text description as a structured spec (`Input` / `Output` / `Steps` / `Test Steps` / `External System called` / `Tests needed`) via the model, and loops until you confirm it's correct. Also applies deterministic keyword-based overrides on top of the model's own `External System called:` and `Tests needed:` classifications -- see below. |
| PLAN | `plan.py` | Restates the confirmed spec as a concrete file manifest -- one block per planned file (`FILE` / `PURPOSE` / `FUNCTIONS` / `ENTRYPOINT` / `ROUND: source or test`) -- and loops until you confirm it. Becomes a fixed contract for the whole run: `check_plan_conformance` (in `resolve.py`) later verifies GENERATE's actual output against it, catching a promised-but-missing file/function immediately after GENERATE instead of possibly not until EXECUTE. Deliberately loose on everything else -- extra helper functions, extra files, and different implementation details are all fine; only "promised but missing" is flagged, so normal model variation between retries doesn't fight it. |
| GENERATE (source) | `generate.py` | Asks the model to write the production code. Gets a test-free spec (`Test Steps` stripped out -- see below), AWS/MySQL/Ollama/LangChain-specific rules only when relevant, and the PLAN's source-file subset rendered as context (`_format_plan_context`). |
| autofix | `resolve.py` + `systems/*.py` | Four deterministic, no-retry-cost patches applied to GENERATE's raw output before anything is saved -- see "Deterministic autofixes" below. |
| GENERATE (test) | `generate.py` | Only runs if `Tests needed: Yes`. Asks the model to write test(s), showing it the real, already-saved source files as context (not a description of them), the spec's `Test Steps`, and the PLAN's test-file subset. |
| SAVE | `save.py` | Writes every attempt -- pass or fail -- to `output/<run_id>/` under a flat, version-suffixed name (`main_v1.py`, `main_v2.py`, ...), so a failed attempt stays inspectable instead of being discarded. Runs once after the source round, and again (source + test files together) after the test round. |
| STAGE | `save.py` (`stage_attempt`) | Writes a second, *unversioned*-filename copy into `output/<run_id>/stage_v<N>/`. Every check from here on runs against this staged copy, not the versioned save -- the generated code's own `import sibling_module` statements only resolve against the original filenames, not `sibling_module_v3.py`. |
| LINT | `lint.py` | `ast.parse()` on every staged `.py` file -- pure syntax check, no imports touched. Runs once for the source round's own files (stage-result name `lint`), and again for the combined source+test files after the test round (`test_lint`). |
| RESOLVE | `resolve.py` | Catches references that syntax checks can't: a call to something never actually defined anywhere, a config file the code reads but was never generated, or a PLAN-promised file/function GENERATE silently dropped. Purely AST-based, no execution -- see below for the four specific things it checks. Same source/test-round split as LINT (`resolve` / `test_resolve`). |
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

**RESOLVE's four checks** (all purely AST-based, no execution; a failure
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
- **A PLAN-promised file or function that's missing from the actual output**
  (`check_plan_conformance`, opt-in via `planned_files`) -- the source
  round's output is checked against the PLAN's source-file subset, the test
  round's against its test-file subset, each riding that round's own
  retry (a source-round conformance failure doesn't regenerate the test
  round, and vice versa).

**VALIDATE's two checks** (an environment problem, not a code problem, so
it gets fundamentally different treatment -- see below):

- **Missing libraries** (`find_missing_libraries`): walks each file's AST for
  top-level imports, filters out sibling generated files, and checks the
  rest against `importlib.util.find_spec`. For each one missing, you're
  asked whether to `pip install` it.
- **Placeholder credentials** (`find_placeholder_config_values` for `.ini`
  files, `find_placeholder_credentials_in_py` as a fallback for `.py`
  config): flags empty values, values matching markers like `password`,
  `changeme`, `your_`, `example`, GENERATE's own deterministic
  `<<your_KEY_NAME>>` sentinel (see below), and -- unconditionally,
  regardless of marker match -- MySQL's `user`/`password` and AWS's
  `aws_access_key_id`/`aws_secret_access_key`, since a fake-but-plausible
  value like `abc123` or a made-up access key ID won't match any marker,
  and there's no point letting EXECUTE run against a real database or AWS
  with a credential nobody actually supplied. You're prompted for the real
  value, which gets written into the **staged** `stage_v<N>/` copy only --
  the versioned `output/<run_id>/` save stays an untouched record of
  exactly what the model produced.

**The `<<your_KEY_NAME>>` placeholder sentinel.** The marker-word list above
is a heuristic guess -- it can both miss a model-invented placeholder that
doesn't happen to contain any of those words, and wrongly flag a genuinely
real value that happens to contain one (e.g. a URL field containing
`example.com`). `CONFIG_FORMAT_INSTRUCTION` (in `generate.py`, shared by
every system that touches config -- AWS, MySQL, and anything added later)
requires GENERATE to write every config value in exactly one deterministic
form: `<<your_KEY_NAME>>`, e.g. `aws_access_key_id = <<your_aws_access_key_id>>`.
`validate._PLACEHOLDER_SENTINEL_RE` checks for this exact shape as an
additional, more precise signal -- **additive to, not a replacement for**,
the marker-word list, since the model following any prompt instruction is
still probabilistic, not guaranteed.

Every prompt in VALIDATE has a timeout (`config.VALIDATE_TIMEOUT_SECONDS`,
default 300s):

- No response in time is treated the same as declining.
- The **whole run** stops, not just the current attempt -- unlike a
  LINT/RESOLVE/COMPILE failure, a missing library or absent credential is
  an environment problem regenerating code can't fix on its own.
- A log message tells you what to fix; rerun once it's addressed.

### Deterministic autofixes

Four narrow, unambiguous bug classes are patched before anything is saved,
rather than fed back as `error_context` for a retry -- in each case there's
nothing for a regenerate-and-retry attempt to usefully *decide*, so patching
costs nothing and a retry would only waste one of the run's limited attempts.
`code_harness.py` runs `resolve.autofix_stdlib_module_imports` and
`resolve.autofix_undefined_sibling_module_imports` (both generic,
language-level) plus every system's own `AUTOFIXES` from `systems.ALL_SYSTEMS`
(system-specific, API-level) on every attempt:

- **`resolve.autofix_stdlib_module_imports`** -- a bare `X.attr` usage (e.g.
  `time.time()`) where `X` is missing but IS a genuine stdlib module.
  `import X` is the only possible fix.
- **`resolve.autofix_undefined_sibling_module_imports`** -- the same idea, for
  a SIBLING GENERATED FILE instead of a stdlib module, in the two shapes it's
  actually shown up: `logger.log_operation(...)` used but `logger` never
  imported (-> `import logger`, unambiguous since the module name is already
  named in the code), and a bare `log_action(...)` call where exactly one
  sibling file defines `log_action` at module level (-> `from logger import
  log_action`; left alone if 2+ siblings define the same name, since that's
  genuinely ambiguous). For the test round, the files it's allowed to import
  from include the already-saved source files, not just the test files
  themselves.
- **`systems.aws.autofix_s3_us_east_1_location_constraint`** -- a real AWS API quirk:
  `create_bucket(..., CreateBucketConfiguration={'LocationConstraint':
  region})` raises `ClientError: InvalidLocationConstraint` whenever
  `region` is `'us-east-1'` at runtime (AWS treats it as the default region
  and rejects it being named explicitly), while every *other* region
  requires exactly that argument. Since the region value is only known at
  runtime (read from a config file GENERATE never sees the contents of),
  the only fix that's correct regardless of what gets configured is
  rewriting the call into a runtime `if region == 'us-east-1': ... else:
  ...` branch -- confirmed against real `moto` for both cases.
- **`systems.aws.autofix_ec2_terminate_instances_state_assertion`** -- a real AWS
  async-behavior bug: `terminate_instances()`'s own *immediate* response
  reports `CurrentState` as `'shutting-down'`, never `'terminated'`
  (termination is asynchronous, confirmed against real `moto`), so a test
  asserting `== 'terminated'` right after the call is simply wrong, not
  flaky. Rewrites the specific `[...]['TerminatingInstances'][N]
  ['CurrentState']['Name'] == 'terminated'` pattern to accept either valid
  immediate state, without touching an unrelated comparison that happens to
  also mention `'terminated'`.

All four were adopted over the equivalent prompt-instruction approach
deliberately -- this session's local model has already been observed
ignoring equally explicit prompt instructions elsewhere (omitting
`TOOL_REGISTRY` despite being told not to redefine it, folding an
`(ENTRYPOINT)` marker inline against the documented format). A prompt
addition is only ever probabilistic; an AST-level rewrite is guaranteed.

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

`eval_plan.py`, `eval_generate.py`, `eval_code_harness.py`, `eval_validate.py`,
`eval_resolve.py`, `eval_lint.py`, `eval_input_capture.py`, and `eval_confirm.py`
are plain pass/fail scripts (no framework) covering the pipeline's own generic,
system-agnostic logic -- run them directly:

```bash
python eval_plan.py
python eval_generate.py
python eval_code_harness.py
python eval_validate.py
python eval_resolve.py
python eval_lint.py
python eval_input_capture.py
python eval_confirm.py
```

Per-system eval cases (AWS/MySQL/Ollama/LangChain instructions and autofixes)
live under `systems/` and run as modules, from the `harness/` directory, so
both `harness/` and `systems/` resolve on `sys.path`:

```bash
python -m systems.eval_config_format
python -m systems.eval_aws
python -m systems.eval_mysql
python -m systems.eval_ollama_langchain
```

`systems/eval_aws.py`'s autofix cases don't stop at checking the rewritten
code is syntactically valid -- the S3 and EC2 autofix cases actually execute
the rewritten function against real `moto`, proving the fix genuinely
resolves the AWS error rather than just parsing.

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
credential keys, a PLAN-promised file/function silently dropped by GENERATE,
a FILE header format deviation that silently merged two files into one, a
multi-parameter function signature mis-split into several bogus planned
functions, the S3 `us-east-1` `LocationConstraint` error, the EC2
`terminate_instances` async-state assertion, a sibling generated file (e.g.
`logger.py`) used but never imported (in both the `module.attr(...)` and
bare-call shapes), and a PLAN reply drifting mid-response from the instructed
plain `FILE: X` header into GENERATE's own `# === FILE: X ===` style, which
silently dropped every file block after the first, etc.) -- see the comments
at the top of each for what specific run each case came from.

## Possible extensions

- **Per-file GENERATE rounds.** Today's two-round split (source, then test)
  only grounds the *test* round in real saved code -- multiple source files
  in the same round can still hallucinate references to each other, caught
  only after the fact by RESOLVE's `check_undefined_module_references`,
  which retries the whole source round. A stricter per-file round (each
  file's GENERATE call sees every sibling file already written before it)
  would close that gap the same way the source/test split closed its own,
  at the cost of dependency-ordering multiple production files instead of
  just two categories. Designed (not yet built) in
  `source-file-dependency-retry-granularity.md`, which extends PLAN's file
  manifest with a `depends_on` field for exactly this -- currently blocked
  on real-world use of the PLAN stage settling first. One file-count call
  per source file instead of one call for the whole round multiplies how
  many gaps exist for Ollama's idle timer to expire between them, so
  `config.OLLAMA_KEEP_ALIVE` (added to cover today's DEFINE/PLAN/GENERATE
  gaps) becomes more load-bearing here, not just a nice-to-have -- worth
  re-checking its value is still long enough once this actually ships.
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
- **Supporting other models.** Everything today is built and tuned around one
  fixed local model (`config.LOCAL_MODEL`, `qwen2.5-coder:7b`) -- needs
  exploring whether other locally-runnable models (e.g. Hermes, Microsoft
  Phi-3 -- placeholders, not evaluated yet) could be used instead or offered
  as a choice. Open questions, not yet answered: does the FILE-header/
  ENTRYPOINT protocol GENERATE relies on (`generate.py`'s `FILE_HEADER_RE`/
  `ENTRY_MARKER_RE`) hold up against a differently-trained model's own
  formatting habits, or would it reproduce the same class of deviation the
  inline `(ENTRYPOINT)` bug did; does a different model's tool-calling
  support change what `systems/ollama.py`'s `OLLAMA_INSTRUCTION` needs to
  say; and would `config.OLLAMA_KEEP_ALIVE`/timeout defaults tuned against
  this one model's CPU-inference speed still make sense for a
  faster-or-slower one.
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
