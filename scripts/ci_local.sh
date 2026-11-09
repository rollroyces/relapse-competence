#!/usr/bin/env bash
# Run exactly what .github/workflows/ci.yml runs, locally.
#
# Useful when GitHub Actions is unavailable (for example when the account is
# in a billing-locked state and jobs cannot be scheduled). The checks are
# identical: lint, test, benchmark.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PY="${PYTHON:-python3}"

# Run against the source tree without requiring an install.
export PYTHONPATH="$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

echo "==> ruff"
"$PY" -m ruff check src tests scripts

echo "==> packaging"
# CI installs the package, and that is the only step that exercises the
# package metadata. A deprecated licence classifier, or a dependency the
# tests need but the dev extra does not declare, fails there and nowhere
# else -- so the wheel is built here too.
WHEEL_DIR="$(mktemp -d)"
trap 'rm -rf "$WHEEL_DIR"' EXIT
"$PY" -m pip wheel --no-deps --no-build-isolation -w "$WHEEL_DIR" . >/dev/null
"$PY" - <<'PY'
import re
import tomllib
from pathlib import Path

metadata = tomllib.loads(Path("pyproject.toml").read_text())
declared = set(metadata["project"]["dependencies"])
declared |= set(metadata["project"]["optional-dependencies"]["dev"])
names = {re.split(r"[<>=!~\[ ]", spec, 1)[0].strip() for spec in declared}
missing = [package for package in ("numpy", "scipy") if package not in names]
if missing:
    raise SystemExit(
        "these packages are imported by the tests but not declared: "
        + ", ".join(missing)
    )
print("package metadata builds, and the test dependencies are declared")
PY

echo "==> pytest"
"$PY" -m pytest

echo "==> audit findings disposition"
"$PY" scripts/audit_findings_disposition.py

echo "==> revision history"
"$PY" scripts/regenerate_revision_history.py --check

echo "==> report consistency"
"$PY" scripts/verify_report_consistency.py

echo "==> benchmark"
"$PY" -m relapse_competence.cli all --patients 800 --outdir results

echo
echo "All CI checks passed locally."
echo "Results written to $ROOT/results/benchmark_results.json"
