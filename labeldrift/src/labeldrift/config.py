"""Configuration loading for labeldrift.

Config can live in:
  - an explicit file passed via --config
  - ./labeldrift.toml (auto-discovered)
  - a [tool.labeldrift] table inside ./pyproject.toml (auto-discovered)

Schema
------
[source]
module = "myproject.labels"      # informational only, used in messages

[[label]]
value = "CRITICAL"                # the literal string to flag
constant = "PRIORITY_CRITICAL"    # the canonical name it should come from
context = ["psyop", "leads"]      # optional: only flag inside paths containing
                                   # any of these substrings. Omit to flag everywhere.

[exclude]
paths = ["myproject/labels.py", "test_", ".venv", "__pycache__"]
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib  # type: ignore[no-redef]

DEFAULT_EXCLUDES: tuple[str, ...] = (".venv", "__pycache__", "node_modules", ".git")


@dataclass(frozen=True)
class LabelRule:
    value: str
    constant: str
    context: tuple[str, ...] = ()

    def applies_to(self, path: Path) -> bool:
        if not self.context:
            return True
        path_str = str(path)
        return any(ctx in path_str for ctx in self.context)


@dataclass(frozen=True)
class LabelDriftConfig:
    source_module: str = ""
    rules: tuple[LabelRule, ...] = ()
    exclude_paths: tuple[str, ...] = DEFAULT_EXCLUDES

    @property
    def values(self) -> set[str]:
        return {r.value for r in self.rules}

    def rule_for(self, value: str) -> LabelRule | None:
        for r in self.rules:
            if r.value == value:
                return r
        return None


class ConfigError(RuntimeError):
    """Raised when no config can be found or a config file is malformed."""


def _rules_from_table(data: dict) -> tuple[LabelRule, ...]:
    raw_rules = data.get("label", [])
    rules: list[LabelRule] = []
    for entry in raw_rules:
        try:
            value = entry["value"]
            constant = entry["constant"]
        except KeyError as exc:
            raise ConfigError(
                f"each [[label]] entry needs 'value' and 'constant': {entry!r}"
            ) from exc
        context = tuple(entry.get("context", ()))
        rules.append(LabelRule(value=value, constant=constant, context=context))
    return tuple(rules)


def _config_from_table(data: dict) -> LabelDriftConfig:
    source_module = data.get("source", {}).get("module", "")
    rules = _rules_from_table(data)
    exclude_paths = tuple(data.get("exclude", {}).get("paths", DEFAULT_EXCLUDES))
    return LabelDriftConfig(
        source_module=source_module, rules=rules, exclude_paths=exclude_paths
    )


def load_config(path: str | Path) -> LabelDriftConfig:
    """Load config from an explicit standalone TOML file."""
    path = Path(path)
    if not path.is_file():
        raise ConfigError(f"config file not found: {path}")
    with path.open("rb") as fh:
        data = tomllib.load(fh)
    return _config_from_table(data)


def discover_config(start_dir: str | Path = ".") -> LabelDriftConfig:
    """Look for ./labeldrift.toml, then [tool.labeldrift] in ./pyproject.toml."""
    start_dir = Path(start_dir)

    standalone = start_dir / "labeldrift.toml"
    if standalone.is_file():
        return load_config(standalone)

    pyproject = start_dir / "pyproject.toml"
    if pyproject.is_file():
        with pyproject.open("rb") as fh:
            data = tomllib.load(fh)
        tool_table = data.get("tool", {}).get("labeldrift")
        if tool_table is not None:
            return _config_from_table(tool_table)

    raise ConfigError(
        "no config found: pass --config, or add labeldrift.toml / "
        "[tool.labeldrift] in pyproject.toml"
    )
