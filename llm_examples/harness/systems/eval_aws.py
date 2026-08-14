"""Eval for systems/aws.py: prompt instructions (SOURCE_INSTRUCTION/TEST_INSTRUCTION)
and the two deterministic autofixes (S3 us-east-1 LocationConstraint, EC2
terminate_instances state assertion).

Run (from the harness/ directory): python -m systems.eval_aws
"""

import ast
import importlib.util
import os
import sys
import tempfile

import boto3
from moto import mock_aws

from generate import build_source_system_instruction, build_test_system_instruction
from systems.aws import (
    SOURCE_INSTRUCTION as AWS_INSTRUCTION,
    TEST_INSTRUCTION as AWS_TEST_INSTRUCTION,
    autofix_ec2_terminate_instances_state_assertion,
    autofix_s3_us_east_1_location_constraint,
)


def check(label, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {label}" + (f" -- {detail}" if detail and not condition else ""))
    return condition


def _write_tmp(filename, code):
    path = os.path.join(tempfile.mkdtemp(), filename)
    with open(path, "w") as f:
        f.write(code)
    return path


def eval_aws_instruction_gated_by_external_system():
    """AWS's SOURCE_INSTRUCTION must appear only when external_system actually
    mentions AWS -- verified through generate.py's real dispatch (build_source_
    system_instruction), the integration point systems.aws plugs into."""
    ok = True
    ok &= check(
        "AWS block included when external_system=AWS",
        AWS_INSTRUCTION in build_source_system_instruction(external_system="AWS"),
    )
    ok &= check(
        "AWS block excluded when external_system=MySQL",
        AWS_INSTRUCTION not in build_source_system_instruction(external_system="MySQL"),
    )
    ok &= check(
        "AWS block excluded when external_system=None",
        AWS_INSTRUCTION not in build_source_system_instruction(external_system="None"),
    )
    ok &= check(
        "AWS block excluded when external_system=''",
        AWS_INSTRUCTION not in build_source_system_instruction(external_system=""),
    )
    return ok


def eval_aws_instruction_requires_region_and_credentials():
    """Regression check for the 2026-08-13 20260813_003655 run and a follow-up gap found in
    the same instruction: ec2_manager.py's boto3.client('ec2') calls never passed region_name,
    and this machine has no ~/.aws/config or AWS_DEFAULT_REGION set -- botocore.exceptions.
    NoRegionError fired before the call even reached moto's mocking. AWS_TEST_INSTRUCTION
    already told the model to use region_name in the TEST file's own client creation, but
    AWS_INSTRUCTION (source code) said nothing about region -- or credentials -- at all.

    The credentials half: even once region_name was required, boto3.client('ec2',
    region_name=...) still never passed aws_access_key_id/aws_secret_access_key, so the
    'config file with credentials' the task asked for ended up only ever holding a region.
    Harmless under moto (which injects dummy credentials regardless), but the generated code
    would never authenticate against real AWS. Fixed the same way MYSQL_INSTRUCTION already
    requires 'user'/'password' by exact key name. Both region and credentials are the same
    underlying config-completeness requirement, so they're checked together here."""
    ok = True
    source = build_source_system_instruction(external_system="AWS")

    ok &= check(
        "source AWS prompt requires region_name on every client",
        "region_name" in source and "NoRegionError" in source,
        source,
    )
    ok &= check(
        "region must be read from the config file, not hardcoded in the boto3 call",
        "region = us-east-1" in source and "config" in source.lower(),
        source,
    )
    ok &= check(
        "instruction requires exact credential key names in the config file",
        "aws_access_key_id" in source and "aws_secret_access_key" in source,
        source,
    )
    ok &= check(
        "instruction requires every boto3 call to pass all three explicitly",
        "aws_access_key_id=<config value>" in source and "aws_secret_access_key=<config value>" in source,
        source,
    )
    ok &= check(
        "instruction warns about NoCredentialsError, not just NoRegionError",
        "NoCredentialsError" in source,
        source,
    )
    return ok


def eval_aws_test_instruction_forbids_deprecated_moto_api():
    """Regression check for the 2026-08-12 20260812_235607 run: the model wrote
    @mock_aws('s3') and @mock_aws('ec2') across all 3 attempts -- neither the old,
    removed per-service moto API (mock_s3, mock_ec2) nor the current bare-decorator
    one. The original AWS_TEST_INSTRUCTION only said HOW to use mock_aws
    correctly; it never said what NOT to do, so the model wasn't warned off
    either wrong pattern."""
    ok = True
    test_instruction = build_test_system_instruction(external_system="AWS")
    ok &= check(
        "instruction explicitly forbids @mock_aws(...) with an argument",
        "mock_aws('s3')" in test_instruction or "no arguments" in test_instruction.lower(),
        test_instruction,
    )
    ok &= check(
        "instruction explicitly names the removed per-service decorators",
        "mock_s3" in test_instruction and "mock_ec2" in test_instruction,
        test_instruction,
    )
    return ok


def eval_aws_test_instruction_requires_self_contained_tests():
    """Regression check for the 2026-08-13 20260813_003655 run: test_get_all_s3
    failed with 'False is not true' because test_create_delete_s3 created then
    deleted 'test-bucket' before test_get_all_s3 ran (alphabetical unittest
    order), so the bucket test_get_all_s3 expected to find was already gone --
    it assumed state left behind by a different test instead of creating its
    own. AWS_TEST_INSTRUCTION said how to mock AWS but never said tests must be
    self-contained or that a test may only delete what it itself created."""
    ok = True
    test_instruction = build_test_system_instruction(external_system="AWS")
    ok &= check(
        "instruction requires each test to create its own resources",
        "self-contained" in test_instruction.lower(),
        test_instruction,
    )
    ok &= check(
        "instruction forbids deleting/terminating resources a test didn't create",
        "did not create" in test_instruction.lower() or "didn't create" in test_instruction.lower(),
        test_instruction,
    )
    ok &= check(
        "instruction requires a time-based unique resource name per test",
        "int(time.time())" in test_instruction,
        test_instruction,
    )
    ok &= check(
        "instruction forbids a fixed literal resource name reused across tests",
        "reused across multiple test methods" in test_instruction,
        test_instruction,
    )
    ok &= check(
        "instruction explicitly requires 'import time' when using time.time() for the name",
        "'import time'" in test_instruction,
        test_instruction,
    )
    return ok


def eval_needs_tests_gates_aws_test_instruction():
    """After the two-round GENERATE split, needs_tests no longer gates prompt
    CONTENT -- it gates whether round 2 runs at all (see code_harness.py). The
    source builder never includes AWS's TEST_INSTRUCTION; the test builder
    always includes it when the external system matches, since round 2 only
    ever runs when tests are needed in the first place."""
    ok = True
    ok &= check(
        "AWS source instruction present",
        AWS_INSTRUCTION in build_source_system_instruction(external_system="AWS"),
    )
    ok &= check(
        "AWS test instruction (moto) never appears in the source builder's output",
        AWS_TEST_INSTRUCTION not in build_source_system_instruction(external_system="AWS"),
    )
    ok &= check(
        "AWS test instruction (moto) included in the test builder's output",
        AWS_TEST_INSTRUCTION in build_test_system_instruction(external_system="AWS"),
    )
    return ok


def eval_autofix_s3_location_constraint_rewrites_call():
    """Regression check for the 2026-08-14 20260814_203949 run: generated code always
    passed CreateBucketConfiguration={'LocationConstraint': region} to create_bucket(),
    which raises botocore.exceptions.ClientError: InvalidLocationConstraint whenever the
    configured region is 'us-east-1' (confirmed live against real moto -- see
    stage_v1/s3_manager.py from that run). The region is only known at runtime (read
    from a config file), so the fix must be a runtime branch, not a static choice."""
    code = (
        "import boto3\n\n"
        "def create_bucket(s3_client, bucket_name, region):\n"
        "    response = s3_client.create_bucket(\n"
        "        Bucket=bucket_name,\n"
        "        CreateBucketConfiguration={'LocationConstraint': region}\n"
        "    )\n"
        "    return response\n"
    )
    fixed_files, fixes = autofix_s3_us_east_1_location_constraint([("s3_manager.py", code)])
    fixed_code = fixed_files[0][1]

    ok = True
    ok &= check("a fix description is returned", len(fixes) == 1, fixes)
    ok &= check(
        "rewritten code branches on region == 'us-east-1'",
        "if region == 'us-east-1':" in fixed_code,
        fixed_code,
    )
    ok &= check(
        "the us-east-1 branch omits CreateBucketConfiguration entirely",
        "create_bucket(Bucket=bucket_name)" in fixed_code,
        fixed_code,
    )
    ok &= check(
        "the else branch still passes CreateBucketConfiguration for every other region",
        "CreateBucketConfiguration={'LocationConstraint': region}" in fixed_code,
        fixed_code,
    )

    try:
        ast.parse(fixed_code)
        parses = True
    except SyntaxError:
        parses = False
    ok &= check("rewritten code is valid Python (ast.parse succeeds)", parses)
    return ok


def eval_autofix_s3_location_constraint_functionally_correct_under_moto():
    """Stronger than a syntax check: actually run the rewritten function against real
    moto for both 'us-east-1' and a non-default region, proving the fix isn't just
    syntactically valid but genuinely resolves the ClientError for both cases."""
    code = (
        "import boto3\n\n"
        "def create_bucket(s3_client, bucket_name, region):\n"
        "    response = s3_client.create_bucket(\n"
        "        Bucket=bucket_name,\n"
        "        CreateBucketConfiguration={'LocationConstraint': region}\n"
        "    )\n"
        "    return response\n"
    )
    fixed_files, _ = autofix_s3_us_east_1_location_constraint([("s3util_eval.py", code)])
    path = _write_tmp("s3util_eval.py", fixed_files[0][1])

    spec = importlib.util.spec_from_file_location("s3util_eval", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["s3util_eval"] = module
    spec.loader.exec_module(module)

    @mock_aws
    def _run():
        results = {}
        for region in ("us-east-1", "eu-west-1"):
            client = boto3.client(
                "s3", region_name=region, aws_access_key_id="x", aws_secret_access_key="y"
            )
            response = module.create_bucket(client, f"bucket-{region}", region)
            results[region] = response["ResponseMetadata"]["HTTPStatusCode"]
        return results

    try:
        results = _run()
        ok = True
        ok &= check(
            "us-east-1 bucket creation succeeds (no InvalidLocationConstraint)",
            results.get("us-east-1") == 200,
            results,
        )
        ok &= check(
            "eu-west-1 bucket creation still succeeds (LocationConstraint still passed)",
            results.get("eu-west-1") == 200,
            results,
        )
    except Exception as e:
        ok = check("rewritten code runs against real moto without error", False, str(e))
    finally:
        sys.modules.pop("s3util_eval", None)

    return ok


def eval_autofix_s3_location_constraint_skips_files_without_the_pattern():
    code = "def create_bucket(s3_client, bucket_name):\n    return s3_client.create_bucket(Bucket=bucket_name)\n"
    fixed_files, fixes = autofix_s3_us_east_1_location_constraint([("plain.py", code)])
    ok = True
    ok &= check("no fix applied when the pattern isn't present", fixes == [])
    ok &= check("file content unchanged", fixed_files[0][1] == code)
    return ok


def eval_autofix_ec2_terminate_assertion_rewrites_comparison():
    """Regression check for the 2026-08-14 20260814_203949 run: the generated test
    asserted CurrentState['Name'] == 'terminated' right after terminate_instances(),
    but that call's IMMEDIATE response reports 'shutting-down' (confirmed live against
    real moto -- termination is asynchronous in real AWS). The assertion itself was
    wrong, not the code under test."""
    code = (
        "def test_delete_ec2_instance():\n"
        "    instance_id = create_ec2_instance('t2.micro', 'key')\n"
        "    delete_response = delete_ec2_instance(instance_id)\n"
        "    assert delete_response['TerminatingInstances'][0]['CurrentState']['Name'] == 'terminated'\n"
    )
    fixed_files, fixes = autofix_ec2_terminate_instances_state_assertion([("test_ec2.py", code)])
    fixed_code = fixed_files[0][1]

    ok = True
    ok &= check("a fix description is returned", len(fixes) == 1, fixes)
    ok &= check(
        "rewritten assertion accepts either valid immediate state",
        "in ('shutting-down', 'terminated')" in fixed_code,
        fixed_code,
    )
    ok &= check("the 'assert' keyword is preserved", "assert delete_response" in fixed_code, fixed_code)
    ok &= check(
        "the original == 'terminated' comparison is gone",
        "== 'terminated'" not in fixed_code,
        fixed_code,
    )

    try:
        ast.parse(fixed_code)
        parses = True
    except SyntaxError:
        parses = False
    ok &= check("rewritten code is valid Python (ast.parse succeeds)", parses)
    return ok


def eval_autofix_ec2_terminate_assertion_functionally_correct_under_moto():
    """Actually runs the rewritten assertion against a real moto terminate_instances()
    response, proving it no longer raises AssertionError."""
    code = (
        "def check_state(response):\n"
        "    assert response['TerminatingInstances'][0]['CurrentState']['Name'] == 'terminated'\n"
        "    return True\n"
    )
    fixed_files, _ = autofix_ec2_terminate_instances_state_assertion([("check_state.py", code)])
    path = _write_tmp("check_state.py", fixed_files[0][1])

    spec = importlib.util.spec_from_file_location("check_state_eval", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["check_state_eval"] = module
    spec.loader.exec_module(module)

    @mock_aws
    def _run():
        client = boto3.client(
            "ec2", region_name="us-east-1", aws_access_key_id="x", aws_secret_access_key="y"
        )
        run_response = client.run_instances(
            ImageId="ami-12345678", MinCount=1, MaxCount=1, InstanceType="t2.micro"
        )
        instance_id = run_response["Instances"][0]["InstanceId"]
        terminate_response = client.terminate_instances(InstanceIds=[instance_id])
        return module.check_state(terminate_response)

    try:
        result = _run()
        ok = check("rewritten assertion passes against a real moto terminate_instances() response", result is True)
    except AssertionError:
        ok = check(
            "rewritten assertion passes against a real moto terminate_instances() response", False
        )
    finally:
        sys.modules.pop("check_state_eval", None)

    return ok


def eval_autofix_ec2_terminate_assertion_skips_unrelated_comparisons():
    """Must not touch an unrelated '== \"terminated\"' comparison that doesn't match the
    TerminatingInstances/CurrentState/Name shape -- e.g. a different resource's status
    string that happens to also use the word 'terminated'."""
    code = "def check(task):\n    assert task['status'] == 'terminated'\n"
    fixed_files, fixes = autofix_ec2_terminate_instances_state_assertion([("unrelated.py", code)])
    ok = True
    ok &= check("no fix applied to an unrelated comparison", fixes == [])
    ok &= check("file content unchanged", fixed_files[0][1] == code)
    return ok


if __name__ == "__main__":
    results = [
        eval_aws_instruction_gated_by_external_system(),
        eval_aws_instruction_requires_region_and_credentials(),
        eval_aws_test_instruction_forbids_deprecated_moto_api(),
        eval_aws_test_instruction_requires_self_contained_tests(),
        eval_needs_tests_gates_aws_test_instruction(),
        eval_autofix_s3_location_constraint_rewrites_call(),
        eval_autofix_s3_location_constraint_functionally_correct_under_moto(),
        eval_autofix_s3_location_constraint_skips_files_without_the_pattern(),
        eval_autofix_ec2_terminate_assertion_rewrites_comparison(),
        eval_autofix_ec2_terminate_assertion_functionally_correct_under_moto(),
        eval_autofix_ec2_terminate_assertion_skips_unrelated_comparisons(),
    ]
    sys.exit(0 if all(results) else 1)
