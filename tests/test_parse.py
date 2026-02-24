from __future__ import annotations

from testgen_cli.parse import extract_single_function_source


def test_accepts_exactly_one_top_level_function() -> None:
    source = """
def add(a, b):
    return a + b
"""
    result = extract_single_function_source(source)
    assert result == "def add(a, b):\n    return a + b"


def test_rejects_import_plus_function() -> None:
    source = """
import math

def area(r):
    return math.pi * r * r
"""
    assert extract_single_function_source(source) is None


def test_rejects_assignment_plus_function() -> None:
    source = """
PI = 3.14

def area(r):
    return PI * r * r
"""
    assert extract_single_function_source(source) is None


def test_rejects_multiple_functions() -> None:
    source = """
def one():
    return 1

def two():
    return 2
"""
    assert extract_single_function_source(source) is None


def test_allows_module_docstring_plus_single_function() -> None:
    source = '''
"""module docs"""

def only():
    return 42
'''
    result = extract_single_function_source(source)
    assert result == "def only():\n    return 42"
