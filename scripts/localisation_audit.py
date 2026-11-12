#!/usr/bin/env python3
"""The localisation audit: can per-molecule attribution rescue the readout?

The leukocyte audit searched the space of *background-subtraction* statistics
and found that none of them clears K3: subtracting the leukocyte reads and
then dividing by the participant's own tumour cfDNA share amplifies the noise
by the inverse of that share, and the two arms of an MRD-positive cohort sit
two orders of magnitude apart in it.

The assay specification's answer is different, and this audit tests it. The
specification says the background must not be subtracted at all: the
tumour-derived molecules must be *counted* directly, using a per-molecule
signature -- a heterozygous germline SNP that the participant's own tumour
shifts. A leukocyte's channel transcript carries the germline allele, not the
tumour's shift of it, so it is never counted. The background is removed by
construction rather than inferred.

That mechanism had never been simulated. The audit adds it, default-off, and
asks four questions:

1. Does the attributed statistic clear K3 in the bulk-plasma regime, where
   the raw one inverts?
2. Is it really the state doing the work, or is it burden? The control here
   is a cohort whose two arms carry the *same* state fraction: any
   discrimination left over is burden, not state.
3. Is the denominator's sequencing-error floor doing the work? The floor
   sits in the denominator of both statistics but only in the numerator of
   the published one, so the attributed statistic is reported both ways.
4. What does it cost? The informative positions are a property of the
   participant, so the audit sweeps the attribution rate and the fraction of
   participants who have one.

    python scripts/localisation_audit.py --patients 800

Outputs
-------
    results/localisation_audit/localisation_audit.json
    results/localisation_audit/localisation_audit.tsv
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

#: The leukocyte compartment's share of the electrical locus's signal. Zero is
#: the model as published; the others are the regime bulk plasma is in.
LEUKOCYTE_FRACTIONS = (0.0, 0.5, 0.9, 0.99)

#: The programme's own thresholds.
K1_THRESHOLD = 0.60
K3_THRESHOLD = 0.65

#: The per-molecule attribution rate: the probability that a tumour-derived
#: channel-transcript molecule carries an informative tumour signature. The
#: assay specification leaves it to the pilot, so it is swept rather than
#: assumed.
ATTRIBUTION_RATES = (0.0, 0.01, 0.05, 0.1, 0.25, 0.5, 1.0)

#: The fraction of participants with at least one informative position. The
#: specification's first stop rule is about this number.
INFORMATIVE_POSITION_RATES = (0.5, 0.7, 0.9, 1.0)

#: The depth axis, for the cost of the attribution.
DEPTHS = (200_000, 2_000_000, 20_000_000)

#: The state fraction both arms carry in the control. It is the simulator's
#: persistent-arm value, so the two arms are matched and any discrimination
#: left over is burden rather than state.
MATCHED_STATE_FRACTION = 0.10


def _config(
    patients: int,
    fold: float,
    state_fraction: float,
    leukocyte_fraction: float,
    attribution_rate: float = 0.0,
    informative_position_rate: float = 1.0,
    informative_positions_mean: float = 1.0,
    depth: int = OPERATING_DEPTH,
    matched_state: bool = False,
    background_vaf_mean: float | None = None,
) -> SimulationConfig:
    base = SimulationConfig(
        regime=Regime.POST_TREATMENT,
        seed=20261106,
        n_patients_per_arm=patients,
    )
    n_electrical = int(round(OPERATING_LOCI * ELECTRICAL_FRACTION))
    overrides = {
        "electrical_fold_change": max(0.0, fold - 1.0),
        "state_fraction_resistant": state_fraction,
        "sequencing_depth": depth,
        "n_loci": OPERATING_LOCI - n_electrical,
        "n_electrical_loci": n_electrical,
        "leukocyte_channel_fraction": leukocyte_fraction,
        "attribution_rate": attribution_rate,
        "informative_position_rate": informative_position_rate,
        "informative_positions_mean": informative_positions_mean,
    }
    if matched_state:
        # Both arms carry the same state fraction, so the only thing left
        # separating them is their burden.
        overrides["state_fraction_persistent"] = state_fraction
    if background_vaf_mean is not None:
        overrides["background_vaf_mean"] = background_vaf_mean
        overrides["background_vaf_sd"] = 0.0
    return replace(base, **overrides)


def _run(
    patients: int,
    fold: float,
    state_fraction: float,
    leukocyte_fraction: float,
    attribution_rate: float = 0.0,
    informative_position_rate: float = 1.0,
    informative_positions_mean: float = 1.0,
    depth: int = OPERATING_DEPTH,
    matched_state: bool = False,
    background_vaf_mean: float | None = None,
) -> dict:
    cfg = _config(
        patients,
        fold,
        state_fraction,
        leukocyte_fraction,
        attribution_rate,
        informative_position_rate,
        informative_positions_mean,
        depth,
        matched_state,
        background_vaf_mean,
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
            "auc_localised": None,
            "auc_localised_corrected": None,
            "applicability": None,
            "median_tumour_cfDNA_share": None,
        }

    def _auc_of(field: str) -> float | None:
        values = [getattr(o, field) for o in mrd]
        if all(v == 0.0 for v in values):
            return None
        return _auc(values, [o.relapsed for o in mrd])

    # The participants the readout applies to: those with an informative
    # position. A participant without one has no attributable read, so the
    # statistic is not defined for them, and counting them as a zero would
    # measure the fraction who are measurable rather than the discrimination.
    applicable = [o for o in mrd if o.has_informative_position]

    def _auc_applicable(field: str) -> float | None:
        if len(applicable) < 2:
            return None
        values = [getattr(o, field) for o in applicable]
        if all(v == 0.0 for v in values):
            return None
        return _auc(values, [o.relapsed for o in applicable])

    return {
        "read_threshold": threshold,
        "n_mrd_positive": len(mrd),
        "n_relapsers": sum(1 for o in mrd if o.relapsed),
        "auc_raw": _auc_of("electrical_enrichment"),
        "auc_localised": _auc_applicable("electrical_enrichment_localised"),
        "auc_localised_corrected": _auc_applicable(
            "electrical_enrichment_localised_corrected"
        ),
        # The fraction of MRD-positive participants the readout applies to.
        "applicability": len(applicable) / len(mrd),
        "n_applicable": len(applicable),
        "median_tumour_cfDNA_share": statistics.median(o.mutation_vaf for o in mrd),
    }


def _control(patients: int, wanted: list[tuple[str, str]]) -> list[dict]:
    """The published AUCs, recomputed with the attribution model off.

    This is the control that the extension did not move the published
    numbers: with the attribution off, the raw statistic is the published
    one, and it has to reproduce the published AUCs exactly.
    """
    control: list[dict] = []
    for dataset, channel in wanted:
        values = MEASURED[(dataset, channel)]
        result = _run(
            patients,
            values["fold"],
            values["state_fraction"],
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
            # With the attribution off, no participant has an informative
            # position, so the attributed statistic is undefined everywhere.
            "auc_localised_with_attribution_off": result["auc_localised"],
        }
        control.append(entry)
        print(
            f"control {dataset}/{channel}: raw AUC {result['auc_raw']:.6f} vs "
            f"published {published} -> {'MATCH' if entry['matches'] else 'MISMATCH'}"
        )
    return control


def _state_control(patients: int, wanted: list[tuple[str, str]]) -> list[dict]:
    """The cohort whose two arms carry the same state fraction.

    Any discrimination left over in this cohort is burden, not state. The
    attributed statistic is reported against this, because the published one
    has a floor-driven residual of its own and the comparison has to be made
    like for like.

    Both arms are set to the same state fraction: the relapsing arm's is
    lowered to the persistent arm's as well, so that the only thing left
    separating the arms is their burden.
    """
    rows: list[dict] = []
    for dataset, channel in wanted:
        values = MEASURED[(dataset, channel)]
        matched = _run(
            patients,
            values["fold"],
            MATCHED_STATE_FRACTION,
            0.99,
            attribution_rate=1.0,
            matched_state=True,
        )
        realistic = _run(
            patients,
            values["fold"],
            values["state_fraction"],
            0.99,
            attribution_rate=1.0,
        )
        rows.append(
            {
                "dataset": dataset,
                "channel": channel,
                "matched_state_fraction": MATCHED_STATE_FRACTION,
                # What the two arms would show if the state were the only
                # thing separating them.
                "auc_raw_realistic": realistic["auc_raw"],
                "auc_localised_realistic": realistic["auc_localised"],
                "auc_localised_corrected_realistic": realistic[
                    "auc_localised_corrected"
                ],
                # What is left when the state is removed: burden alone.
                "auc_raw_matched_state": matched["auc_raw"],
                "auc_localised_matched_state": matched["auc_localised"],
                "auc_localised_corrected_matched_state": matched[
                    "auc_localised_corrected"
                ],
            }
        )
        print(
            f"state control {dataset}/{channel}: "
            f"corrected AUC realistic {realistic['auc_localised_corrected']:.4f} vs "
            f"matched-state {matched['auc_localised_corrected']:.4f}"
        )
    return rows


def _sweep(
    patients: int,
    wanted: list[tuple[str, str]],
    attribution_rate: float,
    informative_position_rate: float,
    depth: int,
) -> list[dict]:
    rows: list[dict] = []
    for dataset, channel in wanted:
        values = MEASURED[(dataset, channel)]
        for leukocyte_fraction in LEUKOCYTE_FRACTIONS:
            result = _run(
                patients,
                values["fold"],
                values["state_fraction"],
                leukocyte_fraction,
                attribution_rate=attribution_rate,
                informative_position_rate=informative_position_rate,
                depth=depth,
            )
            corrected = result["auc_localised_corrected"]
            rows.append(
                {
                    "dataset": dataset,
                    "channel": channel,
                    "leukocyte_fraction": leukocyte_fraction,
                    "attribution_rate": attribution_rate,
                    "informative_position_rate": informative_position_rate,
                    "sequencing_depth": depth,
                    "n_mrd_positive": result["n_mrd_positive"],
                    "n_relapsers": result["n_relapsers"],
                    "n_applicable": result["n_applicable"],
                    "applicability": result["applicability"],
                    "auc_raw": result["auc_raw"],
                    "auc_localised": result["auc_localised"],
                    "auc_localised_corrected": corrected,
                    "median_tumour_cfDNA_share": result[
                        "median_tumour_cfDNA_share"
                    ],
                    "clears_k1": (
                        corrected is not None and corrected > K1_THRESHOLD
                    ),
                    "clears_k3": (
                        corrected is not None and corrected > K3_THRESHOLD
                    ),
                }
            )
            print(
                f"  {dataset}/{channel} leuk={leukocyte_fraction:.2f} "
                f"attr={attribution_rate:.2f} depth={depth:,}: "
                f"raw={result['auc_raw']:.4f} "
                f"localised={_fmt(result['auc_localised'])} "
                f"corrected={_fmt(corrected)}"
            )
    return rows


def _fmt(value: float | None) -> str:
    """A number for printing, or the mark for an undefined statistic.

    The attributed statistic is undefined when no participant in the cohort
    has an informative position, which is the case with the attribution off.
    """
    return "n/a" if value is None else f"{value:.4f}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--patients", type=int, default=800)
    parser.add_argument("--outdir", default="results/localisation_audit")
    parser.add_argument(
        "--configurations",
        default=",".join(f"{d}/{c}" for d, c in MEASURED),
        help="which measured configurations to sweep",
    )
    parser.add_argument(
        "--control-only",
        action="store_true",
        help=(
            "run only the controls, which reproduce the published AUCs and the "
            "matched-state test; this is what CI runs, because the full sweep "
            "takes minutes"
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

    print("== control ==")
    control = _control(args.patients, wanted)
    if not all(entry["matches"] for entry in control):
        print("CONTROL FAILED: the published AUCs were not reproduced", file=sys.stderr)
        return 1

    print("== state control ==")
    state_control = _state_control(args.patients, wanted)

    if args.control_only:
        # The artefact is not written in control-only mode: the committed one
        # holds the full sweep, and CI must not replace it with a control.
        print("control only: the sweep was not run")
        return 0

    sweep: list[dict] = []
    cost: list[dict] = []

    print("== sweep: the attribution rate ==")
    for attribution_rate in ATTRIBUTION_RATES:
        if attribution_rate == 0.0:
            # The attribution off: the same cohort as the published model,
            # so the comparison is like for like.
            sweep += _sweep(
                args.patients,
                wanted,
                0.0,
                1.0,
                OPERATING_DEPTH,
            )
            continue
        sweep += _sweep(
            args.patients,
            wanted,
            attribution_rate,
            1.0,
            OPERATING_DEPTH,
        )

    print("== sweep: the fraction of participants with an informative position ==")
    for informative_position_rate in INFORMATIVE_POSITION_RATES:
        if informative_position_rate == 1.0:
            continue
        sweep += _sweep(
            args.patients,
            wanted,
            1.0,
            informative_position_rate,
            OPERATING_DEPTH,
        )

    print("== cost: depth against the attribution rate ==")
    for depth in DEPTHS:
        if depth == OPERATING_DEPTH:
            continue
        for attribution_rate in ATTRIBUTION_RATES:
            if attribution_rate == 0.0:
                continue
            cost += _sweep(
                args.patients,
                wanted,
                attribution_rate,
                1.0,
                depth,
            )

    payload = {
        "audit": {
            "id": "localisation-audit-2026-11",
            "generated_by": "scripts/localisation_audit.py",
            "generated_at": datetime.now(UTC).isoformat(),
            "git_commit": _git_commit(),
            "source_document": "docs/PLASMA-ASSAY-SPECIFICATION.md",
            "patients_per_arm": args.patients,
            "operating_point": {
                "sequencing_depth": OPERATING_DEPTH,
                "total_loci": OPERATING_LOCI,
                "electrical_fraction": ELECTRICAL_FRACTION,
            },
            "leukocyte_fractions": list(LEUKOCYTE_FRACTIONS),
            "attribution_rates": list(ATTRIBUTION_RATES),
            "informative_position_rates": list(INFORMATIVE_POSITION_RATES),
            "depths": list(DEPTHS),
            "k1_threshold": K1_THRESHOLD,
            "k3_threshold": K3_THRESHOLD,
            "note": (
                "The attribution model is default-off and the golden fixture "
                "is byte-identical with it off. The attributed statistic "
                "counts the channel-transcript reads carrying an informative "
                "tumour signature, so the leukocyte compartment does not "
                "enter it. It is reported with the mutation channel's raw "
                "per-locus VAF as the denominator and with the "
                "sequencing-error floor removed from it, which is the "
                "participant's estimated tumour cfDNA fraction."
            ),
        },
        "control": control,
        "state_control": state_control,
        "sweep": sweep,
        "cost": cost,
    }

    (outdir / "localisation_audit.json").write_text(
        json.dumps(payload, indent=1) + "\n", encoding="utf-8"
    )
    _write_tsv(outdir / "localisation_audit.tsv", sweep + cost)

    print()
    print(f"wrote {outdir / 'localisation_audit.json'}")
    print(f"wrote {outdir / 'localisation_audit.tsv'}")
    return 0


def _git_commit() -> str:
    import subprocess

    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=REPO,
            capture_output=True,
            text=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return "unknown"
    return out.stdout.strip()


def _write_tsv(path: Path, rows: list[dict]) -> None:
    header = [
        "dataset",
        "channel",
        "leukocyte_fraction",
        "attribution_rate",
        "informative_position_rate",
        "sequencing_depth",
        "n_mrd_positive",
        "n_relapsers",
        "n_applicable",
        "applicability",
        "auc_raw",
        "auc_localised",
        "auc_localised_corrected",
        "clears_k1",
        "clears_k3",
    ]
    lines = ["\t".join(header)]
    for row in rows:
        values = []
        for key in header:
            value = row.get(key, "")
            if value is None:
                values.append("")
            elif isinstance(value, float):
                values.append(f"{value:.6f}")
            else:
                values.append(str(value))
        lines.append("\t".join(values))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
