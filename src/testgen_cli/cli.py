import argparse
import sys
import os
from .validate import validate_generated_tests
from .llm import (
    LLMGenerationError,
    generate_unit_tests_for_function,
    regenerate_unit_tests_after_validation_failure,
)
from .parse import extract_single_function_source
from .sanitize import sanitize_function_source

ERROR_MSG = "Error: This tool only generates unit tests for functions."


def _read_source_from_path_or_stdin(path: str | None) -> str:
    if path:
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except OSError:
            return ""
    try:
        return sys.stdin.read()
    except Exception:
        return ""


def main() -> None:
    parser = argparse.ArgumentParser(prog="testgen")
    parser.add_argument(
        "path",
        nargs="?",
        help="Path to a Python file containing a single function. If omitted, reads from stdin.",
    )
    args = parser.parse_args()

    src = _read_source_from_path_or_stdin(args.path)

    fn_src = extract_single_function_source(src)
    if fn_src is None:
        sys.stdout.write(ERROR_MSG)
        sys.exit(1)

    sanitized = sanitize_function_source(fn_src)
    try:
        tests = generate_unit_tests_for_function(sanitized)
    except LLMGenerationError as exc:
        if os.getenv("TESTGEN_DEBUG") == "1":
            print(f"[DEBUG] LLM error: {exc}", file=sys.stderr)
        sys.stdout.write(ERROR_MSG)
        sys.exit(1)

    result = validate_generated_tests(tests)
    if not result.ok:
        if os.getenv("TESTGEN_DEBUG") == "1":
            print(f"[DEBUG] First validation failed: {result.reason}", file=sys.stderr)
        try:
            retry_tests = regenerate_unit_tests_after_validation_failure(
                sanitized,
                tests,
                result.reason,
            )
        except LLMGenerationError as exc:
            if os.getenv("TESTGEN_DEBUG") == "1":
                print(f"[DEBUG] LLM retry error: {exc}", file=sys.stderr)
            sys.stdout.write(ERROR_MSG)
            sys.exit(1)

        retry_result = validate_generated_tests(retry_tests)
        if not retry_result.ok:
            if os.getenv("TESTGEN_DEBUG") == "1":
                print(
                    f"[DEBUG] Retry validation failed: {retry_result.reason}",
                    file=sys.stderr,
                )
            sys.stdout.write(ERROR_MSG)
            sys.exit(1)
        tests = retry_tests

    sys.stdout.write(tests.strip() + "\n")
    sys.exit(0)


if __name__ == "__main__":
    main()
