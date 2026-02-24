from __future__ import annotations

from testgen_cli.validate import validate_generated_tests


def test_accepts_valid_pytest_tests() -> None:
    output = """
import pytest

def test_addition():
    assert 1 + 1 == 2
"""
    result = validate_generated_tests(output)
    assert result.ok is True
    assert result.reason == ""


def test_rejects_markdown_fences() -> None:
    output = """```python
def test_x():
    assert True
```"""
    result = validate_generated_tests(output)
    assert result.ok is False
    assert "markdown fences" in result.reason


def test_rejects_prose() -> None:
    output = """
Here are tests for your function:
def test_x():
    assert True
"""
    result = validate_generated_tests(output)
    assert result.ok is False
    assert "prose" in result.reason


def test_rejects_syntax_errors() -> None:
    output = """
def test_bad(
    assert True
"""
    result = validate_generated_tests(output)
    assert result.ok is False
    assert "syntax error" in result.reason


def test_rejects_output_with_no_test_function() -> None:
    output = """
import pytest

@pytest.fixture
def sample_data():
    return 123
"""
    result = validate_generated_tests(output)
    assert result.ok is False
    assert "no test function found" in result.reason


def test_rejects_non_test_top_level_function() -> None:
    output = """
def add(a, b):
    return a + b

def test_add():
    assert add(1, 2) == 3
"""
    result = validate_generated_tests(output)
    assert result.ok is False
    assert "non-test function not allowed" in result.reason
