import ast
import re
from backend.models.schemas import BugAnalysis

# ── Python ──────────────────────────────────────────────────────────────────

_PYTHON_RUNTIME_ERRORS = [
    "NameError",
    "TypeError",
    "ValueError",
    "IndexError",
    "KeyError",
    "AttributeError",
    "ZeroDivisionError",
    "RecursionError",
    "ImportError",
    "ModuleNotFoundError",
    "FileNotFoundError",
    "OSError",
    "RuntimeError",
    "StopIteration",
    "TimeoutError",
]

_PYTHON_DESCRIPTIONS = {
    "SyntaxError": "Invalid Python syntax",
    "IndentationError": "Incorrect indentation",
    "NameError": "Undefined variable or name",
    "TypeError": "Operation on incompatible types",
    "ValueError": "Invalid value for the given type",
    "IndexError": "List or sequence index out of range",
    "KeyError": "Dictionary key not found",
    "AttributeError": "Object has no such attribute or method",
    "ZeroDivisionError": "Division by zero",
    "RecursionError": "Maximum recursion depth exceeded",
    "ImportError": "Failed to import module",
    "ModuleNotFoundError": "Module not found",
    "RuntimeError": "Runtime error occurred",
    "TimeoutError": "Code timed out — check for infinite loops",
    "LogicError": "Code runs but produces unexpected output",
}

# ── Java ─────────────────────────────────────────────────────────────────────

_JAVA_DESCRIPTIONS = {
    "CompileError": "Java compilation failed",
    "NullPointerException": "Null reference accessed",
    "ArrayIndexOutOfBoundsException": "Array index out of bounds",
    "StringIndexOutOfBoundsException": "String index out of bounds",
    "ClassCastException": "Invalid type cast",
    "ArithmeticException": "Arithmetic error (e.g. division by zero)",
    "StackOverflowError": "Stack overflow — check for infinite recursion",
    "NumberFormatException": "Invalid number format",
    "TimeoutError": "Code timed out — check for infinite loops",
    "LogicError": "Code runs but produces unexpected output",
}


def analyze(language: str, code: str, stderr: str) -> BugAnalysis:
    if language == "python":
        return _analyze_python(code, stderr)
    elif language == "java":
        return _analyze_java(stderr)
    return BugAnalysis(category="UnknownError", description="Could not classify the error.")


# ── Python analysis ──────────────────────────────────────────────────────────

def _analyze_python(code: str, stderr: str) -> BugAnalysis:
    # 1. Static check — catches SyntaxError / IndentationError before running
    try:
        ast.parse(code)
    except SyntaxError as e:
        category = "IndentationError" if "indent" in str(e).lower() else "SyntaxError"
        return BugAnalysis(
            category=category,
            line=e.lineno,
            description=_PYTHON_DESCRIPTIONS.get(category, str(e)),
        )

    if not stderr:
        return BugAnalysis(category="LogicError", description=_PYTHON_DESCRIPTIONS["LogicError"])

    # 2. Parse runtime stderr
    for err_type in _PYTHON_RUNTIME_ERRORS:
        if err_type in stderr:
            line = _extract_python_line(stderr)
            return BugAnalysis(
                category=err_type,
                line=line,
                description=_PYTHON_DESCRIPTIONS.get(err_type, err_type),
            )

    return BugAnalysis(category="RuntimeError", description=stderr.strip().splitlines()[-1] if stderr.strip() else "Unknown error")


def _extract_python_line(stderr: str) -> int | None:
    """Extract the last line number from Python tracebacks."""
    matches = re.findall(r'line (\d+)', stderr)
    if matches:
        return int(matches[-1])
    return None


# ── Java analysis ────────────────────────────────────────────────────────────

def _analyze_java(stderr: str) -> BugAnalysis:
    if not stderr:
        return BugAnalysis(category="LogicError", description=_JAVA_DESCRIPTIONS["LogicError"])

    # Compile errors from javac look like:  Main.java:5: error: ...
    compile_match = re.search(r'\.java:(\d+):', stderr)
    if compile_match and ("error:" in stderr or "^" in stderr):
        line = int(compile_match.group(1))
        msg = _first_java_error_msg(stderr)
        return BugAnalysis(category="CompileError", line=line, description=msg or _JAVA_DESCRIPTIONS["CompileError"])

    # Runtime exceptions
    java_exceptions = [
        "NullPointerException",
        "ArrayIndexOutOfBoundsException",
        "StringIndexOutOfBoundsException",
        "ClassCastException",
        "ArithmeticException",
        "StackOverflowError",
        "NumberFormatException",
        "TimeoutError",
    ]
    for exc in java_exceptions:
        if exc in stderr:
            line = _extract_java_runtime_line(stderr)
            return BugAnalysis(
                category=exc,
                line=line,
                description=_JAVA_DESCRIPTIONS.get(exc, exc),
            )

    return BugAnalysis(category="RuntimeError", description=stderr.strip().splitlines()[-1] if stderr.strip() else "Unknown error")


def _first_java_error_msg(stderr: str) -> str | None:
    """Return the first 'error: <message>' from javac output."""
    match = re.search(r'error: (.+)', stderr)
    return match.group(1).strip() if match else None


def _extract_java_runtime_line(stderr: str) -> int | None:
    """Extract line number from Java runtime stack trace."""
    match = re.search(r'Main\.java:(\d+)\)', stderr)
    return int(match.group(1)) if match else None
