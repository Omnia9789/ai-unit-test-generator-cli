from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class FunctionInfo:
    name: str
    start_line: int
    end_line: int


def _is_module_docstring_node(node: ast.AST) -> bool:
    if not isinstance(node, ast.Expr):
        return False
    value = getattr(node, "value", None)
    if isinstance(value, ast.Constant) and isinstance(value.value, str):
        return True
    return False


def extract_single_function_source(source: str) -> Optional[str]:
    """
    Return the exact source slice for the single top-level function in `source`.

    Strict acceptance:
    - Exactly one top-level FunctionDef/AsyncFunctionDef
    - All other top-level nodes must be ONLY an optional module docstring
    """
    if not isinstance(source, str) or not source.strip():
        return None

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return None

    funcs: list[ast.AST] = []
    for idx, node in enumerate(tree.body):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            funcs.append(node)
            continue
       
        if idx == 0 and _is_module_docstring_node(node):
            continue

        return None

    if len(funcs) != 1:
        return None

    fn = funcs[0]
    start = getattr(fn, "lineno", None)
    end = getattr(fn, "end_lineno", None)
    if start is None or end is None:
        return None

    lines = source.splitlines(True)  # keep line endings
    fn_src = "".join(lines[start - 1 : end]).strip()
    return fn_src if fn_src else None
