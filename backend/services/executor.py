import subprocess
import os
from dataclasses import dataclass


@dataclass
class ExecutionResult:
    stdout: str
    stderr: str
    exit_code: int


def run_code(language: str, code: str, timeout: int = 10) -> ExecutionResult:
    if language == "python":
        return _run_python(code, timeout)
    elif language == "java":
        return _run_java(code, timeout)
    else:
        return ExecutionResult(stdout="", stderr=f"Unsupported language: {language}", exit_code=1)


def _run_python(code: str, timeout: int) -> ExecutionResult:
    try:
        result = subprocess.run(
            [
                "docker", "run", "--rm", "-i",
                "--network=none",
                "--memory=128m",
                "--cpus=0.5",
                f"--stop-timeout={timeout}",
                "python-sandbox",
                "python3", "-",
            ],
            input=code.encode(),
            capture_output=True,
            timeout=timeout + 5,
        )
        return ExecutionResult(
            stdout=result.stdout.decode(errors="replace"),
            stderr=result.stderr.decode(errors="replace"),
            exit_code=result.returncode,
        )
    except subprocess.TimeoutExpired:
        return ExecutionResult(
            stdout="",
            stderr="TimeoutError: Code execution exceeded the time limit (10 seconds). Check for infinite loops.",
            exit_code=1,
        )
    except Exception as e:
        return ExecutionResult(stdout="", stderr=f"Execution error: {e}", exit_code=1)


def _run_java(code: str, timeout: int) -> ExecutionResult:
    try:
        result = subprocess.run(
            [
                "docker", "run", "--rm", "-i",
                "--network=none",
                "--memory=256m",
                "--cpus=0.5",
                f"--stop-timeout={timeout}",
                "java-sandbox",
            ],
            input=code.encode(),
            capture_output=True,
            timeout=timeout + 10,  # extra buffer: javac startup is slow
        )
        return ExecutionResult(
            stdout=result.stdout.decode(errors="replace"),
            stderr=result.stderr.decode(errors="replace"),
            exit_code=result.returncode,
        )
    except subprocess.TimeoutExpired:
        return ExecutionResult(
            stdout="",
            stderr="TimeoutError: Code execution exceeded the time limit (10 seconds). Check for infinite loops.",
            exit_code=1,
        )
    except Exception as e:
        return ExecutionResult(stdout="", stderr=f"Execution error: {e}", exit_code=1)
