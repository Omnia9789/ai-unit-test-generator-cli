from __future__ import annotations

import ast
from dataclasses import dataclass


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    reason: str = ""


def _contains_markdown_fence(text: str) -> bool:
    return "```" in text


def _looks_like_obvious_prose(text: str) -> bool:
    lowered = text.strip().lower()
    bad_starts = (
        "here are",
        "sure,",
        "certainly",
        "i can",
        "below is",
        "these tests",
        "explanation",
    )
    return lowered.startswith(bad_starts)


def _is_pytest_fixture_function(node: ast.AST) -> bool:
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return False

    for dec in node.decorator_list:
        # @pytest.fixture
        if isinstance(dec, ast.Attribute):
            if isinstance(dec.value, ast.Name) and dec.value.id == "pytest" and dec.attr == "fixture":
                return True
        # @fixture (if imported directly)
        if isinstance(dec, ast.Name) and dec.id == "fixture":
            return True
        # @pytest.fixture(...)
        if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute):
            if isinstance(dec.func.value, ast.Name) and dec.func.value.id == "pytest" and dec.func.attr == "fixture":
                return True
        # @fixture(...)
        if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Name) and dec.func.id == "fixture":
            return True

    return False


def _validate_top_level_structure(tree: ast.Module) -> ValidationResult:
    test_count = 0

    for node in tree.body:
        # Allow imports
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            continue

        # Allow test functions and pytest fixtures only
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name.startswith("test_"):
                test_count += 1
                continue
            if _is_pytest_fixture_function(node):
                continue
            return ValidationResult(False, f"non-test function not allowed: {node.name}")

        # Optional: allow a module docstring? For strictness, reject all Expr top-level nodes.
        # Reject everything else (classes, assignments, expressions, calls, etc.)
        return ValidationResult(False, f"disallowed top-level node: {type(node).__name__}")

    if test_count < 1:
        return ValidationResult(False, "no test function found")

    return ValidationResult(True, "")


def validate_generated_tests(output: str) -> ValidationResult:
    if not isinstance(output, str) or not output.strip():
        return ValidationResult(False, "empty output")

    if _contains_markdown_fence(output):
        return ValidationResult(False, "markdown fences are not allowed")

    if _looks_like_obvious_prose(output):
        return ValidationResult(False, "output appears to contain prose")

    try:
        tree = ast.parse(output)
    except SyntaxError as exc:
        return ValidationResult(False, f"syntax error: {exc}")

    return _validate_top_level_structure(tree)