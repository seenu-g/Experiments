# code_harness

A local-model code-generation harness: you describe what you want, a local
Ollama model writes the code, and a fixed pipeline of checks decides whether
to trust it -- retrying with the failure fed back in until it passes or the
attempt budget runs out.

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

## The pipeline

```
DEFINE -> GENERATE -> SAVE -> STAGE -> LINT -> RESOLVE -> COMPILE -> VALIDATE -> EXECUTE
```

Each stage is its own file. `code_harness.py` is pure orchestration -- it
calls each stage, records the result, and decides what happens next; it
doesn't implement any stage's logic itself.

| Stage | File | What it does |
|---|---|---|
| DEFINE | `define.py` | Restates your free-text description as a structured spec (Input / Output / Steps / External System called / Tests needed) via the model, and loops until you confirm it's correct. Also applies deterministic keyword-based overrides on top of the model's own `External System called:` and `Tests needed:` classifications -- see below. |
| GENERATE | `generate.py` | Sends the confirmed spec (plus any prior failure) to the model and parses its reply into `(filename, code)` pairs. The system prompt is built dynamically: AWS/MySQL-specific instructions only appear when DEFINE detected that external system, and the test-writing instructions (moto mocking, unique timestamped test DB/user names, etc.) only appear when DEFINE decided tests are actually wanted. The base prompt (every run) also requires one function per operation (no unrequested command-string dispatcher), a test file that actually runs its own tests (`unittest.main()` or an explicit call to every bare `test_*()`), and any `.ini` config file the code reads must itself be one of the output files -- see below. |
| autofix | `resolve.py` (`autofix_stdlib_module_imports`) | Runs on GENERATE's raw `(filename, code)` pairs before anything is saved: if a file uses a bare stdlib name (e.g. `time.time()`) without importing it, the missing `import` is patched in automatically -- deterministic and unambiguous for genuine stdlib modules, so it doesn't burn a retry attempt the way an ambiguous cross-file reference has to. |
| SAVE | `save.py` | Writes every attempt -- pass or fail -- to `output/<run_id>/` under a flat, version-suffixed name (`main_v1.py`, `main_v2.py`, ...), so a failed attempt stays inspectable instead of being discarded. |
| STAGE | `save.py` (`stage_attempt`) | Writes a second, *unversioned*-filename copy into `output/<run_id>/stage_v<N>/`. Every check from here on runs against this staged copy, not the versioned save -- the generated code's own `import sibling_module` statements only resolve against the original filenames, not `sibling_module_v3.py`. |
| LINT | `lint.py` | `ast.parse()` on every staged `.py` file -- pure syntax check, no imports touched. |
| RESOLVE | `resolve.py` | Catches a hallucinated cross-file (or self-) reference: a `module.attr(...)` call where `attr` is never defined anywhere in the generated files, plus a bare `foo(...)` call that's never imported/defined, plus a `.ini` file referenced via `configparser` that was never actually generated this attempt (`configparser.read()` silently no-ops on a missing file instead of raising, so this would otherwise only surface as a confusing `KeyError` at EXECUTE). Purely AST-based, no execution. |
| COMPILE | `compile.py` | `py_compile` on every staged `.py` file -- bytecode-level check, still doesn't execute or import anything third-party. |
| VALIDATE | `validate.py` | Checks the staged code's *runtime* prerequisites before EXECUTE actually runs it: are all imported third-party libraries installed, and do any config/credential values look like placeholders the model invented? See below. |
| EXECUTE | `execute.py` | Runs the entrypoint in a subprocess (10s timeout) against the staged `stage_v<N>/` copy and captures exit code / stdout / stderr. |

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
config files code reads. Two different classes of thing can slip past both:

- **A reference to something that's never defined anywhere** -- e.g. an
  entrypoint that does `import test_database_manager` and then calls
  `test_database_manager.TestDatabaseManager()`, where `TestDatabaseManager`
  was never defined in that file or any sibling file. This is what RESOLVE
  (`resolve.py`) catches, before COMPILE or EXECUTE waste a cycle on it.
  Regenerated code *can* fix this, so a RESOLVE failure retries like a
  LINT/COMPILE failure.
- **A missing library or a placeholder credential** -- can't fail LINT/COMPILE
  either, but this is an *environment* problem, not a code problem, so it
  gets fundamentally different treatment (see next section).

VALIDATE's two checks:

- **Missing libraries** (`find_missing_libraries`): walks each file's AST for
  top-level imports, filters out sibling generated files, and checks the
  rest against `importlib.util.find_spec`. For each one missing, you're
  asked whether to `pip install` it.
- **Placeholder credentials** (`find_placeholder_config_values` for `.ini`
  files, `find_placeholder_credentials_in_py` as a fallback for `.py`
  config): flags empty values, values matching markers like `password`,
  `changeme`, `your_`, `example`, and -- for MySQL tasks specifically --
  the `user`/`password` keys unconditionally, since a fake-but-plausible
  value like `abc123` won't match any marker. You're prompted for the real
  value, which gets written into the **staged** `stage_v<N>/` copy only --
  the versioned `output/<run_id>/` save stays an untouched record of
  exactly what the model produced.

Every prompt in VALIDATE has a timeout (`config.VALIDATE_TIMEOUT_SECONDS`,
default 300s). No response in time is treated the same as declining: the
whole run stops (not just the current attempt) with a log message telling
you what to fix and that you can rerun once it's addressed -- unlike a
LINT/RESOLVE/COMPILE failure, a missing library or absent credential is an
environment problem regenerating code can't fix on its own.

### The retry loop

`code_harness.py` runs up to `config.MAX_STAGE_ATTEMPTS` versions (default
3) of GENERATE -> SAVE -> STAGE -> LINT -> RESOLVE -> COMPILE -> VALIDATE ->
EXECUTE. A LINT, RESOLVE, or COMPILE failure feeds its error back into the
next version's GENERATE call and retries; everything after the failed stage
is recorded as `SKIPPED` for that version. A VALIDATE failure stops the
whole run instead of retrying, for the reason above. The run ends in one of:

- **SUCCESS** -- some version's EXECUTE passed.
- **FAILED** -- no version passed within the attempt budget.
- **Stopped early** -- VALIDATE couldn't be satisfied.

## Output layout

```
output/<run_id>/
    main_v1.py              # versioned save of attempt 1 (or db_config_v1.ini, etc.
    lint_v1.result           #  -- one file per (filename, code) pair GENERATE returned)
    resolve_v1.result
    compile_v1.result
    validate_v1.result
    execute_v1.result
    stage_v1/                 # unversioned-filename staging copy every check runs against
        main.py
        db_config.ini          # credentials here may be edited by VALIDATE; the
                                # versioned save above is never touched
    main_v2.py
    ...
    run.log                  # full narrative of the run, mirrored to console
```

`output/` is gitignored.

## Evals

`eval_generate.py`, `eval_validate.py`, `eval_resolve.py`, `eval_lint.py`,
and `eval_input_capture.py` are plain pass/fail scripts (no framework)
covering the deterministic parsing/detection logic -- run them directly:

```bash
python eval_generate.py
python eval_validate.py
python eval_resolve.py
python eval_lint.py
python eval_input_capture.py
```

They're regression checks accumulated from real failures seen during
development (malformed model output, credentials in the wrong file format,
a misclassified external system, a hallucinated cross-file reference, a
missing stdlib import, a referenced-but-never-generated config file, an
unrequested command dispatcher, a test file that never runs its own tests,
etc.) -- see the comments at the top of each for what specific run each
case came from.
