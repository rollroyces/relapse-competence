#!/usr/bin/env python3
"""Capture the current simulator output as a regression fixture.

Run this BEFORE changing the simulator. The fixture is then used by
``tests/test_simulator.py`` to prove that the fidelity extensions are
default-off: with the default configuration the published numbers must not
move by a single bit.

    python scripts/capture_default_model_reference.py
"""

from __future__ import annotations

import json
from pathlib import Path

from relapse_competence.config import Regime, SimulationConfig
from relapse_competence.simulator import LongitudinalSimulator

FIXTURE = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "default_model_reference.json"

CONFIGS = {
    "post_treatment_default": SimulationConfig(
        regime=Regime.POST_TREATMENT,
        seed=20261106,
        n_patients_per_arm=8,
    ),
    "with_electrical_channel": SimulationConfig(
        regime=Regime.POST_TREATMENT,
        seed=20261106,
        n_patients_per_arm=8,
        n_electrical_loci=50,
    ),
    "screening_default": SimulationConfig(
        regime=Regime.SCREENING,
        seed=20261106,
        n_patients_per_arm=8,
    ),
}


def capture() -> dict:
    payload: dict[str, object] = {"configs": {}}
    for name, config in CONFIGS.items():
        simulator = LongitudinalSimulator(config)
        cohort = simulator.generate_cohort()
        arms: dict[str, object] = {}
        for arm, trajectories in cohort.items():
            arms[arm.value] = [
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
        payload["configs"][name] = arms  # type: ignore[index]
    return payload


def main() -> int:
    FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    FIXTURE.write_text(json.dumps(capture(), indent=1) + "\n", encoding="utf-8")
    print(f"wrote {FIXTURE} ({FIXTURE.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
