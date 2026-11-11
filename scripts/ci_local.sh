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
#
# The build backend is used without isolation when it is already installed,
# so the check works offline; a fresh virtualenv on Python 3.12 or later has
# no setuptools, so the isolated build is used there instead. Both paths
# validate the same metadata, which is the point of the check.
WHEEL_DIR="$(mktemp -d)"
trap 'rm -rf "$WHEEL_DIR"' EXIT
if "$PY" -c "import setuptools" >/dev/null 2>&1; then
    "$PY" -m pip wheel --no-deps --no-build-isolation -w "$WHEEL_DIR" . >/dev/null
else
    "$PY" -m pip wheel --no-deps -w "$WHEEL_DIR" . >/dev/null
fi
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

echo "==> application tracker"
"$PY" scripts/application_tracker.py --check

echo "==> leukocyte audit control"
"$PY" scripts/leukocyte_audit.py --patients 800 --control-only

echo "==> driver-versus-passenger audit"
# The audit reads the cached public deposits, which are gitignored and
# therefore absent on a CI runner. Where the cache is there the audit is
# re-run and its artefact has to match the committed one; where it is not,
# the committed artefact is checked by the report-consistency step below.
if [ -d "$ROOT/data/gse353299" ] && [ -d "$ROOT/data/gse299684" ]; then
    "$PY" scripts/driver_passenger_audit.py --permutations 200
    "$PY" scripts/kcnn4_copy_number_audit.py --permutations 200
else
    echo "no local copy of the public deposits; checking the committed artefacts only"
    "$PY" - <<'PY'
import json
from pathlib import Path

for artefact, name in (
    (
        "results/driver_passenger_audit/driver_passenger_audit.json",
        "driver-passenger",
    ),
    (
        "results/kcnn4_copy_number/kcnn4_copy_number.json",
        "copy-number",
    ),
):
    path = Path(artefact)
    if not path.exists():
        raise SystemExit(f"missing: {path}")
    payload = json.loads(path.read_text())
    for dataset, body in payload["datasets"].items():
        print(
            f"  {name}: {dataset} "
            f"({body.get('cohort', '?')}): "
            f"{body.get('n_libraries', len(body.get('libraries', [])))} "
            "libraries"
        )
PY
fi

echo "==> PLCO CDAS submission package"
"$PY" scripts/check_plco_cdas_package.py
"$PY" scripts/build_plco_cdas_pdf.py --check

echo "==> report consistency"
"$PY" scripts/verify_report_consistency.py

echo "==> benchmark"
"$PY" -m relapse_competence.cli all --patients 800 --outdir results

echo
echo "All CI checks passed locally."
echo "Results written to $ROOT/results/benchmark_results.json"
