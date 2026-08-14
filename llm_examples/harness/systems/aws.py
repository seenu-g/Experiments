"""AWS-specific knowledge: boto3/EC2/S3 prompt instructions and deterministic
autofixes for known API quirks. Kept out of generate.py/resolve.py so those stay
generic Python/pipeline tooling instead of accumulating per-system business logic
-- see systems/__init__.py for how this module plugs into GENERATE and the
autofix stage.
"""

import ast

from resolve import _replace_source_span, _replace_statement_lines
from systems.config_format import CONFIG_FORMAT_INSTRUCTION

NAME = "AWS"


def matches(external_system: str) -> bool:
    return "aws" in external_system.lower()


NEEDS_CONFIG_FILE = True

SOURCE_INSTRUCTION = (
    "If the task involves AWS services via boto3, write production code with plain boto3 clients "
    "(no hardcoded endpoint_url). Store the AWS region AND credentials in the same config INI "
    "file, under keys named exactly 'region', 'aws_access_key_id', and 'aws_secret_access_key' "
    "(e.g. 'region = us-east-1', 'aws_access_key_id = your_access_key', 'aws_secret_access_key = "
    "your_secret_key' in the same section) -- the actual values are placeholders a human fills in "
    "later, but the KEYS must exist. Every boto3.client(...)/boto3.resource(...) call must pass "
    "all three explicitly -- region_name=<config value>, aws_access_key_id=<config value>, "
    "aws_secret_access_key=<config value> -- read from the config, never hardcoded directly in "
    "the boto3 call itself and never omitted. Do not rely on any of these being available some "
    "other way (environment variables, ~/.aws/config, an IAM role): there is no default region or "
    "credentials configured in this environment, so boto3 raises NoRegionError/NoCredentialsError "
    "before a call even reaches AWS (or moto, under test) if any of the three is omitted. "
    + CONFIG_FORMAT_INSTRUCTION
)

TEST_INSTRUCTION = (
    "For the unit test file, mock AWS with moto: decorate test functions/classes with a bare "
    "@mock_aws (import via 'from moto import mock_aws'), and create boto3 clients/resources "
    "inside the mocked test using region_name='us-east-1' -- moto intercepts the calls in-process, "
    "so no real AWS credentials or network access are needed. mock_aws takes NO arguments -- never "
    "write @mock_aws('s3') or @mock_aws('ec2') or any other service name as an argument; that is "
    "the old, removed per-service API (mock_s3, mock_ec2, etc., which no longer exist in moto and "
    "will raise ImportError). The single, current @mock_aws decorator mocks every AWS service "
    "generically and takes no arguments at all. If the task's entrypoint is the test file, running "
    "it under moto must fully succeed without touching real AWS. Each test must be self-contained: "
    "create every resource that test needs within that same test (never assume a resource created "
    "by a different test still exists -- test order is not guaranteed and each test may run against "
    "a fresh mock), and only ever delete/terminate a resource that this same test created -- never "
    "delete or terminate a resource you did not create yourself, even inside the mock. Every "
    "resource name/ID a test creates (bucket name, instance name, etc.) must be unique to that "
    "test -- pass it in as a variable built from a timestamp (e.g. f'test-bucket-{int(time.time())}'), "
    "never a fixed literal like 'test-bucket' reused across multiple test methods, so tests can "
    "never collide on the same resource name. If you use time.time() for this, the test file must "
    "'import time' at the top -- it is not implicitly available just because it's used elsewhere."
)


def _flatten_subscript_chain(node: ast.AST) -> list:
    """['TerminatingInstances'][0]['CurrentState']['Name'] -> ['TerminatingInstances', 0,
    'CurrentState', 'Name'] (outermost expression first). A non-constant subscript (e.g.
    a variable index) becomes None in the list -- still useful for matching a suffix/
    membership pattern even when one link in the chain isn't statically known."""
    keys = []
    while isinstance(node, ast.Subscript):
        keys.append(node.slice.value if isinstance(node.slice, ast.Constant) else None)
        node = node.value
    keys.reverse()
    return keys


def autofix_s3_us_east_1_location_constraint(files: list) -> tuple[list, list[str]]:
    """Deterministically fix a real AWS API quirk no static check can express as a plain
    "name undefined" issue: S3's create_bucket(..., CreateBucketConfiguration={
    'LocationConstraint': <region>}) raises botocore.exceptions.ClientError:
    InvalidLocationConstraint whenever <region> evaluates to 'us-east-1' at runtime --
    AWS treats 'us-east-1' as the default region and rejects it being named explicitly,
    while every OTHER region requires exactly this argument. Confirmed live against real
    moto (2026-08-14, the 20260814_203949 run): generated code that always includes
    CreateBucketConfiguration fails immediately when the configured region is us-east-1.

    Prompt instructions alone are an unreliable fix for this -- this session's local model
    has already been observed ignoring equally explicit instructions elsewhere (the
    TOOL_REGISTRY omission, the inline '(ENTRYPOINT)' header). Since the actual region
    value is only known at RUNTIME (read from a config file GENERATE has no static
    visibility into), the only fix that's correct regardless of what region ends up
    configured is to make the generated code itself branch on it at runtime -- so this
    rewrites the call into an if/else on `<region> == 'us-east-1'` rather than picking a
    single hardcoded behavior.

    Runs on the in-memory (filename, code) pairs BEFORE save/stage, same as
    resolve.autofix_stdlib_module_imports. A file with a syntax error is left untouched.

    Returns (fixed_files, fix_descriptions)."""
    fixed_files = []
    fixes = []
    for filename, code in files:
        if not filename.endswith(".py"):
            fixed_files.append((filename, code))
            continue

        try:
            tree = ast.parse(code, filename=filename)
        except SyntaxError:
            fixed_files.append((filename, code))
            continue

        # Collect matching statements bottom-to-top so earlier line numbers stay valid
        # as later-in-the-file statements get rewritten first.
        targets = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                call = node.value
                assign_prefix = f"{ast.get_source_segment(code, node.targets[0])} = "
            elif isinstance(node, ast.Return):
                call = node.value
                assign_prefix = "return "
            elif isinstance(node, ast.Expr):
                call = node.value
                assign_prefix = ""
            else:
                continue

            if not (
                isinstance(call, ast.Call)
                and isinstance(call.func, ast.Attribute)
                and call.func.attr == "create_bucket"
            ):
                continue

            bucket_kw = next((kw for kw in call.keywords if kw.arg == "Bucket"), None)
            config_kw = next((kw for kw in call.keywords if kw.arg == "CreateBucketConfiguration"), None)
            other_kws = [kw for kw in call.keywords if kw.arg not in ("Bucket", "CreateBucketConfiguration")]
            if bucket_kw is None or config_kw is None or not isinstance(config_kw.value, ast.Dict):
                continue

            region_expr = next(
                (
                    v
                    for k, v in zip(config_kw.value.keys, config_kw.value.values)
                    if isinstance(k, ast.Constant) and k.value == "LocationConstraint"
                ),
                None,
            )
            if region_expr is None:
                continue

            targets.append((node, call, assign_prefix, bucket_kw, other_kws, region_expr))

        if not targets:
            fixed_files.append((filename, code))
            continue

        targets.sort(key=lambda t: t[0].lineno, reverse=True)
        for stmt_node, call, assign_prefix, bucket_kw, other_kws, region_expr in targets:
            region_src = ast.get_source_segment(code, region_expr)
            bucket_src = ast.get_source_segment(code, bucket_kw.value)
            client_src = ast.get_source_segment(code, call.func.value)
            extra = "".join(
                f", {kw.arg}={ast.get_source_segment(code, kw.value)}" for kw in other_kws
            )
            indent = " " * stmt_node.col_offset

            replacement = (
                f"{indent}if {region_src} == 'us-east-1':\n"
                f"{indent}    {assign_prefix}{client_src}.create_bucket(Bucket={bucket_src}{extra})\n"
                f"{indent}else:\n"
                f"{indent}    {assign_prefix}{client_src}.create_bucket(Bucket={bucket_src}, "
                f"CreateBucketConfiguration={{'LocationConstraint': {region_src}}}{extra})\n"
            )
            code = _replace_statement_lines(code, stmt_node, replacement)
            fixes.append(
                f"{filename}: auto-fixed create_bucket() to branch on region -- AWS rejects an "
                f"explicit LocationConstraint for 'us-east-1' but requires it for every other region"
            )

        fixed_files.append((filename, code))

    return fixed_files, fixes


def autofix_ec2_terminate_instances_state_assertion(files: list) -> tuple[list, list[str]]:
    """Deterministically fix a real AWS async-behavior bug: terminate_instances()'s own
    IMMEDIATE response reports CurrentState as 'shutting-down', not 'terminated' --
    termination is asynchronous in real AWS (and moto, correctly emulating it), so an
    assertion expecting 'terminated' right after the call is simply wrong, not flaky.
    Confirmed live against real moto (2026-08-14, the 20260814_203949 run):
    ec2.terminate_instances(...)['TerminatingInstances'][0]['CurrentState'] was
    {'Code': 32, 'Name': 'shutting-down'} immediately after the call.

    Matches `<expr>['TerminatingInstances'][N]['CurrentState']['Name'] == 'terminated'`
    (any subscript in between, so it isn't thrown off by a literal 0 vs. a variable
    index) and rewrites the comparison to accept either valid immediate state:
    `<expr>[...] in ('shutting-down', 'terminated')`.

    Returns (fixed_files, fix_descriptions)."""
    fixed_files = []
    fixes = []
    for filename, code in files:
        if not filename.endswith(".py"):
            fixed_files.append((filename, code))
            continue

        try:
            tree = ast.parse(code, filename=filename)
        except SyntaxError:
            fixed_files.append((filename, code))
            continue

        targets = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Compare):
                continue
            if len(node.ops) != 1 or not isinstance(node.ops[0], ast.Eq):
                continue
            if len(node.comparators) != 1:
                continue
            comparator = node.comparators[0]
            if not (isinstance(comparator, ast.Constant) and comparator.value == "terminated"):
                continue

            keys = _flatten_subscript_chain(node.left)
            if keys[-2:] != ["CurrentState", "Name"] or "TerminatingInstances" not in keys:
                continue

            targets.append(node)

        if not targets:
            fixed_files.append((filename, code))
            continue

        targets.sort(key=lambda n: (n.lineno, n.col_offset), reverse=True)
        for node in targets:
            left_src = ast.get_source_segment(code, node.left)
            replacement = f"{left_src} in ('shutting-down', 'terminated')"
            code = _replace_source_span(code, node, replacement)
            fixes.append(
                f"{filename}: auto-fixed terminate_instances() state assertion -- the immediate "
                f"response reports 'shutting-down' (termination is asynchronous), not always "
                f"'terminated'"
            )

        fixed_files.append((filename, code))

    return fixed_files, fixes


AUTOFIXES = [autofix_s3_us_east_1_location_constraint, autofix_ec2_terminate_instances_state_assertion]
