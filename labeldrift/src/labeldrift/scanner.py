"""AST-based scanner: find bare string literals matching configured label
values, outside the paths where they're legitimately allowed."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path

from labeldrift.config import LabelDriftConfig


@dataclass(frozen=True)
class Violation:
    path: Path
    lineno: int
    value: str
    constant: str
    source_module: str

    def message(self) -> str:
        target = f"{self.source_module}.{self.constant}" if self.source_module else self.constant
        return f"{self.path}:{self.lineno}: use {target} instead of bare string {self.value!r}"


def _is_excluded(path: Path, exclude_paths: tuple[str, ...]) -> bool:
    path_str = str(path)
    return any(token in path_str for token in exclude_paths)


def _string_literals(tree: ast.AST) -> list[tuple[int, str]]:
    found: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            found.append((node.lineno, node.value))
    return sorted(found)


def scan_file(path: Path, cfg: LabelDriftConfig) -> list[Violation]:
    """Scan a single file. Returns [] on syntax errors (skips, doesn't crash)."""
    try:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
    except (SyntaxError, UnicodeDecodeError, OSError):
        return []

    violations: list[Violation] = []
    for lineno, value in _string_literals(tree):
        rule = cfg.rule_for(value)
        if rule is None:
            continue
        if not rule.applies_to(path):
            continue
        violations.append(
            Violation(
                path=path,
                lineno=lineno,
                value=value,
                constant=rule.constant,
                source_module=cfg.source_module,
            )
        )
    return violations


def scan(src_dir: str | Path, cfg: LabelDriftConfig) -> dict[Path, list[Violation]]:
    """Scan every .py file under src_dir. Returns {path: [violations]} for
    files that have at least one violation."""
    src_dir = Path(src_dir)
    findings: dict[Path, list[Violation]] = {}
    for py_file in sorted(src_dir.rglob("*.py")):
        if _is_excluded(py_file, cfg.exclude_paths):
            continue
        violations = scan_file(py_file, cfg)
        if violations:
            findings[py_file] = violations
    return findings
