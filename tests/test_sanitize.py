from __future__ import annotations

from testgen_cli.sanitize import sanitize_function_source


def test_strips_function_docstring() -> None:
    source = '''
def greet(name):
    """Return greeting text."""
    return "hi " + name
'''
    cleaned = sanitize_function_source(source)
    assert '"""' not in cleaned
    assert "Return greeting text." not in cleaned


def test_strips_comments() -> None:
    source = """
def add(a, b):
    # leading comment
    total = a + b  # inline comment
    return total
"""
    cleaned = sanitize_function_source(source)
    assert "# leading comment" not in cleaned
    assert "# inline comment" not in cleaned


def test_preserves_logic() -> None:
    source = '''
def clamp(value, low, high):
    """Keep value in range."""
    # branch logic should remain unchanged
    if value < low:
        return low
    if value > high:
        return high
    return value  # same value
'''
    cleaned = sanitize_function_source(source)

    namespace_original: dict[str, object] = {}
    namespace_cleaned: dict[str, object] = {}
    exec(source, namespace_original)
    exec(cleaned, namespace_cleaned)

    original = namespace_original["clamp"]
    cleaned_fn = namespace_cleaned["clamp"]

    for args in [(-1, 0, 10), (5, 0, 10), (100, 0, 10)]:
        assert original(*args) == cleaned_fn(*args)
