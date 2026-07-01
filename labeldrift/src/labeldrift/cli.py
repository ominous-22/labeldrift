"""labeldrift CLI: ``labeldrift check <src-dir> [--config PATH]``"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from labeldrift import __version__
from labeldrift.config import ConfigError, discover_config, load_config
from labeldrift.scanner import scan


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="labeldrift",
        description="Find hardcoded label/enum strings that have drifted "
        "from their canonical constant definitions.",
    )
    parser.add_argument(
        "--version", action="version", version=f"labeldrift {__version__}"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    check = sub.add_parser("check", help="scan a source directory for violations")
    check.add_argument(
        "src_dir", nargs="?", default="src", help="directory to scan (default: src)"
    )
    check.add_argument(
        "--config", type=Path, default=None, help="path to a labeldrift.toml config"
    )
    return parser


def _run_check(src_dir: str, config_path: Path | None) -> int:
    try:
        cfg = load_config(config_path) if config_path else discover_config(".")
    except ConfigError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if not Path(src_dir).is_dir():
        print(f"ERROR: source directory not found: {src_dir}", file=sys.stderr)
        return 2

    if not cfg.rules:
        print("ERROR: config has no [[label]] rules — nothing to check", file=sys.stderr)
        return 2

    findings = scan(src_dir, cfg)

    if not findings:
        print(f"\u2713 No label drift found ({len(cfg.rules)} rule(s) checked)")
        return 0

    total = sum(len(v) for v in findings.values())
    print(f"\u2717 Found {total} label drift violation(s) in {len(findings)} file(s):\n")
    for _path, violations in sorted(findings.items()):
        for violation in violations:
            print(f"  {violation.message()}")
    return 1


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "check":
        return _run_check(args.src_dir, args.config)

    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
