#!/usr/bin/env python3
"""The gate review: the programme's own killing conditions, against measured inputs.

The research plan states five conditions under which the programme is dead
(K1-K5). Three of them are now evaluable, because the state-resolved audits
replaced the simulator's assumed electrical fold and state fraction with
measured ones, and the D0 audit produced a window verdict per candidate.

This script evaluates them and writes the verdict down. It is deliberately
unforgiving in two directions: a condition that is **not evaluable** is
reported as such rather than passed, and a condition that rests on a
model-based projection rather than a measurement says so.

    python scripts/gate_review.py --patients 800
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

#: The killing conditions, as stated in docs/RESEARCH-PLAN.md section 0.
K1_AUC_THRESHOLD = 0.6
K3_AUC_THRESHOLD = 0.65

#: The depth x panel-size grid the programme uses as its affordability space.
DEPTHS = (5_000, 50_000, 200_000, 500_000)
LOCI = (50, 200)
ELECTRICAL_FRACTION = 0.25

#: The specificity bar the programme's thresholds are calibrated to.
TARGET_SPECIFICITY = 0.98

#: The state-expression audits, and how each one's state is used.
DATASETS = {
    "SCLC": "results/gse299684/state_expression.json",
    "NSCLC": "results/gse353299/state_expression.json",
}


def _primary(artefact: dict) -> dict:
    name = artefact["audit"]["primary_definition"]
    return next(s for s in artefact["state_definition_sweep"] if s["definition"] == name)


def _channels(artefact: dict) -> dict[str, dict]:
    return {c["gene"]: c for c in _primary(artefact)["channels"] if c.get("status") == "ok"}


def measured_parameters(root: Path) -> list[dict]:
    """The measured per-cell fold and state fraction, per dataset."""
    rows: list[dict] = []
    for dataset, relative in DATASETS.items():
        path = root / relative
        if not path.exists():
            continue
        artefact = json.loads(path.read_text())
        channels = _channels(artefact)
        if dataset == "SCLC":
            primary = _primary(artefact)
            malignant = primary["n_yap1_positive"] + primary["n_yap1_negative"]
            fraction = primary["n_yap1_positive"] / malignant
            source = "pooled over all libraries"
        else:
            fractions = sorted(
                s["state_positive_fraction_of_malignant"]
                for s in artefact["per_sample"]
                if s["treatment"].strip().lower() == "osi_mrd"
                and s["state_positive_fraction_of_malignant"] is not None
            )
            fraction = fractions[len(fractions) // 2]
            source = "per-library median at the residual-disease timepoint"
        for gene, record in channels.items():
            fold = record.get("linear_fold_vs_yap1negative")
            if fold is None:
                continue
            rows.append(
                {
                    "dataset": dataset,
                    "channel": gene,
                    "abundance_fold_state_vs_tumour": fold,
                    "state_fraction": fraction,
                    "state_fraction_source": source,
                    # The simulator multiplies the bulk marker by 1 + fold * f,
                    # so the measured bulk factor 1 + f * (d - 1) is expressed
                    # in the simulator's own parameter as d - 1.
                    "simulator_electrical_fold_change": max(0.0, fold - 1.0),
                    "bulk_elevation": 1.0 + fraction * (fold - 1.0),
                }
            )
    return rows


def sweep_configuration(
    base: SimulationConfig, entry: dict
) -> list[dict]:
    """The depth x panel-size grid for one measured configuration."""
    # The sweep sets the channel split itself, so only the measured
    # parameters are injected here.
    config = replace(
        base,
        electrical_fold_change=entry["simulator_electrical_fold_change"],
        state_fraction_resistant=entry["state_fraction"],
    )
    rows: list[dict] = []
    for depth in DEPTHS:
        for row in run_channel_allocation_sweep(
            config,
            total_loci=LOCI,
            depth=depth,
            electrical_fractions=(ELECTRICAL_FRACTION,),
            target_specificity=TARGET_SPECIFICITY,
        ):
            rows.append(
                {
                    "sequencing_depth": row["depth"],
                    "total_loci": row["total_loci"],
                    "electrical_fraction": row["electrical_fraction"],
                    "total_reads_per_draw": row["total_reads_per_draw"],
                    "mrd_sensitivity": row["mrd_sensitivity"],
                    "mrd_specificity_vs_responders": row["mrd_specificity_vs_responders"],
                    "mrd_specificity_vs_persistent": row["mrd_specificity_vs_persistent"],
                    "ppv_within_mrd_positive": row["ppv_within_mrd_positive"],
                    "auc_electrical_enrichment_within_mrd_positive": row[
                        "auc_electrical_enrichment_within_mrd_positive"
                    ],
                }
            )
    return rows


def evaluate_k1_k3(entries: list[dict]) -> list[dict]:
    """K1 and K3 for each measured configuration.

    The verdicts follow the plan's own detection rules: K1 is the
    burden-normalised enrichment AUC at the 200,000x / 200-locus operating
    point, and so is K3. The rest of the grid is reported as context, not as
    the verdict, because a configuration with a handful of MRD-positive
    patients can produce an AUC of 1.0 by chance.

    A channel that does not over-express the state in tissue has no readout to
    evaluate: K1 then fires by construction, and the record says so.
    """
    verdicts: list[dict] = []
    for entry in entries:
        rows = entry["sweep"]
        best = max(rows, key=lambda r: r["auc_electrical_enrichment_within_mrd_positive"])
        at_operating_point = next(
            (
                r
                for r in rows
                if r["sequencing_depth"] == 200_000 and r["total_loci"] == 200
            ),
            None,
        )
        auc = at_operating_point["auc_electrical_enrichment_within_mrd_positive"]
        tissue_candidate = entry["abundance_fold_state_vs_tumour"] > 1.0
        verdicts.append(
            {
                "dataset": entry["dataset"],
                "channel": entry["channel"],
                "auc_at_operating_point": auc,
                "auc_best_in_grid": best["auc_electrical_enrichment_within_mrd_positive"],
                "grid": rows,
                "best_in_grid": {
                    "sequencing_depth": best["sequencing_depth"],
                    "total_loci": best["total_loci"],
                    "total_reads_per_draw": best["total_reads_per_draw"],
                    "auc": best["auc_electrical_enrichment_within_mrd_positive"],
                },
                "k1_fired": auc <= K1_AUC_THRESHOLD,
                "k3_fired": auc <= K3_AUC_THRESHOLD,
                "state_candidate_in_tissue": tissue_candidate,
                "k3_at_operating_point": auc <= K3_AUC_THRESHOLD,
                "k3_cleared_somewhere_in_grid": (
                    best["auc_electrical_enrichment_within_mrd_positive"]
                    > K3_AUC_THRESHOLD
                ),
                "state_fraction": entry["state_fraction"],
                "state_fraction_source": entry["state_fraction_source"],
                "abundance_fold_state_vs_tumour": entry[
                    "abundance_fold_state_vs_tumour"
                ],
                "bulk_elevation": entry["bulk_elevation"],
                "basis": (
                    "model-based projection: the simulator run with the measured "
                    "per-cell fold and state fraction, not a plasma measurement"
                ),
            }
        )
    return verdicts


def window_verdicts(root: Path) -> dict:
    """The D0 window verdict per candidate target."""
    path = root / "results/d0_window_audit/d0_window_audit.json"
    if not path.exists():
        return {}
    artefact = json.loads(path.read_text())
    return {
        record["symbol"]: {
            "verdict": (record.get("verdict") or {}).get("class"),
            "window_fold": (record.get("verdict") or {}).get(
                "window_fold_vs_max_offtarget"
            ),
        }
        for record in artefact.get("targets", [])
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(REPO))
    parser.add_argument("--outdir", default="results/gate_review")
    parser.add_argument("--patients", type=int, default=800)
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    outdir = root / args.outdir
    outdir.mkdir(parents=True, exist_ok=True)

    base = SimulationConfig(
        regime=Regime.POST_TREATMENT,
        seed=20261106,
        n_patients_per_arm=args.patients,
    )

    entries = measured_parameters(root)
    if not entries:
        print("no state-expression artefacts found; run them first", file=sys.stderr)
        return 1

    for entry in entries:
        entry["sweep"] = sweep_configuration(base, entry)

    k1_k3 = evaluate_k1_k3(entries)
    windows = window_verdicts(root)

    # --- the conditions ---
    conditions: list[dict] = []

    fired_k1 = [v for v in k1_k3 if v["k1_fired"]]
    fired_k3 = [v for v in k1_k3 if v["k3_fired"]]
    candidates = [v for v in k1_k3 if v["state_candidate_in_tissue"]]
    conditions.append(
        {
            "id": "K1",
            "condition": (
                "The state-specific readout carries no information beyond tumour "
                "burden"
            ),
            "how_detected": "D2: burden-normalised enrichment AUC <= 0.6",
            "status": "fired" if fired_k1 else "not_fired",
            "scope": "per dataset and channel",
            "evidence": [
                {
                    "dataset": v["dataset"],
                    "channel": v["channel"],
                    "auc_at_operating_point": v["auc_at_operating_point"],
                }
                for v in k1_k3
            ],
            "fired_for": [
                f"{v['dataset']} / {v['channel']}" for v in fired_k1
            ],
            "state_candidates": [
                f"{v['dataset']} / {v['channel']}" for v in candidates
            ],
            "basis": (
                "model-based projection with measured inputs; not a plasma "
                "measurement"
            ),
        }
    )

    conditions.append(
        {
            "id": "K3",
            "condition": (
                "The state cannot be inferred from plasma at any affordable read "
                "budget"
            ),
            "how_detected": (
                "D3: enrichment AUC <= 0.65 at 200,000x / 200 loci"
            ),
            "status": "fired" if fired_k3 else "not_fired",
            "scope": "per dataset and channel, over the depth x panel-size grid",
            "evidence": [
                {
                    "dataset": v["dataset"],
                    "channel": v["channel"],
                    "auc_at_operating_point": v["auc_at_operating_point"],
                    "auc_best_in_grid": v["auc_best_in_grid"],
                    "best_in_grid": v["best_in_grid"],
                    "state_candidate_in_tissue": v["state_candidate_in_tissue"],
                }
                for v in k1_k3
            ],
            "fired_for": [
                f"{v['dataset']} / {v['channel']}" for v in fired_k3
            ],
            "state_candidates": [
                f"{v['dataset']} / {v['channel']}" for v in candidates
            ],
            "basis": (
                "model-based projection with measured inputs; not a plasma "
                "measurement"
            ),
        }
    )

    # K2: the state is present and relapse-associated in lung.
    nsclc_state = None
    nsclc_path = root / DATASETS["NSCLC"]
    if nsclc_path.exists():
        artefact = json.loads(nsclc_path.read_text())
        per_timepoint = {e["treatment"]: e for e in artefact["per_timepoint"]}
        naive = per_timepoint.get("treatment_naive", {})
        mrd = per_timepoint.get("osi_mrd", {})
        nsclc_state = {
            "treatment_naive_state_fraction": naive.get(
                "state_positive_fraction_of_malignant"
            ),
            "mrd_state_fraction_pooled": mrd.get(
                "state_positive_fraction_of_malignant"
            ),
        }
    conditions.append(
        {
            "id": "K2",
            "condition": (
                "The state is not present, or not relapse-associated, in lung"
            ),
            "how_detected": (
                "D2: no state-associated methylation delta between primary and "
                "relapsed tissue"
            ),
            "status": "not_evaluable",
            "scope": "the condition as written names a methylation delta",
            "evidence": {
                "state_resolved_measurements": nsclc_state,
                "note": (
                    "The state is present and more frequent after treatment in "
                    "EGFR-mutant NSCLC, which is evidence against K2 firing. It "
                    "is not the methylation delta the condition names, and no "
                    "primary-versus-relapsed methylation comparison exists in "
                    "this repository, so the condition is recorded as not "
                    "evaluable rather than passed. For relapsed SCLC there is no "
                    "treatment-naive comparator at all."
                ),
            },
            "basis": "partially addressable, not evaluable as written",
        }
    )

    # K4: every candidate target has an unacceptable therapeutic window.
    not_viable = [
        gene
        for gene, record in windows.items()
        if record["verdict"] == "not_a_lung_target"
    ]
    no_bulk_window = [
        gene
        for gene, record in windows.items()
        if record["verdict"] == "no_bulk_window"
    ]
    conditions.append(
        {
            "id": "K4",
            "condition": "Every candidate target has an unacceptable therapeutic window",
            "how_detected": "D0 gate: GTEx specificity verdict fails",
            "status": "fired",
            "scope": "systemic drug delivery",
            "evidence": {
                "not_viable_as_lung_targets": not_viable,
                "no_bulk_tissue_window": no_bulk_window,
                "window_verdicts": windows,
                "state_resolved_counter_evidence": (
                    "The state-resolved audits found the state channel-high in "
                    "the target tissue for the matched disease and channel, so a "
                    "state-directed rather than systemic modality is not excluded "
                    "by the expression evidence. No such modality exists in this "
                    "programme, and the D0 window findings for KCa3.1 (lung "
                    "expression 12x below minor salivary gland, loss-of-function "
                    "intolerance, on-target neurological and cardiac liabilities) "
                    "and for Piezo1 (no separation from PIEZO2, no clinical "
                    "asset) are unaffected."
                ),
            },
            "basis": "measurement (GTEx, Open Targets, ClinVar)",
        }
    )

    conditions.append(
        {
            "id": "K5",
            "condition": (
                "Suppressing the state does not reduce relapse competence in "
                "patient-derived models"
            ),
            "how_detected": "D5: no differential killing of the state-bearing clone",
            "status": "not_evaluable",
            "scope": "requires perturbation and a viability readout",
            "evidence": {
                "note": (
                    "No wet-lab arm has been run. The state-resolved datasets "
                    "are observational, and one of them (GSE325242, the "
                    "RORB-loss organoid study) would have been the closest "
                    "available perturbation system, but its deposit carries no "
                    "gene annotation and cannot be measured."
                )
            },
            "basis": "no experiment has been performed",
        }
    )

    payload = {
        "audit": {
            "id": "gate-review-2026-11",
            "generated_by": "scripts/gate_review.py",
            "generated_at": datetime.now(UTC).isoformat(),
            "patients_per_arm": args.patients,
            "depths": list(DEPTHS),
            "loci": list(LOCI),
            "electrical_fraction": ELECTRICAL_FRACTION,
            "k1_auc_threshold": K1_AUC_THRESHOLD,
            "k3_auc_threshold": K3_AUC_THRESHOLD,
            "note": (
                "K1 and K3 are evaluated on a model-based projection: the "
                "simulator run with the measured per-cell fold and state "
                "fraction. They are not plasma measurements, and a real plasma "
                "cohort could move them. K4 rests on measurements; K2 and K5 are "
                "not evaluable on the evidence in this repository."
            ),
        },
        "conditions": conditions,
        "k1_k3_detail": k1_k3,
        "measured_parameters": [
            {k: v for k, v in entry.items() if k != "sweep"} for entry in entries
        ],
    }

    (outdir / "gate_review.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    lines = [
        "condition\tstatus\tscope\tfired_for\tdetail",
    ]
    for condition in conditions:
        fired = ", ".join(condition.get("fired_for") or []) or "-"
        lines.append(
            "\t".join(
                [
                    condition["id"],
                    condition["status"],
                    condition["scope"],
                    fired,
                    condition["how_detected"],
                ]
            )
        )
    lines.append("")
    lines.append("dataset\tchannel\tauc_at_200k_200\tauc_best_in_grid\tk1_fired\tk3_fired")
    for verdict in k1_k3:
        lines.append(
            "\t".join(
                [
                    verdict["dataset"],
                    verdict["channel"],
                    f"{verdict['auc_at_operating_point']:.4f}",
                    f"{verdict['auc_best_in_grid']:.4f}",
                    "yes" if verdict["k1_fired"] else "no",
                    "yes" if verdict["k3_fired"] else "no",
                ]
            )
        )
    (outdir / "gate_matrix.tsv").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print()
    print(f"{'condition':<12}{'status':<16}{'fired for'}")
    print("-" * 78)
    for condition in conditions:
        fired = ", ".join(condition.get("fired_for") or []) or "-"
        print(f"{condition['id']:<12}{condition['status']:<16}{fired}")
    print()
    print(
        f"{'dataset':<8}{'channel':<10}{'AUC@200k/200':>13}{'best':>9}"
        f"{'K1':>5}{'K3':>5}  candidate"
    )
    for verdict in k1_k3:
        print(
            f"{verdict['dataset']:<8}{verdict['channel']:<10}"
            f"{verdict['auc_at_operating_point']:>13.4f}"
            f"{verdict['auc_best_in_grid']:>9.4f}"
            f"{'fire' if verdict['k1_fired'] else '-':>5}"
            f"{'fire' if verdict['k3_fired'] else '-':>5}"
            f"  {'yes' if verdict['state_candidate_in_tissue'] else 'no'}"
        )
    print(f"\nwrote {outdir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
