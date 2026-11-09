#!/usr/bin/env python3
"""Compare the simulator's default output against the captured reference.

The fidelity extensions must be default-off: with the default configuration
the generated trajectories have to match the reference. This is the guard
that the published numbers cannot drift.

The comparison is exact for everything but floats, which are compared with a
relative tolerance of 1e-12: ``exp``, ``log`` and ``expm1`` differ in the
last bit between platforms, and the reference was captured on one machine.
A change in the model moves the numbers by many orders of magnitude more
than that, so the guard still catches what it exists to catch.
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


#: The relative tolerance for the float comparison, and why it is what it is.
REL_TOL = 1e-12

#: The absolute floor, for values that are zero or near it. A purely
#: relative tolerance has no meaning at zero, and the fixture holds
#: structural zeros -- a responder's residual volume, its state fraction --
#: that a platform could render as a denormal rather than as exactly 0.0.
ABS_TOL = 1e-15


def _close(reference: object, produced: object) -> bool:
    """Whether two values agree, exactly for everything but floats.

    Floats are compared with a relative tolerance so that a last-bit
    difference between platforms does not read as a change in the model.
    Everything else -- strings, integers, booleans, ``None`` -- is compared
    exactly, so a moved identifier or a changed read count is still caught.
    """
    if isinstance(reference, bool) or isinstance(produced, bool):
        return reference == produced
    if isinstance(reference, float) or isinstance(produced, float):
        if reference is None or produced is None:
            return reference is produced
        if isinstance(reference, float) != isinstance(produced, float):
            return False
        if reference != reference and produced != produced:  # both NaN
            return True
        if reference == produced:
            return True
        scale = max(abs(reference), abs(produced))
        return abs(reference - produced) <= REL_TOL * scale + ABS_TOL
    return reference == produced


def diff(reference: object, produced: object, path: str = "") -> list[str]:
    """Every place the two structures differ.

    Floats are compared with a relative tolerance rather than for equality.
    The reference was captured on one machine, and ``exp``, ``log`` and
    ``expm1`` differ in the last bit between platforms: the same run on
    Linux x86-64 and macOS arm64 differs by one or two units in the last
    place, which is about 1e-15 relative. That is not a change in the model,
    and requiring bit equality would make the guard unpassable on every
    platform that is not the one that captured the fixture.

    The tolerance is 1e-12 relative, which is three orders of magnitude
    above that and many orders of magnitude below any change in behaviour
    that the guard exists to catch: a moved default parameter, a changed
    draw order or an edited formula moves the numbers by far more. Every
    non-float field -- the identifiers, the arms, the draw indices, the
    integer read counts, the booleans -- is still compared exactly.
    """
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
    if not _close(reference, produced):
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
    print("default simulator output matches the reference within the platform tolerance")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
