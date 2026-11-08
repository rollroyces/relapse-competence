#!/usr/bin/env python3
"""What the measured state enrichment means for a plasma assay.

The state-resolved audits established something about **cells in tissue**: the
relapse-competent population over-expresses ion channels relative to the
surrounding tumour. The programme's clinical path, however, is a **plasma**
assay, and plasma integrates over every tumour cell in the circulation. A
per-cell enrichment is therefore not the quantity that decides whether the
electrical channel is readable in blood.

This script closes that gap. For each disease and channel it takes the
measured per-cell abundance fold and the measured state fraction, computes
the bulk elevation a plasma assay would see, and then re-runs the channel
allocation sweep with those measured values in place of the simulator's
assumed ones.

The two metrics are not interchangeable, and the difference matters:

* the **detection rate** (fraction of cells with at least one transcript)
  governs a per-cell or tissue readout;
* the **abundance fold** (mean expression, in counts per 10,000) governs the
  bulk plasma signal.

Run
---
    python scripts/plasma_readability.py
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from relapse_competence.benchmark import run_channel_allocation_sweep  # noqa: E402
from relapse_competence.config import Regime, SimulationConfig  # noqa: E402

#: The simulator's assumed electrical fold: the bulk marker is elevated this
#: many times in state-bearing cells.
ASSUMED_FOLD = 3.0
#: The simulator's assumed state fraction in a relapsing patient.
ASSUMED_STATE_FRACTION = 0.25

#: The two audited datasets, with the state fraction measured in each.
DATASETS: dict[str, dict] = {
    "SCLC": {
        "artefact": "results/gse299684/state_expression.json",
        "state": "YAP1+",
        "state_fraction": None,  # taken from the artefact
    },
    "NSCLC": {
        "artefact": "results/gse353299/state_expression.json",
        "state": "KRT17+",
        "state_fraction": None,  # the per-library median at the MRD timepoint
    },
}

CHANNELS = ("KCNN4", "PIEZO1")


def _primary(artefact: dict) -> dict:
    primary = artefact["audit"]["primary_definition"]
    return next(s for s in artefact["state_definition_sweep"] if s["definition"] == primary)


def measured_state_fraction(name: str, artefact: dict) -> tuple[float, str]:
    """The state fraction that a plasma assay would meet, and where it comes from."""
    if name == "SCLC":
        primary = _primary(artefact)
        total = primary["n_yap1_positive"] + primary["n_yap1_negative"]
        return primary["n_yap1_positive"] / total, "pooled over all libraries"
    fractions = sorted(
        s["state_positive_fraction_of_malignant"]
        for s in artefact["per_sample"]
        if s["treatment"].strip().lower() == "osi_mrd"
        and s["state_positive_fraction_of_malignant"] is not None
    )
    return fractions[len(fractions) // 2], "per-library median at the MRD timepoint"


def bulk_elevation(fraction: float, fold: float) -> float:
    """The factor by which the bulk plasma signal is elevated.

    A tumour with a state fraction ``f`` whose state cells carry the channel
    ``fold`` times more than the rest has a bulk signal of
    ``(1 - f) + f * fold``, which is ``1 + f * (fold - 1)`` times the signal of
    a state-free tumour.
    """
    return 1.0 + fraction * (fold - 1.0)


def fraction_used(entry: dict) -> float:
    """The state fraction the sweep actually used for this entry."""
    if entry.get("control"):
        return ASSUMED_STATE_FRACTION
    return entry["state_fraction"]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".")
    parser.add_argument("--outdir", default="results/plasma_readability")
    parser.add_argument("--patients", type=int, default=400)
    parser.add_argument("--depth", type=int, default=200_000)
    parser.add_argument("--loci", type=int, default=200)
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    outdir = root / args.outdir
    outdir.mkdir(parents=True, exist_ok=True)

    measured: list[dict] = []
    for name, spec in DATASETS.items():
        path = root / spec["artefact"]
        if not path.exists():
            print(f"missing {path}; skipping {name}", file=sys.stderr)
            continue
        artefact = json.loads(path.read_text())
        primary = _primary(artefact)
        genes = {c["gene"]: c for c in primary["channels"] if c.get("status") == "ok"}
        fraction, source = measured_state_fraction(name, artefact)
        for channel in CHANNELS:
            if channel not in genes:
                continue
            record = genes[channel]
            abundance_fold = record.get("linear_fold_vs_yap1negative")
            if abundance_fold is None:
                continue
            measured.append(
                {
                    "dataset": name,
                    "state": spec["state"],
                    "channel": channel,
                    "state_fraction": fraction,
                    "state_fraction_source": source,
                    # The simulator multiplies the bulk marker by
                    # 1 + fold * state_fraction; the measured bulk factor is
                    # 1 + f * (abundance_fold - 1), so the two parameters are
                    # not the same number.
                    "simulator_electrical_fold_change": max(0.0, abundance_fold - 1.0),
                    "detection_ratio_state_vs_tumour": record[
                        "detection_ratio_vs_yap1negative"
                    ],
                    "abundance_fold_state_vs_tumour": abundance_fold,
                    "bulk_elevation_with_measured_values": bulk_elevation(
                        fraction, abundance_fold
                    ),
                    "bulk_elevation_with_the_simulators_assumption": bulk_elevation(
                        ASSUMED_STATE_FRACTION, ASSUMED_FOLD
                    ),
                }
            )

    # The control: the same sweep with the simulator's own assumed parameters,
    # so that any difference is attributable to the measured values and not to
    # the re-run.
    measured.append(
        {
            "dataset": "simulator default",
            "state": "assumed",
            "channel": "assumed",
            "state_fraction": ASSUMED_STATE_FRACTION,
            "state_fraction_source": "the simulator's own assumption",
            "detection_ratio_state_vs_tumour": None,
            "abundance_fold_state_vs_tumour": ASSUMED_FOLD,
            "bulk_elevation_with_measured_values": bulk_elevation(
                ASSUMED_STATE_FRACTION, ASSUMED_FOLD
            ),
            "bulk_elevation_with_the_simulators_assumption": bulk_elevation(
                ASSUMED_STATE_FRACTION, ASSUMED_FOLD
            ),
            "control": True,
            # The control runs the simulator's own assumption unchanged.
            "simulator_electrical_fold_change": ASSUMED_FOLD,
        }
    )

    # --- re-run the channel allocation sweep with the measured values ---
    base = SimulationConfig(
        regime=Regime.POST_TREATMENT,
        seed=20261106,
        n_patients_per_arm=args.patients,
        sequencing_depth=args.depth,
        n_loci=args.loci,
    )
    sweeps: list[dict] = []
    for entry in measured:
        fraction = entry["state_fraction"]
        if entry.get("control"):
            fraction = ASSUMED_STATE_FRACTION
        else:
            fraction = entry["state_fraction"]
        # Only the two parameters under test change. The control changes
        # neither, so it reproduces the published D1 row exactly -- which is
        # what makes the other rows attributable to the measurements.
        config = replace(
            base,
            n_electrical_loci=max(1, args.loci // 4),
            electrical_fold_change=entry["simulator_electrical_fold_change"],
        )
        if not entry.get("control"):
            config = replace(config, state_fraction_resistant=fraction)
        rows = run_channel_allocation_sweep(
            config,
            total_loci=(args.loci,),
            depth=args.depth,
            electrical_fractions=(0.0, 0.25),
        )
        for row in rows:
            if row["electrical_fraction"] not in (0.0, 0.25):
                continue
            sweeps.append(
                {
                    "dataset": entry["dataset"],
                    "channel": entry["channel"],
                    "electrical_fraction": row["electrical_fraction"],
                    "electrical_fold_change_used": config.electrical_fold_change,
                    "state_fraction_used": fraction,
                    "bulk_elevation_used": bulk_elevation(
                        fraction,
                        1.0 + entry["simulator_electrical_fold_change"],
                    ),
                    "mrd_sensitivity": row["mrd_sensitivity"],
                    "mrd_specificity_vs_persistent": row["mrd_specificity_vs_persistent"],
                    "ppv_within_mrd_positive": row["ppv_within_mrd_positive"],
                    "auc_electrical_enrichment_within_mrd_positive": row[
                        "auc_electrical_enrichment_within_mrd_positive"
                    ],
                    "ppv_after_electrical_refinement": row[
                        "ppv_after_electrical_refinement"
                    ],
                    "relapse_fraction_retained_by_refinement": row[
                        "relapse_fraction_retained_by_refinement"
                    ],
                }
            )
        print(
            f"{entry['dataset']} {entry['channel']}: simulator fold "
            f"{config.electrical_fold_change:.3f}, state fraction {fraction:.3f} "
            f"-> bulk elevation "
            f"{bulk_elevation(fraction, 1.0 + config.electrical_fold_change):.3f}",
            flush=True,
        )

    payload = {
        "audit": {
            "id": "plasma-readability-2026-11",
            "generated_by": "scripts/plasma_readability.py",
            "generated_at": datetime.now(UTC).isoformat(),
            "question": (
                "Does the measured per-cell state enrichment survive dilution "
                "into a bulk plasma signal, and what does that do to the "
                "channel allocation conclusion?"
            ),
            "simulator_assumption": {
                "electrical_fold_change": ASSUMED_FOLD,
                "state_fraction": ASSUMED_STATE_FRACTION,
                "bulk_elevation": bulk_elevation(ASSUMED_STATE_FRACTION, ASSUMED_FOLD),
            },
            "benchmark_configuration": {
                "patients_per_arm": args.patients,
                "depth": args.depth,
                "total_loci": args.loci,
                "electrical_fraction": 0.25,
            },
        },
        "measured": measured,
        "sweeps": sweeps,
    }
    (outdir / "plasma_readability.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    print()
    print(f"{'dataset':<8} {'channel':<8} {'fold':>7} {'state f':>9} {'bulk':>7} {'AUC enr':>9} {'PPV+':>7} {'PPV refined':>12}")
    print("-" * 84)
    for entry in measured:
        match = next(
            (
                s
                for s in sweeps
                if s["dataset"] == entry["dataset"]
                and s["channel"] == entry["channel"]
                and s["electrical_fraction"] == 0.25
            ),
            None,
        )
        print(
            f"{entry['dataset']:<8} {entry['channel']:<8} "
            f"{entry['abundance_fold_state_vs_tumour']:>7.3f} "
            f"{fraction_used(entry):>9.3f} "
            f"{bulk_elevation(fraction_used(entry), 1.0 + entry['simulator_electrical_fold_change']):>7.3f} "
            + (
                f"{match['auc_electrical_enrichment_within_mrd_positive']:>9.3f} "
                f"{match['ppv_within_mrd_positive']:>7.3f} "
                f"{match['ppv_after_electrical_refinement']:>12.3f}"
                if match
                else ""
            )
        )
    print(f"\nwrote {outdir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
