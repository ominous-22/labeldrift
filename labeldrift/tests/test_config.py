from pathlib import Path

import pytest

from labeldrift.config import ConfigError, LabelRule, discover_config, load_config

FIXTURES = Path(__file__).parent / "fixtures"


def test_load_config_parses_rules():
    cfg = load_config(FIXTURES / "labeldrift.toml")
    assert cfg.source_module == "fixtures.labels"
    assert len(cfg.rules) == 2
    assert LabelRule("CRITICAL", "PRIORITY_CRITICAL", ()) in cfg.rules
    assert cfg.rule_for("HIGH_RISK").context == ("psyop",)


def test_load_config_missing_file_raises():
    with pytest.raises(ConfigError):
        load_config(FIXTURES / "does_not_exist.toml")


def test_label_rule_applies_to_respects_context():
    scoped = LabelRule("HIGH_RISK", "PSYOP_HIGH_RISK", context=("psyop",))
    assert scoped.applies_to(Path("src/cls_psyop/scorer.py"))
    assert not scoped.applies_to(Path("src/cls_leads/scorer.py"))

    unscoped = LabelRule("CRITICAL", "PRIORITY_CRITICAL")
    assert unscoped.applies_to(Path("anything/anywhere.py"))


def test_discover_config_finds_standalone_toml(tmp_path):
    (tmp_path / "labeldrift.toml").write_text(
        '[[label]]\nvalue = "X"\nconstant = "Y"\n'
    )
    cfg = discover_config(tmp_path)
    assert cfg.rule_for("X").constant == "Y"


def test_discover_config_finds_pyproject_table(tmp_path):
    (tmp_path / "pyproject.toml").write_text(
        '[tool.labeldrift]\n[[tool.labeldrift.label]]\nvalue = "X"\nconstant = "Y"\n'
    )
    cfg = discover_config(tmp_path)
    assert cfg.rule_for("X").constant == "Y"


def test_discover_config_raises_when_nothing_found(tmp_path):
    with pytest.raises(ConfigError):
        discover_config(tmp_path)
