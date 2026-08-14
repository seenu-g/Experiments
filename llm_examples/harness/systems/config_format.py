"""Shared, system-agnostic config-file conventions every system module composes into
its own SOURCE_INSTRUCTION when a task needs credentials/settings stored on disk.

Not itself a "system" -- no NAME/matches()/AUTOFIXES here, just the one convention
(single INI file, configparser, the <<your_KEY_NAME>> placeholder sentinel) every
system shares, so config handling stays consistent regardless of which external
system a given task touches.
"""

CONFIG_FORMAT_INSTRUCTION = (
    "Any config values (credentials, connection settings, etc.) must be stored in ONE INI file "
    "(e.g. app_config.ini) shared by whatever external systems the task involves -- AWS "
    "credentials/region and a database's credentials both belong in that same file if a task "
    "needs both, never split across separate config files. Parse it via configparser -- never a "
    "Python dict, .env, or .json file. This keeps config storage consistent and in one "
    "predictable format across tasks. If any file calls configparser's .read('app_config.ini') "
    "(or whatever you name it), that exact .ini file MUST itself be one of the files you output, "
    "with its own '# === FILE: app_config.ini ===' header and fenced block -- referencing a "
    "config file without actually outputting it is a bug: configparser.read() does not raise an "
    "error for a missing file, it silently does nothing, so the code only fails later with a "
    "confusing KeyError when a key is looked up.\n\n"
    "Every config VALUE (never the key itself) must be written in exactly this placeholder "
    "form: <<your_KEY_NAME>>, where KEY_NAME is the same name as the key it belongs to -- for "
    "example 'aws_access_key_id = <<your_aws_access_key_id>>' and 'password = "
    "<<your_password>>'. Do not invent any other placeholder style (no 'YOUR_KEY_HERE', no "
    "empty value, no fake-looking value like 'abc123' or 'AKIAIOSFODNN7EXAMPLE') -- this exact "
    "'<<your_...>>' form is the ONE format this harness recognizes as 'needs a real value "
    "before running', for every external system, not just this one."
)
