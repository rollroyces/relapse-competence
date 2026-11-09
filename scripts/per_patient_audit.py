#!/usr/bin/env python3
"""The per-patient audit: run the plasma projection for each tumour, not for an average.

The gate review projects the plasma readout from a *pooled* per-cell fold and a
*pooled* state fraction. Both pooled values are cell-count weighted, and in the
relapsed-SCLC deposit three libraries hold 84% of the state cells. A pooled
fold therefore need not describe any individual tumour.

This script re-runs the projection with each library's own measured fold and
its own measured state fraction, over the same depth x panel-size grid the
gate review uses, and records what the readout would do for that tumour.

Two layers are reported, and they are not the same kind of statement:

- the **measurement**: the library's own fold and state fraction, and whether
  the channel is on in that tumour. This needs no assumption.
- the **projection**: what a plasma assay would score, given that tumour.
  This needs a counterfactual the repository has never measured -- the state
  fraction of the MRD-positive patients who do *not* relapse -- so the
  projection is swept over it and the band is reported, not a point.

The pooled inputs are re-projected here as a **control**: they must reproduce
the gate review's published operating-point AUCs exactly, or the per-library
numbers are not comparable with them.

    python scripts/per_patient_audit.py --patients 800

Outputs
-------
    results/per_patient_audit/per_patient_audit.json
    results/per_patient_audit/per_patient_audit.tsv
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from relapse_competence.benchmark import run_channel_allocation_sweep  # noqa: E402
from relapse_competence.config import Regime, SimulationConfig  # noqa: E402

#: The gate review's thresholds, unchanged.
K1_AUC_THRESHOLD = 0.6
K3_AUC_THRESHOLD = 0.65

#: The depth x panel-size grid the programme uses as its affordability space.
DEPTHS = (5_000, 50_000, 200_000, 500_000)
LOCI = (50, 200)

#: The plan's own operating point.
OPERATING_DEPTH = 200_000
OPERATING_LOCI = 200

ELECTRICAL_FRACTION = 0.25
TARGET_SPECIFICITY = 0.98

#: The simulator's default state fraction for the MRD-positive patients who do
#: not relapse. This is an assumption, not a measurement: no deposit in this
#: repository contains a relapsed-SCLC MRD-positive non-relapser cohort. The
#: projection is swept over it.
PERSISTENT_FRACTIONS = (0.0, 0.05, 0.10, 0.20)
DEFAULT_PERSISTENT_FRACTION = 0.10

#: The channel to project, per dataset. These are the configurations the gate
#: review named as state candidates.
CHANNELS = {
    "SCLC": ("KCNN4", "PIEZO1"),
    "NSCLC": ("KCNN4",),
}

#: The state-expression artefacts, and how the pooled inputs are read from
#: them, so the control uses the gate review's own numbers.
POOLED_ARTEFACTS = {
    "SCLC": "results/gse299684/state_expression.json",
    "NSCLC": "results/gse353299/state_expression.json",
}
GATE_REVIEW_ARTEFACT = "results/gate_review/gate_review.json"


def _base_config(patients: int) -> SimulationConfig:
    return SimulationConfig(
        regime=Regime.POST_TREATMENT,
        seed=20261106,
        n_patients_per_arm=patients,
    )


def _pooled_inputs(root: Path) -> dict[tuple[str, str], dict]:
    """The pooled fold and state fraction, read as the gate review reads them."""
    rows: dict[tuple[str, str], dict] = {}
    for dataset, relative in POOLED_ARTEFACTS.items():
        artefact = json.loads((root / relative).read_text())
        primary = artefact["audit"]["primary_definition"]
        entry = next(
            s for s in artefact["state_definition_sweep"] if s["definition"] == primary
        )
        channels = {
            c["gene"]: c for c in entry["channels"] if c.get("status") == "ok"
        }
        if dataset == "SCLC":
            # The two scripts name their state counters differently, and the
            # pooled fraction has to be the gate review's number, so the
            # published artefact's own naming is read rather than assumed.
            positive = entry.get("n_yap1_positive", entry.get("n_state_positive"))
            negative = entry.get("n_yap1_negative", entry.get("n_state_negative"))
            fraction = positive / (positive + negative)
        else:
            fractions = sorted(
                s["state_positive_fraction_of_malignant"]
                for s in artefact["per_sample"]
                if s["treatment"].strip().lower() == "osi_mrd"
                and s["state_positive_fraction_of_malignant"] is not None
            )
            fraction = fractions[len(fractions) // 2]
        for gene in CHANNELS[dataset]:
            fold = channels[gene].get("linear_fold_vs_yap1negative")
            if fold is None:
                continue
            rows[(dataset, gene)] = {
                "abundance_fold": fold,
                "state_fraction": fraction,
                "detection_ratio": channels[gene].get(
                    "detection_ratio_vs_yap1negative"
                ),
            }
    return rows


def _run_grid(
    base: SimulationConfig,
    fold: float,
    state_fraction: float,
    persistent_fraction: float,
    depths: tuple[int, ...],
    loci: tuple[int, ...],
    state_fraction_sd: float | None = None,
) -> list[dict]:
    """The depth x panel-size grid for one set of inputs.

    ``state_fraction_sd`` of ``None`` leaves the simulator's own between-patient
    spread in place, which is what the gate review used and therefore what the
    control must use. The per-library projections set it to zero, so that the
    cohort is homogeneous in the state fraction and the comparison is with the
    library's own tumour.
    """
    changes: dict = {
        "electrical_fold_change": max(0.0, fold - 1.0),
        "state_fraction_resistant": state_fraction,
        "state_fraction_persistent": persistent_fraction,
    }
    if state_fraction_sd is not None:
        changes["state_fraction_resistant_sd"] = state_fraction_sd
    config = replace(base, **changes)
    rows: list[dict] = []
    for depth in depths:
        for row in run_channel_allocation_sweep(
            config,
            total_loci=loci,
            depth=depth,
            electrical_fractions=(ELECTRICAL_FRACTION,),
            target_specificity=TARGET_SPECIFICITY,
        ):
            rows.append(
                {
                    "sequencing_depth": depth,
                    "total_loci": row["total_loci"],
                    "total_reads_per_draw": row["total_reads_per_draw"],
                    "auc": row["auc_electrical_enrichment_within_mrd_positive"],
                    "mrd_sensitivity": row["mrd_sensitivity"],
                    "mrd_specificity_vs_responders": row[
                        "mrd_specificity_vs_responders"
                    ],
                    "ppv_within_mrd_positive": row["ppv_within_mrd_positive"],
                }
            )
    return rows


def _control(root: Path, base: SimulationConfig) -> dict:
    """Re-project the pooled inputs and compare with the gate review."""
    published: dict[tuple[str, str], float] = {}
    gate_path = root / GATE_REVIEW_ARTEFACT
    if gate_path.exists():
        gate = json.loads(gate_path.read_text())
        for verdict in gate["k1_k3_detail"]:
            published[(verdict["dataset"], verdict["channel"])] = verdict[
                "auc_at_operating_point"
            ]
    pooled = _pooled_inputs(root)
    entries: list[dict] = []
    for (dataset, gene), values in sorted(pooled.items()):
        rows = _run_grid(
            base,
            values["abundance_fold"],
            values["state_fraction"],
            DEFAULT_PERSISTENT_FRACTION,
            (OPERATING_DEPTH,),
            (OPERATING_LOCI,),
        )
        recomputed = rows[0]["auc"]
        reference = published.get((dataset, gene))
        entries.append(
            {
                "dataset": dataset,
                "channel": gene,
                "abundance_fold": values["abundance_fold"],
                "state_fraction": values["state_fraction"],
                "recomputed_auc_at_operating_point": recomputed,
                "gate_review_auc_at_operating_point": reference,
                "matches": (
                    reference is not None and abs(recomputed - reference) < 1e-12
                ),
                "absolute_difference": (
                    abs(recomputed - reference) if reference is not None else None
                ),
            }
        )
    return {
        "note": (
            "The pooled inputs, re-projected on this script's code path, must "
            "reproduce the gate review's published operating-point AUCs."
        ),
        "entries": entries,
        "all_match": all(e["matches"] for e in entries) if entries else False,
    }


def _per_library(
    root: Path, base: SimulationConfig
) -> tuple[list[dict], list[dict]]:
    """The per-library grid, and the per-library summaries."""
    folds_path = root / "results/per_library_folds/per_library_folds.json"
    if not folds_path.exists():
        raise SystemExit(
            "results/per_library_folds/per_library_folds.json is missing; run "
            "scripts/per_library_folds.py first"
        )
    folds = json.loads(folds_path.read_text())

    records: list[dict] = []
    for library in folds["per_library"]:
        dataset = library["dataset"]
        for channel in CHANNELS.get(dataset, ()):
            entry = library["channels"].get(channel)
            if entry is None or entry.get("status") != "ok":
                continue
            fold = entry.get("linear_fold")
            if fold is None:
                continue
            fraction = library["state_fraction"]
            grid = _run_grid(
                base,
                fold,
                fraction,
                DEFAULT_PERSISTENT_FRACTION,
                DEPTHS,
                LOCI,
                state_fraction_sd=0.0,
            )
            operating = next(
                row
                for row in grid
                if row["sequencing_depth"] == OPERATING_DEPTH
                and row["total_loci"] == OPERATING_LOCI
            )
            sensitivity = []
            for persistent in PERSISTENT_FRACTIONS:
                rows = _run_grid(
                    base,
                    fold,
                    fraction,
                    persistent,
                    (OPERATING_DEPTH,),
                    (OPERATING_LOCI,),
                    state_fraction_sd=0.0,
                )
                sensitivity.append(
                    {
                        "state_fraction_persistent": persistent,
                        "auc": rows[0]["auc"],
                        "k1_fired": rows[0]["auc"] <= K1_AUC_THRESHOLD,
                        "k3_fired": rows[0]["auc"] <= K3_AUC_THRESHOLD,
                    }
                )
            records.append(
                {
                    "dataset": dataset,
                    "accession": library["accession"],
                    "label": library["label"],
                    "treatment": library["treatment"],
                    "channel": channel,
                    "inputs": {
                        "n_malignant": library["n_malignant"],
                        "n_state": library["n_state"],
                        "state_fraction": fraction,
                        "abundance_fold": fold,
                        "electrical_fold_change": max(0.0, fold - 1.0),
                        "detection_ratio": entry.get("detection_ratio"),
                        "fold_stable": entry.get("fold_stable"),
                        "n_state_cells_for_fold": entry.get("n_state_cells"),
                    },
                    "grid": grid,
                    "operating_point": {
                        "sequencing_depth": OPERATING_DEPTH,
                        "total_loci": OPERATING_LOCI,
                        "auc": operating["auc"],
                        "mrd_sensitivity": operating["mrd_sensitivity"],
                        "mrd_specificity_vs_responders": operating[
                            "mrd_specificity_vs_responders"
                        ],
                        "ppv_within_mrd_positive": operating[
                            "ppv_within_mrd_positive"
                        ],
                        "k1_fired": operating["auc"] <= K1_AUC_THRESHOLD,
                        "k3_fired": operating["auc"] <= K3_AUC_THRESHOLD,
                    },
                    "persistent_sensitivity": sensitivity,
                }
            )

    summaries: list[dict] = []
    for dataset, channels in CHANNELS.items():
        for channel in channels:
            subset = [
                r
                for r in records
                if r["dataset"] == dataset and r["channel"] == channel
            ]
            if not subset:
                continue
            aucs = [r["operating_point"]["auc"] for r in subset]
            computable = [
                r for r in subset if r["inputs"]["abundance_fold"] is not None
            ]
            above_one = [
                r for r in computable if r["inputs"]["abundance_fold"] > 1.0
            ]
            summaries.append(
                {
                    "dataset": dataset,
                    "channel": channel,
                    "n_libraries": len(subset),
                    "n_fold_computable": len(computable),
                    "n_fold_above_one": len(above_one),
                    "fold_median": statistics.median(
                        r["inputs"]["abundance_fold"] for r in computable
                    )
                    if computable
                    else None,
                    "fold_min": min(
                        r["inputs"]["abundance_fold"] for r in computable
                    )
                    if computable
                    else None,
                    "fold_max": max(
                        r["inputs"]["abundance_fold"] for r in computable
                    )
                    if computable
                    else None,
                    "n_clearing_k3": sum(
                        1 for r in subset if not r["operating_point"]["k3_fired"]
                    ),
                    "n_firing_k1": sum(
                        1 for r in subset if r["operating_point"]["k1_fired"]
                    ),
                    "auc_at_operating_point": {
                        "min": min(aucs),
                        "median": statistics.median(aucs),
                        "max": max(aucs),
                    },
                    "state_fraction": {
                        "min": min(r["inputs"]["state_fraction"] for r in subset),
                        "median": statistics.median(
                            r["inputs"]["state_fraction"] for r in subset
                        ),
                        "max": max(r["inputs"]["state_fraction"] for r in subset),
                    },
                }
            )
    return records, summaries


def _tsv(records: list[dict]) -> str:
    header = [
        "dataset",
        "accession",
        "label",
        "treatment",
        "channel",
        "n_malignant",
        "n_state",
        "state_fraction",
        "abundance_fold",
        "fold_stable",
        "auc_at_200k_200",
        "k1_fired",
        "k3_fired",
        "mrd_sensitivity",
        "mrd_specificity_vs_responders",
        "ppv_within_mrd_positive",
    ]
    for depth in DEPTHS:
        for loci in LOCI:
            header.append(f"auc_{depth}x_{loci}")
    for persistent in PERSISTENT_FRACTIONS:
        header.append(f"auc_persistent_{persistent:.2f}")
    lines = ["\t".join(header)]
    for r in records:
        operating = r["operating_point"]
        cells = [
            r["dataset"],
            r["accession"],
            r["label"],
            r["treatment"] or "",
            r["channel"],
            str(r["inputs"]["n_malignant"]),
            str(r["inputs"]["n_state"]),
            f"{r['inputs']['state_fraction']:.6f}",
            f"{r['inputs']['abundance_fold']:.6f}",
            "yes" if r["inputs"]["fold_stable"] else "no",
            f"{operating['auc']:.6f}",
            "yes" if operating["k1_fired"] else "no",
            "yes" if operating["k3_fired"] else "no",
            f"{operating['mrd_sensitivity']:.6f}",
            f"{operating['mrd_specificity_vs_responders']:.6f}",
            f"{operating['ppv_within_mrd_positive']:.6f}",
        ]
        for depth in DEPTHS:
            for loci in LOCI:
                cell = next(
                    g
                    for g in r["grid"]
                    if g["sequencing_depth"] == depth and g["total_loci"] == loci
                )
                cells.append(f"{cell['auc']:.6f}")
        for entry in r["persistent_sensitivity"]:
            cells.append(f"{entry['auc']:.6f}")
        lines.append("\t".join(cells))
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--patients", type=int, default=800)
    parser.add_argument("--outdir", default="results/per_patient_audit")
    args = parser.parse_args(argv)

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    base = _base_config(args.patients)
    control = _control(REPO, base)
    for entry in control["entries"]:
        status = "MATCH" if entry["matches"] else "MISMATCH"
        print(
            f"control {entry['dataset']} / {entry['channel']}: {status} "
            f"(recomputed {entry['recomputed_auc_at_operating_point']:.6f}, "
            f"published {entry['gate_review_auc_at_operating_point']})"
        )
    if not control["all_match"]:
        print(
            "the pooled inputs do not reproduce the gate review's published "
            "AUCs; the per-library numbers are not comparable with them",
            file=sys.stderr,
        )
        return 1

    records, summaries = _per_library(REPO, base)

    document = {
        "audit": {
            "id": "per-patient-audit-2026-11",
            "generated_by": "scripts/per_patient_audit.py",
            "generated_at": datetime.now(UTC).isoformat(),
            "patients_per_arm": args.patients,
            "depths": list(DEPTHS),
            "loci": list(LOCI),
            "electrical_fraction": ELECTRICAL_FRACTION,
            "operating_point": {
                "sequencing_depth": OPERATING_DEPTH,
                "total_loci": OPERATING_LOCI,
            },
            "k1_auc_threshold": K1_AUC_THRESHOLD,
            "k3_auc_threshold": K3_AUC_THRESHOLD,
            "persistent_state_fractions": list(PERSISTENT_FRACTIONS),
            "default_persistent_state_fraction": DEFAULT_PERSISTENT_FRACTION,
            "note": (
                "The per-library projection holds the relapsers' state fraction "
                "at that library's measured value with no between-patient "
                "spread, so the cohort is homogeneous in the way that matters. "
                "The MRD-positive patients who do not relapse are assigned a "
                "state fraction this repository has never measured; the "
                "projection is swept over it rather than presented as a point. "
                "The measurement layer -- each library's own fold and state "
                "fraction -- carries no assumption at all."
            ),
        },
        "control": control,
        "summaries": summaries,
        "per_library": records,
    }

    (outdir / "per_patient_audit.json").write_text(
        json.dumps(document, indent=2) + "\n"
    )
    (outdir / "per_patient_audit.tsv").write_text(_tsv(records))

    for summary in summaries:
        print(
            f"{summary['dataset']} / {summary['channel']}: "
            f"fold > 1 in {summary['n_fold_above_one']}/"
            f"{summary['n_fold_computable']} libraries; "
            f"{summary['n_clearing_k3']}/{summary['n_libraries']} clear K3"
        )
    print(f"wrote {outdir / 'per_patient_audit.json'}")
    print(f"wrote {outdir / 'per_patient_audit.tsv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
