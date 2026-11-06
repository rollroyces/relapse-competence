#!/usr/bin/env python3
"""Compare the simulator's default output against the captured reference.

The fidelity extensions must be default-off: with the default configuration
the generated trajectories have to match the reference exactly, digit for
digit. This is the guard that the published numbers cannot drift.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from relapse_competence.config import Regime, SimulationConfig  # noqa: E402
from relapse_competence.simulator import LongitudinalSimulator  # noqa: E402

FIXTURE = (
    Path(__file__).resolve().parents[1]
    / "tests"
    / "fixtures"
    / "default_model_reference.json"
)

CONFIGS = {
    "post_treatment_default": SimulationConfig(
        regime=Regime.POST_TREATMENT, seed=20261106, n_patients_per_arm=8
    ),
    "with_electrical_channel": SimulationConfig(
        regime=Regime.POST_TREATMENT,
        seed=20261106,
        n_patients_per_arm=8,
        n_electrical_loci=50,
    ),
    "screening_default": SimulationConfig(
        regime=Regime.SCREENING, seed=20261106, n_patients_per_arm=8
    ),
}


def current() -> dict:
    payload: dict = {"configs": {}}
    for name, config in CONFIGS.items():
        cohort = LongitudinalSimulator(config).generate_cohort()
        payload["configs"][name] = {
            arm.value: [
                {
                    "patient_id": t.patient_id,
                    "residual_volume_mm3": t.residual_volume_mm3,
                    "doubling_time_days": t.doubling_time_days,
                    "state_fraction": t.state_fraction,
                    "relapse_draw": t.relapse_draw,
                    "has_chip": t.has_chip,
                    "measurements": [
                        {
                            "draw_index": m.draw_index,
                            "mutant_reads": m.mutant_reads,
                            "observed_vaf": m.observed_vaf,
                            "true_vaf": m.true_vaf,
                            "tumour_volume_mm3": m.tumour_volume_mm3,
                            "electrical_reads": m.electrical_reads,
                            "background_vaf": m.background_vaf,
                            "genome_equivalents": m.genome_equivalents,
                        }
                        for m in t.measurements
                    ],
                }
                for t in trajectories
            ]
            for arm, trajectories in cohort.items()
        }
    return payload


def diff(reference: object, produced: object, path: str = "") -> list[str]:
    """Every place the two structures differ."""
    problems: list[str] = []
    if isinstance(reference, dict) and isinstance(produced, dict):
        for key in sorted(set(reference) | set(produced)):
            if key not in reference:
                problems.append(f"{path}.{key}: unexpected")
            elif key not in produced:
                problems.append(f"{path}.{key}: missing")
            else:
                problems += diff(reference[key], produced[key], f"{path}.{key}")
        return problems
    if isinstance(reference, list) and isinstance(produced, list):
        if len(reference) != len(produced):
            problems.append(f"{path}: length {len(reference)} != {len(produced)}")
            return problems
        for i, (a, b) in enumerate(zip(reference, produced, strict=True)):
            problems += diff(a, b, f"{path}[{i}]")
        return problems
    if reference != produced:
        problems.append(f"{path}: {reference!r} != {produced!r}")
    return problems


def main() -> int:
    reference = json.loads(FIXTURE.read_text())
    problems = diff(reference, current())
    if problems:
        print(f"DRIFT: {len(problems)} difference(s) against the reference")
        for problem in problems[:20]:
            print("  ", problem)
        return 1
    print("default simulator output matches the reference exactly")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
