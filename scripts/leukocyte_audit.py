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


def _config(
    patients: int,
    fold: float,
    state_fraction: float,
    tumour_multiplier: float,
    leukocyte_fraction: float,
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
        sequencing_depth=OPERATING_DEPTH,
        n_loci=OPERATING_LOCI - n_electrical,
        n_electrical_loci=n_electrical,
        tumor_vaf_per_mm3=base.tumor_vaf_per_mm3 * tumour_multiplier,
        leukocyte_channel_fraction=leukocyte_fraction,
    )


def _run(
    patients: int,
    fold: float,
    state_fraction: float,
    tumour_multiplier: int,
    leukocyte_fraction: float,
) -> dict:
    cfg = _config(
        patients, fold, state_fraction, tumour_multiplier, leukocyte_fraction
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
    return {
        "read_threshold": threshold,
        "n_mrd_positive": len(mrd),
        "n_relapsers": sum(1 for o in mrd if o.relapsed),
        "auc_raw": raw,
        "auc_attributable": attributable,
        # The tumour's share of the cfDNA pool, measured from the mutation
        # channel: this is what the electrical channel is read against.
        "median_tumour_cfDNA_share": statistics.median(
            o.mutation_vaf for o in mrd
        ),
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

    rows: list[dict] = []
    for dataset, channel in wanted:
        values = MEASURED[(dataset, channel)]
        for multiplier in TUMOUR_SHARE_MULTIPLIERS:
            for fraction in LEUKOCYTE_FRACTIONS:
                result = _run(
                    args.patients,
                    values["fold"],
                    values["state_fraction"],
                    multiplier,
                    fraction,
                )
                rows.append(
                    {
                        "dataset": dataset,
                        "channel": channel,
                        "tumour_share_multiplier": multiplier,
                        "leukocyte_fraction": fraction,
                        "n_mrd_positive": result["n_mrd_positive"],
                        "n_relapsers": result["n_relapsers"],
                        "auc_raw": result["auc_raw"],
                        "auc_attributable": result["auc_attributable"],
                        "median_tumour_cfDNA_share": result[
                            "median_tumour_cfDNA_share"
                        ],
                    }
                )
                raw = result["auc_raw"]
                att = result["auc_attributable"]
                share = result["median_tumour_cfDNA_share"]
                print(
                    f"{dataset}/{channel} x{multiplier:>5} leuk={fraction:.2f}  "
                    f"n_mrd={result['n_mrd_positive']:>4}  "
                    f"share={share if share is None else format(share, '.2e')}  "
                    f"raw={raw if raw is None else round(raw, 4)}  "
                    f"attributable={att if att is None else round(att, 4)}"
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
        "n_mrd_positive",
        "n_relapsers",
        "auc_raw",
        "auc_attributable",
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
                    str(row["n_mrd_positive"]),
                    str(row["n_relapsers"]),
                    "" if row["auc_raw"] is None else f"{row['auc_raw']:.6f}",
                    ""
                    if row["auc_attributable"] is None
                    else f"{row['auc_attributable']:.6f}",
                    ""
                    if row["median_tumour_cfDNA_share"] is None
                    else f"{row['median_tumour_cfDNA_share']:.3e}",
                ]
            )
        )
    (outdir / "leukocyte_audit.tsv").write_text("\n".join(lines) + "\n")
    print(f"wrote {outdir / 'leukocyte_audit.json'}")
    print(f"wrote {outdir / 'leukocyte_audit.tsv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
