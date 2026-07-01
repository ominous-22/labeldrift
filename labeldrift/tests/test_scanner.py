from pathlib import Path

from labeldrift.config import load_config
from labeldrift.scanner import scan, scan_file

FIXTURES = Path(__file__).parent / "fixtures"


def _cfg():
    return load_config(FIXTURES / "labeldrift.toml")


def test_global_rule_flagged_anywhere():
    violations = scan_file(FIXTURES / "psyop" / "pipeline.py", _cfg())
    values = {v.value for v in violations}
    assert "CRITICAL" in values


def test_context_scoped_rule_flagged_in_context():
    violations = scan_file(FIXTURES / "psyop" / "pipeline.py", _cfg())
    values = {v.value for v in violations}
    assert "HIGH_RISK" in values


def test_context_scoped_rule_not_flagged_outside_context():
    violations = scan_file(FIXTURES / "unrelated" / "notes.py", _cfg())
    assert violations == []


def test_canonical_labels_file_is_excluded():
    findings = scan(FIXTURES, _cfg())
    assert FIXTURES / "labels.py" not in findings


def test_scan_aggregates_across_tree():
    findings = scan(FIXTURES, _cfg())
    assert FIXTURES / "psyop" / "pipeline.py" in findings
    assert FIXTURES / "unrelated" / "notes.py" not in findings
    total = sum(len(v) for v in findings.values())
    assert total == 2  # one CRITICAL, one HIGH_RISK


def test_violation_message_includes_source_module():
    violations = scan_file(FIXTURES / "psyop" / "pipeline.py", _cfg())
    msg = violations[0].message()
    assert "fixtures.labels" in msg
    assert str(FIXTURES / "psyop" / "pipeline.py") in msg


def test_scan_file_handles_syntax_error_gracefully(tmp_path):
    broken = tmp_path / "broken.py"
    broken.write_text("def f(:\n    pass")
    assert scan_file(broken, _cfg()) == []
