#while running code locally with subprocess is enough to start, this needs to run in a docker container.

import subprocess

def run_code(file_path):
    try:
        result = subprocess.run(
            ["python", file_path],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            return {
                "success": True,
                "output": result.stdout
            }

        return {
            "success": False,
            "error": result.stderr
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }