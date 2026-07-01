"""labeldrift — find hardcoded label/enum strings that have drifted from
their canonical constant definitions.

Public API:
    load_config(path)   -> LabelDriftConfig
    scan(src_dir, cfg)  -> dict[Path, list[Violation]]
"""

from __future__ import annotations

from labeldrift.config import LabelDriftConfig, LabelRule, load_config
from labeldrift.scanner import Violation, scan, scan_file

__version__ = "0.1.0"

__all__ = [
    "LabelDriftConfig",
    "LabelRule",
    "Violation",
    "load_config",
    "scan",
    "scan_file",
    "__version__",
]
