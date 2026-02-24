from __future__ import annotations

import ast
import io
import tokenize


def strip_comments(source: str) -> str:
    """
    Remove comments using tokenize (safer than regex).
    Keeps code tokens intact.
    """
    out_tokens: list[tokenize.TokenInfo] = []
    reader = io.StringIO(source).readline

    for tok in tokenize.generate_tokens(reader):
        if tok.type == tokenize.COMMENT:
            continue
        out_tokens.append(tok)

    return tokenize.untokenize(out_tokens)


def strip_docstrings_from_function(source: str) -> str:
    """
    Remove the function-level docstring (only).
    Assumes `source` contains a single function definition (top-level).
    """
    tree = ast.parse(source)
    if not tree.body or not isinstance(tree.body[0], (ast.FunctionDef, ast.AsyncFunctionDef)):
        return source  

    fn = tree.body[0]

    if (
        fn.body
        and isinstance(fn.body[0], ast.Expr)
        and isinstance(getattr(fn.body[0], "value", None), ast.Constant)
        and isinstance(fn.body[0].value.value, str)
    ):
      
        fn.body = fn.body[1:]

        try:
            return ast.unparse(fn).strip() + "\n"
        except Exception:
            return source
    return source


def sanitize_function_source(fn_source: str) -> str:
    """
    Full sanitization pipeline for function source:
    1) strip comments
    2) strip function docstring
    3) normalize trailing whitespace
    """
    no_comments = strip_comments(fn_source)
    no_doc = strip_docstrings_from_function(no_comments)


    lines = [line.rstrip() for line in no_doc.splitlines()]
    return "\n".join(lines).strip() + "\n"
