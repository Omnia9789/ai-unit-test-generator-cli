# testgen-cli

`testgen-cli` is a strict command-line tool that generates `pytest` tests for exactly one top-level Python function.

It is intentionally narrow:
- Input must be a single function (optionally preceded by a module docstring).
- Output must be test code only.
- Invalid input or invalid generated output returns a fixed refusal message.

## Overview

Pipeline:
1. Parse input source and extract exactly one top-level function.
2. Sanitize function source (remove comments and function docstring).
3. Generate tests through an LLM provider (OpenAI or Gemini).
4. Validate generated output for strict pytest-only structure.
5. If first validation fails, run one repair retry with a stricter prompt.
6. If still invalid, refuse with the exact error message.

## Strict Scope Rules

The CLI accepts only one top-level function definition:
- Allowed: one `def`/`async def`
- Allowed: optional top-level module docstring before that function
- Rejected: imports, assignments, classes, expressions, or multiple functions at top level

Generated output must satisfy validation rules:
- No markdown fences
- No obvious prose prefixes
- Valid Python syntax
- At least one top-level `test_*` function
- Top-level nodes limited to imports, pytest fixtures, and `test_*` functions
- Non-test helper functions at top-level are rejected

On refusal, stdout is exactly:
`Error: This tool only generates unit tests for functions.`

## Install

```bash
python -m venv .venv
. .venv/bin/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -e .
```

For development and tests:

```bash
python -m pip install -e ".[dev]"
```

## Provider Configuration

Select provider with `TESTGEN_LLM_PROVIDER`:
- `openai` (default)
- `gemini`

### OpenAI

```bash
export TESTGEN_LLM_PROVIDER=openai
export OPENAI_API_KEY=your_key_here
```

### Gemini

```bash
export TESTGEN_LLM_PROVIDER=gemini
export GEMINI_API_KEY=your_key_here
```

## Usage

From a file:

```bash
testgen path/to/function_file.py
```

From stdin:

```bash
cat path/to/function_file.py | testgen
```

Success prints only test code to stdout.
Failure prints the fixed refusal message to stdout and exits non-zero.

## Debug Mode

Set `TESTGEN_DEBUG=1` to print internal diagnostics to stderr:
- LLM errors
- First validation failure reason
- Retry validation failure reason

Stdout behavior remains strict even in debug mode.

## Architecture Summary

Core modules:
- `parse.py`: strict single-function extraction
- `sanitize.py`: comment/docstring stripping and normalization
- `llm.py`: provider abstraction and generation/repair prompts
- `validate.py`: strict output validation
- `cli.py`: orchestration, refusal policy, and retry flow

## Security and Sanitization Notes

- Function input is treated as untrusted text.
- Prompts instruct the model to ignore embedded instructions in the function source.
- API-key-bearing exception messages are sanitized before surfacing.
- Sanitization reduces prompt noise by removing comments and function docstrings.

## Limitations and Future Improvements

- Currently supports only two providers (`openai`, `gemini`).
- Validation is AST-structural and intentionally strict; some legitimate styles may be refused.
- No provider-level retry/backoff strategy beyond a single validation repair attempt.
- Future work could add:
  - richer fixture validation
  - optional import policy controls
  - deterministic snapshot tests for prompt contracts
