from __future__ import annotations

import pytest

from testgen_cli import cli
from testgen_cli.validate import ValidationResult


def test_cli_refuses_when_input_is_not_single_function(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(cli, "_read_source_from_path_or_stdin", lambda _path: "bad")
    monkeypatch.setattr(cli, "extract_single_function_source", lambda _src: None)
    monkeypatch.setattr(cli.sys, "argv", ["testgen"])

    with pytest.raises(SystemExit) as exc:
        cli.main()

    captured = capsys.readouterr()
    assert exc.value.code == 1
    assert captured.out == cli.ERROR_MSG
    assert captured.err == ""


def test_cli_retries_once_after_validation_failure_then_succeeds(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    first = "not valid tests"
    repaired = "def test_repaired():\n    assert True\n"

    monkeypatch.setattr(cli, "_read_source_from_path_or_stdin", lambda _path: "source")
    monkeypatch.setattr(
        cli, "extract_single_function_source", lambda _src: "def f(x):\n    return x\n"
    )
    monkeypatch.setattr(cli, "sanitize_function_source", lambda src: src)
    monkeypatch.setattr(cli, "generate_unit_tests_for_function", lambda _src: first)
    monkeypatch.setattr(
        cli,
        "regenerate_unit_tests_after_validation_failure",
        lambda _src, invalid_output, reason: repaired
        if invalid_output == first and reason == "syntax error: bad"
        else "",
    )

    def fake_validate(output: str) -> ValidationResult:
        if output == first:
            return ValidationResult(False, "syntax error: bad")
        if output == repaired:
            return ValidationResult(True, "")
        return ValidationResult(False, "unexpected")

    monkeypatch.setattr(cli, "validate_generated_tests", fake_validate)
    monkeypatch.setattr(cli.sys, "argv", ["testgen"])

    with pytest.raises(SystemExit) as exc:
        cli.main()

    captured = capsys.readouterr()
    assert exc.value.code == 0
    assert captured.out == repaired
    assert captured.err == ""
