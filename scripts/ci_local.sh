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
"$PY" -m ruff check src tests

echo "==> pytest"
"$PY" -m pytest

echo "==> report consistency"
"$PY" scripts/verify_report_consistency.py

echo "==> benchmark"
"$PY" -m relapse_competence.cli all --patients 800 --outdir results

echo
echo "All CI checks passed locally."
echo "Results written to $ROOT/results/benchmark_results.json"
