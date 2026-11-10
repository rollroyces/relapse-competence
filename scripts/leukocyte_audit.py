#!/usr/bin/env python3
"""The leukocyte audit: what a bulk plasma channel can and cannot read.

The plasma model has no leukocyte compartment. The plasma cfDNA pool is
modelled as tumour-shed material plus a 1e-6 sequencing-error floor, so the
electrical channel's signal is the tumour's contribution alone. In bulk
plasma that is not the case: most cfDNA is leukocyte-derived, and KCa3.1 is
expressed in immune cells, so the channel locus carries a large leukocyte
background and the tumour's state is a small perturbation on it.

This script turns that compartment on -- default-off, and the golden fixture
stays byte-identical when it is off -- and sweeps it against the tumour's
cfDNA share, reporting the enrichment AUC under both statistics:

- the **raw** enrichment, which is the programme's published statistic: the
  electrical channel's per-locus signal over the mutation channel's;
- the **tumour-attributable** enrichment, which subtracts the leukocyte
  reads first and is what a readout that localises the channel transcript to
  the tumour would measure.

    python scripts/leukocyte_audit.py --patients 800

Outputs
-------
    results/leukocyte_audit/leukocyte_audit.json
    results/leukocyte_audit/leukocyte_audit.tsv
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

from relapse_competence.benchmark import _auc, collect_outcomes  # noqa: E402
from relapse_competence.config import Regime, SimulationConfig  # noqa: E402

#: The programme's operating point, unchanged: 200,000x, 200 loci, 25% of the
#: read budget on the electrical channel.
OPERATING_DEPTH = 200_000
OPERATING_LOCI = 200
ELECTRICAL_FRACTION = 0.25
TARGET_SPECIFICITY = 0.98

#: The published operating-point AUCs, which the control has to reproduce.
PUBLISHED_AUC = {
    ("NSCLC", "KCNN4"): 0.9928621553884712,
    ("SCLC", "KCNN4"): 0.706544901065449,
    ("SCLC", "PIEZO1"): 0.6945048256673333,
}

#: The measured inputs for the configurations the gate review named: the
#: per-cell fold and the state fraction, from the committed artefacts.
MEASURED = {
    ("NSCLC", "KCNN4"): {
        "fold": 3.6979371667856475,
        "state_fraction": 0.3916913946587537,
    },
    ("SCLC", "KCNN4"): {
        "fold": 2.5538652224413894,
        "state_fraction": 0.10402781802376122,
    },
    ("SCLC", "PIEZO1"): {
        "fold": 3.3631214355966152,
        "state_fraction": 0.10402781802376122,
    },
}

#: Multipliers on the tumour's cfDNA yield, which is the axis the audit
#: sweeps: how much tumour DNA has to be in the plasma for the readout to
#: work.
TUMOUR_SHARE_MULTIPLIERS = (1, 3, 10, 30, 100, 300, 1000, 3000, 10000)

#: The leukocyte compartment's share of the electrical locus's signal. Zero is
#: the model as published; the others are the regime bulk plasma is in.
LEUKOCYTE_FRACTIONS = (0.0, 0.5, 0.9, 0.99)

#: The programme's K3 threshold, the criterion the operating point has to
#: clear in the bulk-plasma regime.
K3_THRESHOLD = 0.65

#: The search space for the re-derived operating point: the depth and the size
#: of the leukocyte reference set. The reference set takes its loci from the
#: mutation panel, so the panel cannot grow past the point where the mutation
#: channel has no loci left.
DERIVATION_DEPTHS = (200_000, 2_000_000, 20_000_000)
DERIVATION_REFERENCE_LOCI = (5, 20, 50)

#: The leukocyte compartment's share in the regime the derivation is run at:
#: bulk plasma, where the state's own share of the channel is about two per
#: cent of the measurement.
DERIVATION_LEUKOCYTE_FRACTION = 0.99


def _config(
    patients: int,
    fold: float,
    state_fraction: float,
    tumour_multiplier: float,
    leukocyte_fraction: float,
    depth: int = OPERATING_DEPTH,
    n_reference_loci: int = 0,
) -> SimulationConfig:
    base = SimulationConfig(
        regime=Regime.POST_TREATMENT,
        seed=20261106,
        n_patients_per_arm=patients,
    )
    n_electrical = int(round(OPERATING_LOCI * ELECTRICAL_FRACTION))
    return replace(
        base,
        electrical_fold_change=max(0.0, fold - 1.0),
        state_fraction_resistant=state_fraction,
        sequencing_depth=depth,
        n_loci=OPERATING_LOCI - n_electrical - n_reference_loci,
        n_electrical_loci=n_electrical,
        n_leukocyte_reference_loci=n_reference_loci,
        tumor_vaf_per_mm3=base.tumor_vaf_per_mm3 * tumour_multiplier,
        leukocyte_channel_fraction=leukocyte_fraction,
    )


def _run(
    patients: int,
    fold: float,
    state_fraction: float,
    tumour_multiplier: int,
    leukocyte_fraction: float,
    depth: int = OPERATING_DEPTH,
    n_reference_loci: int = 0,
) -> dict:
    cfg = _config(
        patients,
        fold,
        state_fraction,
        tumour_multiplier,
        leukocyte_fraction,
        depth,
        n_reference_loci,
    )
    outcomes, threshold = collect_outcomes(cfg, target_specificity=TARGET_SPECIFICITY)
    evaluation = [o for o in outcomes if o.split == "evaluation"]
    mrd = [o for o in evaluation if o.mrd_flagged]
    if not mrd:
        return {
            "read_threshold": threshold,
            "n_mrd_positive": 0,
            "n_relapsers": 0,
            "auc_raw": None,
            "auc_attributable": None,
            "median_tumour_cfDNA_share": None,
        }
    raw = _auc(
        [o.electrical_enrichment for o in mrd], [o.relapsed for o in mrd]
    )
    attributable = _auc(
        [o.electrical_enrichment_attributable for o in mrd],
        [o.relapsed for o in mrd],
    )
    reference_corrected = _auc(
        [o.electrical_enrichment_reference_corrected for o in mrd],
        [o.relapsed for o in mrd],
    )
    return {
        "read_threshold": threshold,
        "n_mrd_positive": len(mrd),
        "n_relapsers": sum(1 for o in mrd if o.relapsed),
        "auc_raw": raw,
        "auc_attributable": attributable,
        "auc_reference_corrected": reference_corrected,
        # The tumour's share of the cfDNA pool, measured from the mutation
        # channel: this is what the electrical channel is read against.
        "median_tumour_cfDNA_share": statistics.median(
            o.mutation_vaf for o in mrd
        ),
        # The two arms separately, because the burden-normalised statistic
        # amplifies the noise by the inverse of the patient's own share, and
        # the two arms of an MRD-positive cohort do not sit at the same one.
        "median_tumour_cfDNA_share_relapsers": statistics.median(
            [o.mutation_vaf for o in mrd if o.relapsed]
        )
        if any(o.relapsed for o in mrd)
        else None,
        "median_tumour_cfDNA_share_non_relapsers": statistics.median(
            [o.mutation_vaf for o in mrd if not o.relapsed]
        )
        if any(not o.relapsed for o in mrd)
        else None,
    }


def _derive_operating_point(patients: int, wanted: list[tuple[str, str]]) -> dict:
    """Search the panel space for an operating point that survives the compartment.

    The criterion is the programme's own: the reference-corrected enrichment
    AUC has to clear K3 in the bulk-plasma regime, at the measured tumour
    share. What the panel can be is the search space -- sequencing depth, and
    the size of the leukocyte reference set -- because the correction's
    precision is set by how well the background can be measured in the
    sample, and that noise is amplified by the tumour's own small cfDNA
    share.

    The derivation is run on the surviving readout, EGFR-mutant NSCLC on
    KCa3.1; the SCLC configurations were already carrying marginal margins
    before the compartment was added.
    """
    dataset, channel = wanted[0]
    values = MEASURED[(dataset, channel)]
    rows: list[dict] = []
    for depth in DERIVATION_DEPTHS:
        for n_reference in DERIVATION_REFERENCE_LOCI:
            result = _run(
                patients,
                values["fold"],
                values["state_fraction"],
                1,
                DERIVATION_LEUKOCYTE_FRACTION,
                depth=depth,
                n_reference_loci=n_reference,
            )
            corrected = result["auc_reference_corrected"]
            rows.append(
                {
                    "depth": depth,
                    "n_leukocyte_reference_loci": n_reference,
                    "total_reads_per_draw": depth * OPERATING_LOCI,
                    "n_mrd_positive": result["n_mrd_positive"],
                    "median_tumour_cfDNA_share": result[
                        "median_tumour_cfDNA_share"
                    ],
                    "median_tumour_cfDNA_share_relapsers": result[
                        "median_tumour_cfDNA_share_relapsers"
                    ],
                    "median_tumour_cfDNA_share_non_relapsers": result[
                        "median_tumour_cfDNA_share_non_relapsers"
                    ],
                    "auc_raw": result["auc_raw"],
                    "auc_attributable": result["auc_attributable"],
                    "auc_reference_corrected": corrected,
                    "clears_k3": (
                        corrected is not None and corrected >= K3_THRESHOLD
                    ),
                }
            )
            print(
                f"derivation depth={depth:>9,} ref={n_reference:>3}  "
                f"raw={result['auc_raw']:.4f}  "
                f"attributable={result['auc_attributable']:.4f}  "
                f"reference_corrected="
                f"{corrected if corrected is None else round(corrected, 4)}  "
                f"{'CLEARS K3' if rows[-1]['clears_k3'] else ''}"
            )
    clearing = [r for r in rows if r["clears_k3"]]
    if clearing:
        selected = min(
            clearing,
            key=lambda r: (
                r["total_reads_per_draw"],
                -r["n_leukocyte_reference_loci"],
            ),
        )
    elif rows:
        # Nothing clears the threshold. Report the best available panel rather
        # than nothing, and say plainly that it falls short.
        selected = max(
            rows,
            key=lambda r: (
                r["auc_reference_corrected"] or 0.0,
                -r["total_reads_per_draw"],
            ),
        )
    else:
        selected = None
    return {
        "audit": {
            "id": "leukocyte-audit-operating-point-2026-11",
            "generated_by": "scripts/leukocyte_audit.py",
            "generated_at": datetime.now(UTC).isoformat(),
            "patients_per_arm": patients,
            "configuration": f"{dataset}/{channel}",
            "criterion": {
                "statistic": "reference-corrected enrichment AUC",
                "threshold": K3_THRESHOLD,
                "leukocyte_fraction": DERIVATION_LEUKOCYTE_FRACTION,
                "total_loci": OPERATING_LOCI,
                "electrical_fraction": ELECTRICAL_FRACTION,
                "tumour_share_multiplier": 1,
            },
            "note": (
                "The reference set takes its loci from the mutation panel, so "
                "the panel cannot grow past the point where the mutation "
                "channel has no loci left. The selection is the cheapest "
                "configuration in reads per draw that clears the threshold; "
                "the whole frontier is reported so the trade can be made "
                "differently."
            ),
        },
        "frontier": rows,
        "selected": selected,
        "selected_reads_per_draw": (
            selected["total_reads_per_draw"] if selected else None
        ),
        "anything_clears_k3": bool(clearing),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--patients", type=int, default=800)
    parser.add_argument("--outdir", default="results/leukocyte_audit")
    parser.add_argument(
        "--configurations",
        default=",".join(f"{d}/{c}" for d, c in MEASURED),
        help="which measured configurations to sweep",
    )
    parser.add_argument(
        "--control-only",
        action="store_true",
        help=(
            "run only the control, which reproduces the published AUCs; this is "
            "what CI runs, because the full sweep takes minutes"
        ),
    )
    args = parser.parse_args(argv)

    wanted = [tuple(part.split("/")) for part in args.configurations.split(",")]
    for key in wanted:
        if key not in MEASURED:
            print(f"unknown configuration: {key}", file=sys.stderr)
            return 1

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    control: list[dict] = []
    for dataset, channel in wanted:
        values = MEASURED[(dataset, channel)]
        result = _run(
            args.patients,
            values["fold"],
            values["state_fraction"],
            1,
            0.0,
        )
        published = PUBLISHED_AUC.get((dataset, channel))
        entry = {
            "dataset": dataset,
            "channel": channel,
            "recomputed_auc_raw": result["auc_raw"],
            "published_auc": published,
            "matches": (
                published is not None
                and result["auc_raw"] is not None
                and abs(result["auc_raw"] - published) < 1e-9
            ),
        }
        control.append(entry)
        print(
            f"control {dataset}/{channel}: raw AUC {result['auc_raw']:.6f} vs "
            f"published {published} -> {'MATCH' if entry['matches'] else 'MISMATCH'}"
        )
    if not all(entry["matches"] for entry in control):
        print(
            "the control does not reproduce the published AUCs; the sweep would "
            "not be comparable with them",
            file=sys.stderr,
        )
        return 1

    if args.control_only:
        print("control only: the sweep was not run")
        return 0

    # --- the operating point, re-derived with a leukocyte reference set ---
    derivation = _derive_operating_point(args.patients, wanted)
    (outdir / "operating_point.json").write_text(
        json.dumps(derivation, indent=2) + "\n"
    )
    selected = derivation["selected"]
    print(
        "operating point: "
        + (
            f"depth {selected['depth']:,} with {selected['n_leukocyte_reference_loci']} "
            f"reference loci (reference-corrected AUC "
            f"{selected['auc_reference_corrected']:.4f})"
            if selected
            else "no configuration in the search space clears K3"
        )
    )

    reference_loci = (
        selected["n_leukocyte_reference_loci"] if selected else 0
    )

    rows: list[dict] = []
    for dataset, channel in wanted:
        values = MEASURED[(dataset, channel)]
        for multiplier in TUMOUR_SHARE_MULTIPLIERS:
            for fraction in LEUKOCYTE_FRACTIONS:
                for n_reference in (0, reference_loci):
                    result = _run(
                        args.patients,
                        values["fold"],
                        values["state_fraction"],
                        multiplier,
                        fraction,
                        n_reference_loci=n_reference,
                    )
                    rows.append(
                        {
                            "dataset": dataset,
                            "channel": channel,
                            "tumour_share_multiplier": multiplier,
                            "leukocyte_fraction": fraction,
                            "n_leukocyte_reference_loci": n_reference,
                            "n_mrd_positive": result["n_mrd_positive"],
                            "n_relapsers": result["n_relapsers"],
                            "auc_raw": result["auc_raw"],
                            "auc_attributable": result["auc_attributable"],
                            "auc_reference_corrected": result[
                                "auc_reference_corrected"
                            ],
                            "median_tumour_cfDNA_share": result[
                                "median_tumour_cfDNA_share"
                            ],
                            "median_tumour_cfDNA_share_relapsers": result[
                                "median_tumour_cfDNA_share_relapsers"
                            ],
                            "median_tumour_cfDNA_share_non_relapsers": result[
                                "median_tumour_cfDNA_share_non_relapsers"
                            ],
                        }
                    )
                raw = result["auc_raw"]
                att = result["auc_attributable"]
                ref = result["auc_reference_corrected"]
                share = result["median_tumour_cfDNA_share"]
                print(
                    f"{dataset}/{channel} x{multiplier:>5} leuk={fraction:.2f} "
                    f"ref={n_reference:>4} "
                    f"n_mrd={result['n_mrd_positive']:>4}  "
                    f"share={share if share is None else format(share, '.2e')}  "
                    f"raw={raw if raw is None else round(raw, 4)}  "
                    f"attributable={att if att is None else round(att, 4)}  "
                    f"ref_corrected={ref if ref is None else round(ref, 4)}"
                )

    document = {
        "audit": {
            "id": "leukocyte-audit-2026-11",
            "generated_by": "scripts/leukocyte_audit.py",
            "generated_at": datetime.now(UTC).isoformat(),
            "patients_per_arm": args.patients,
            "operating_point": {
                "sequencing_depth": OPERATING_DEPTH,
                "total_loci": OPERATING_LOCI,
                "electrical_fraction": ELECTRICAL_FRACTION,
            },
            "tumour_share_multipliers": list(TUMOUR_SHARE_MULTIPLIERS),
            "leukocyte_fractions": list(LEUKOCYTE_FRACTIONS),
            "note": (
                "The leukocyte compartment is default-off and the golden "
                "fixture is byte-identical with it off. The raw enrichment is "
                "the programme's published statistic; the attributable "
                "enrichment subtracts the leukocyte reads first and is what a "
                "readout that localises the channel transcript to the tumour "
                "would measure."
            ),
        },
        "control": control,
        "sweep": rows,
    }
    (outdir / "leukocyte_audit.json").write_text(
        json.dumps(document, indent=2) + "\n"
    )

    header = [
        "dataset",
        "channel",
        "tumour_share_multiplier",
        "leukocyte_fraction",
        "n_leukocyte_reference_loci",
        "n_mrd_positive",
        "n_relapsers",
        "auc_raw",
        "auc_attributable",
        "auc_reference_corrected",
        "median_tumour_cfDNA_share",
    ]
    lines = ["\t".join(header)]
    for row in rows:
        lines.append(
            "\t".join(
                [
                    row["dataset"],
                    row["channel"],
                    str(row["tumour_share_multiplier"]),
                    f"{row['leukocyte_fraction']:.2f}",
                    str(row["n_leukocyte_reference_loci"]),
                    str(row["n_mrd_positive"]),
                    str(row["n_relapsers"]),
                    "" if row["auc_raw"] is None else f"{row['auc_raw']:.6f}",
                    ""
                    if row["auc_attributable"] is None
                    else f"{row['auc_attributable']:.6f}",
                    ""
                    if row["auc_reference_corrected"] is None
                    else f"{row['auc_reference_corrected']:.6f}",
                    ""
                    if row["median_tumour_cfDNA_share"] is None
                    else f"{row['median_tumour_cfDNA_share']:.3e}",
                ]
            )
        )
    (outdir / "leukocyte_audit.tsv").write_text("\n".join(lines) + "\n")
    print(f"wrote {outdir / 'leukocyte_audit.json'}")
    print(f"wrote {outdir / 'leukocyte_audit.tsv'}")
    print(f"wrote {outdir / 'operating_point.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
