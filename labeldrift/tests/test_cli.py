from pathlib import Path

from labeldrift.cli import main

FIXTURES = Path(__file__).parent / "fixtures"


def test_check_returns_1_when_violations_found(capsys):
    code = main(["check", str(FIXTURES), "--config", str(FIXTURES / "labeldrift.toml")])
    assert code == 1
    out = capsys.readouterr().out
    assert "Found 2 label drift violation(s)" in out


def test_check_returns_0_on_clean_subtree(capsys):
    code = main(
        [
            "check",
            str(FIXTURES / "unrelated"),
            "--config",
            str(FIXTURES / "labeldrift.toml"),
        ]
    )
    assert code == 0
    out = capsys.readouterr().out
    assert "No label drift found" in out


def test_check_missing_src_dir_returns_2():
    code = main(
        ["check", "does/not/exist", "--config", str(FIXTURES / "labeldrift.toml")]
    )
    assert code == 2


def test_check_missing_config_returns_2(tmp_path):
    code = main(["check", str(tmp_path)])
    assert code == 2


def test_version_flag(capsys):
    import pytest

    with pytest.raises(SystemExit) as exc_info:
        main(["--version"])
    assert exc_info.value.code == 0
    out = capsys.readouterr().out
    assert "labeldrift" in out
