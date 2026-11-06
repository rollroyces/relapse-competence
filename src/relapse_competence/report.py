"""Results assembly and serialisation.

Every results file is stamped with its *mode*. ``simulated`` means the numbers
came out of code that actually ran. ``projected`` means they are assumptions,
and the writer refuses to emit one unless the caller has explicitly opted in
via ``RELAPSE_COMPETENCE_ALLOW_PROJECTION=1``.

This is the single behaviour that the predecessor benchmark in another
repository lacked, and the reason its projected numbers could be published as
a validation result.
"""

from __future__ import annotations

import datetime as _dt
import json
import os
import subprocess
from pathlib import Path
from typing import Any

from .calibration import calibration_provenance, reference_benchmarks
from .config import SimulationConfig
from .contracts import require, require_projection_permission

__all__ = ["build_report", "write_report", "git_commit"]


def git_commit(repo_root: Path | None = None) -> str | None:
    """Best-effort git commit hash for provenance. ``None`` if unavailable."""
    root = repo_root or Path(__file__).resolve().parents[2]
    try:
        out = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if out.returncode != 0:
        return None
    return out.stdout.strip() or None


def build_report(
    mode: str,
    config: SimulationConfig,
    payload: dict[str, Any],
    claim_scope: str,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    """Assemble a results record with provenance and a mode stamp."""
    if mode not in {"simulated", "projected"}:
        raise ValueError(f"unknown mode: {mode!r}")
    if mode == "projected":
        require_projection_permission()

    require(
        isinstance(payload, dict) and bool(payload),
        "refusing to write an empty results payload",
    )

    return {
        "metadata": {
            "mode": mode,
            "generated_at": _dt.datetime.now(_dt.UTC).isoformat(),
            "git_commit": git_commit(repo_root),
            "package": "relapse_competence",
            "python": os.sys.version.split()[0],
        },
        "claim_scope": claim_scope,
        "config": _config_to_dict(config),
        "calibration": calibration_provenance(),
        "reference_benchmarks": reference_benchmarks(),
        "results": payload,
    }


def _config_to_dict(config: SimulationConfig) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for name in config.__dataclass_fields__:
        value = getattr(config, name)
        out[name] = value.value if hasattr(value, "value") else value
    return out


def write_report(report: dict[str, Any], path: str | Path) -> Path:
    """Write a results record as pretty JSON, creating parent directories."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=2, default=str) + "\n", encoding="utf-8")
    return target
