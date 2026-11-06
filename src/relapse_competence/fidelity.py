"""Model fidelity and split-model validation.

Two questions this module answers, both of which the research plan lists as
open:

**1. How much do the published numbers move when the simulator is made more
realistic?** The risk register calls the modelling assumptions *certain to be
partly wrong*. Each variant here turns on one fidelity extension -- multi-clone
resistance, Gompertzian growth, site-dependent shedding, per-locus background
variation -- and the headline MRD numbers are recomputed against the published
model.

**2. How much performance is lost to the modelling gap?** A detector is fitted
on data from the published model and applied, *without refitting*, to data
from the fidelity model. The difference between that and a detector refitted on
the fidelity model is the part of the performance the published model was
hiding. This is the standard way to bound the value of a simulation-based
design, and it is the only honest way to quote a simulated number.

The fidelity extensions are default-off in :class:`SimulationConfig`; this
module turns them on explicitly, variant by variant, and never changes the
published configuration.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass, replace
from typing import Any

from .benchmark import PatientOutcome, collect_outcomes, run_depth_sweep
from .config import PatientArm, SimulationConfig

__all__ = [
    "ModelVariant",
    "MODEL_VARIANTS",
    "FIDELITY_VARIANT",
    "run_fidelity_comparison",
    "run_split_model_validation",
]


@dataclass(frozen=True)
class ModelVariant:
    """One named set of fidelity settings."""

    name: str
    description: str
    overrides: dict[str, Any]


#: The published model, and one variant per fidelity extension.
MODEL_VARIANTS: tuple[ModelVariant, ...] = (
    ModelVariant(
        name="published",
        description=(
            "The published model: one resistant clone, exponential growth, "
            "uniform shedding, a single background floor."
        ),
        overrides={},
    ),
    ModelVariant(
        name="multi_clone",
        description=(
            "Three resistant clones with different fitness and different "
            "shedding, splitting the residual burden unevenly."
        ),
        overrides={
            "n_clones": 3,
            "clone_residual_fraction_sd": 0.6,
            "clone_doubling_time_cv": 0.35,
            "clone_shedding_sd": 0.5,
        },
    ),
    ModelVariant(
        name="gompertzian",
        description=(
            "Gompertzian growth, calibrated so the initial doubling time is "
            "unchanged and growth decelerates towards the carrying capacity."
        ),
        overrides={"growth_model": "gompertz"},
    ),
    ModelVariant(
        name="site_dependent_shedding",
        description=(
            "Each patient relapses at a drawn metastatic site, with that "
            "site's own ctDNA shedding multiplier."
        ),
        overrides={"site_shedding_enabled": True},
    ),
    ModelVariant(
        name="per_locus_background",
        description=(
            "The background floor varies across tracked loci, so the mutant "
            "read count is over-dispersed relative to a single Poisson."
        ),
        overrides={"per_locus_background_log_sd": 1.0},
    ),
    ModelVariant(
        name="combined",
        description="All four extensions at once.",
        overrides={
            "n_clones": 3,
            "clone_residual_fraction_sd": 0.6,
            "clone_doubling_time_cv": 0.35,
            "clone_shedding_sd": 0.5,
            "growth_model": "gompertz",
            "site_shedding_enabled": True,
            "per_locus_background_log_sd": 1.0,
        },
    ),
)

#: The variant used as the "test" model in the split-model validation.
FIDELITY_VARIANT = MODEL_VARIANTS[-1]


def _variant_config(base: SimulationConfig, variant: ModelVariant) -> SimulationConfig:
    return replace(base, **variant.overrides)


def _depth_requirement(
    results: list, min_sensitivity: float = 0.8
) -> dict[str, object] | None:
    """The cheapest configuration that reaches ``min_sensitivity``.

    "Cheapest" is total reads per draw (``depth * loci``), which is the cost
    driver of the assay.
    """
    qualifying = [
        r for r in results if r.target_reached and r.sensitivity >= min_sensitivity
    ]
    if not qualifying:
        return None
    best = min(qualifying, key=lambda r: r.total_reads_per_draw)
    return {
        "sequencing_depth": best.sequencing_depth,
        "n_loci": best.n_loci,
        "total_reads_per_draw": best.total_reads_per_draw,
        "sensitivity": best.sensitivity,
        "specificity": best.specificity,
        "median_lead_time_days": best.median_lead_time_days,
    }


def run_fidelity_comparison(
    base_config: SimulationConfig,
    depths: tuple[int, ...] = (5_000, 50_000, 200_000, 500_000),
    locus_counts: tuple[int, ...] = (50, 200),
    target_specificity: float = 0.98,
    min_sensitivity: float = 0.8,
) -> dict[str, object]:
    """Recompute the headline MRD numbers under every fidelity variant."""
    published: dict[str, object] | None = None
    variants: list[dict[str, object]] = []

    for variant in MODEL_VARIANTS:
        config = _variant_config(base_config, variant)
        sweep = run_depth_sweep(
            config,
            depths=depths,
            locus_counts=locus_counts,
            target_specificity=target_specificity,
        )
        requirement = _depth_requirement(sweep, min_sensitivity)
        conventional = next(
            (r for r in sweep if r.sequencing_depth == 50_000 and r.n_loci == 50),
            None,
        )
        recommended = next(
            (r for r in sweep if r.sequencing_depth == 200_000 and r.n_loci == 200),
            None,
        )
        record: dict[str, object] = {
            "variant": variant.name,
            "description": variant.description,
            "overrides": variant.overrides,
            "depth_requirement_at_sensitivity": requirement,
            "configurations": [r.as_dict() for r in sweep],
        }
        if conventional is not None:
            record["conventional_50k_50"] = {
                "sensitivity": conventional.sensitivity,
                "specificity": conventional.specificity,
                "ppv": conventional.ppv,
                "median_lead_time_days": conventional.median_lead_time_days,
                "median_lead_time_among_all_resistant_days": (
                    conventional.median_lead_time_among_all_resistant_days
                ),
                "read_threshold": conventional.read_threshold,
                "target_reached": conventional.target_reached,
            }
        if recommended is not None:
            record["recommended_200k_200"] = {
                "sensitivity": recommended.sensitivity,
                "specificity": recommended.specificity,
                "ppv": recommended.ppv,
                "median_lead_time_days": recommended.median_lead_time_days,
                "median_lead_time_among_all_resistant_days": (
                    recommended.median_lead_time_among_all_resistant_days
                ),
                "read_threshold": recommended.read_threshold,
                "target_reached": recommended.target_reached,
            }
        variants.append(record)
        if variant.name == "published":
            published = record

    def _delta(record: dict[str, object], key: str, field: str) -> float | None:
        block = record.get(key)
        base_block = (published or {}).get(key)
        if not isinstance(block, dict) or not isinstance(base_block, dict):
            return None
        reference_value = base_block.get(field)
        value = block.get(field)
        if not isinstance(reference_value, int | float) or not isinstance(value, int | float):
            return None
        return float(value) - float(reference_value)

    for record in variants:
        record["delta_vs_published"] = {
            "sensitivity_200k_200": _delta(record, "recommended_200k_200", "sensitivity"),
            "specificity_200k_200": _delta(record, "recommended_200k_200", "specificity"),
            "median_lead_time_days_200k_200": _delta(
                record, "recommended_200k_200", "median_lead_time_days"
            ),
            "median_lead_time_days_50k_50": _delta(
                record, "conventional_50k_50", "median_lead_time_days"
            ),
        }

    return {
        "base_config": base_config,
        "min_sensitivity_for_depth_requirement": min_sensitivity,
        "variants": variants,
    }


# ----------------------------------------------------------------------
# split-model validation
# ----------------------------------------------------------------------
def _mrd_metrics(outcomes: list[PatientOutcome]) -> dict[str, object]:
    """The MRD metrics, with the same definitions the allocation sweep uses."""
    evaluation = [o for o in outcomes if o.split == "evaluation"]
    relapsers = [o for o in evaluation if o.relapsed]
    non_relapsed = [o for o in evaluation if not o.relapsed]
    mrd_positive = [o for o in evaluation if o.mrd_flagged]

    def _specificity_for(arm_name: str) -> float:
        subset = [o for o in non_relapsed if o.arm.value == arm_name]
        if not subset:
            return float("nan")
        return sum(1 for o in subset if not o.mrd_flagged) / len(subset)

    leads = [o.lead_days for o in relapsers if o.lead_days is not None]
    return {
        "n_evaluation": len(evaluation),
        "n_relapsed": len(relapsers),
        "mrd_sensitivity": (
            sum(1 for o in relapsers if o.mrd_flagged) / len(relapsers)
            if relapsers
            else 0.0
        ),
        "mrd_specificity_vs_responders": _specificity_for("responder"),
        "mrd_specificity_vs_persistent": _specificity_for("persistent"),
        "persistent_share_of_mrd_positive": (
            sum(1 for o in mrd_positive if o.arm is PatientArm.PERSISTENT) / len(mrd_positive)
            if mrd_positive
            else float("nan")
        ),
        "n_mrd_positive": len(mrd_positive),
        "ppv_within_mrd_positive": (
            sum(1 for o in mrd_positive if o.relapsed) / len(mrd_positive)
            if mrd_positive
            else float("nan")
        ),
        "median_lead_time_days": statistics.median(leads) if leads else None,
        "auc_electrical_raw_within_mrd_positive": _auc(
            [o.electrical_raw for o in mrd_positive], [o.relapsed for o in mrd_positive]
        ),
        "auc_electrical_enrichment_within_mrd_positive": _auc(
            [o.electrical_enrichment for o in mrd_positive],
            [o.relapsed for o in mrd_positive],
        ),
    }


def _auc(scores: list[float], labels: list[bool]) -> float:
    """Tie-corrected Mann-Whitney AUC, with the same definition as the sweep."""
    positives = sum(1 for label in labels if label)
    negatives = len(labels) - positives
    if positives == 0 or negatives == 0:
        return float("nan")
    order = sorted(range(len(scores)), key=lambda i: scores[i])
    ranks = [0.0] * len(scores)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and scores[order[j + 1]] == scores[order[i]]:
            j += 1
        average = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[order[k]] = average
        i = j + 1
    rank_sum = sum(rank for rank, label in zip(ranks, labels, strict=False) if label)
    u = rank_sum - positives * (positives + 1) / 2.0
    return u / (positives * negatives)


def run_split_model_validation(
    base_config: SimulationConfig,
    target_specificity: float = 0.98,
    variants: tuple[ModelVariant, ...] | None = None,
) -> dict[str, object]:
    """Fit the detector on the published model, apply it to the fidelity models.

    For every variant:

    * **published** -- the detector fitted on the published model, applied to
      the published model. This is the headline number.
    * **transfer** -- the same detector, fitted on the published model, applied
      *without refitting* to the variant's model. This is what a design
      decision taken on the published model would actually deliver.
    * **refit** -- a detector refitted on the variant's model. This is what that
      model supports, and the gap between *refit* and *transfer* is the price
      of holding the published detector fixed.

    Running every variant, rather than only the combined one, is what makes
    the failure attributable: the read threshold does not transfer for some
    extensions and not for others, and the reader can see which.
    """
    published_config = _variant_config(base_config, MODEL_VARIANTS[0])
    published_outcomes, k_published = collect_outcomes(
        published_config, target_specificity=target_specificity
    )
    published_metrics = _mrd_metrics(published_outcomes)

    evaluations: list[dict[str, object]] = []
    for variant in variants or (FIDELITY_VARIANT,):
        variant_config = _variant_config(base_config, variant)
        transfer_outcomes, _ = collect_outcomes(
            variant_config, target_specificity=target_specificity, read_threshold=k_published
        )
        refit_outcomes, k_refit = collect_outcomes(
            variant_config, target_specificity=target_specificity
        )
        transfer_metrics = _mrd_metrics(transfer_outcomes)
        refit_metrics = _mrd_metrics(refit_outcomes)

        evaluations.append(
            {
                "variant": variant.name,
                "description": variant.description,
                "read_threshold_published": k_published,
                "read_threshold_refit": k_refit,
                "published_model_published_detector": published_metrics,
                "variant_model_published_detector": transfer_metrics,
                "variant_model_refitted_detector": refit_metrics,
                "cost_of_not_recalibrating": {
                    "mrd_sensitivity": _delta_between(
                        transfer_metrics, refit_metrics, "mrd_sensitivity"
                    ),
                    "mrd_specificity_vs_responders": _delta_between(
                        transfer_metrics, refit_metrics, "mrd_specificity_vs_responders"
                    ),
                    "mrd_specificity_vs_persistent": _delta_between(
                        transfer_metrics, refit_metrics, "mrd_specificity_vs_persistent"
                    ),
                    "median_lead_time_days": _delta_between(
                        transfer_metrics, refit_metrics, "median_lead_time_days"
                    ),
                    "ppv_within_mrd_positive": _delta_between(
                        transfer_metrics, refit_metrics, "ppv_within_mrd_positive"
                    ),
                },
                "model_gap_with_detector_held_fixed": {
                    "mrd_sensitivity": _delta_between(
                        published_metrics, transfer_metrics, "mrd_sensitivity"
                    ),
                    "mrd_specificity_vs_responders": _delta_between(
                        published_metrics, transfer_metrics, "mrd_specificity_vs_responders"
                    ),
                    "mrd_specificity_vs_persistent": _delta_between(
                        published_metrics, transfer_metrics, "mrd_specificity_vs_persistent"
                    ),
                    "median_lead_time_days": _delta_between(
                        published_metrics, transfer_metrics, "median_lead_time_days"
                    ),
                },
            }
        )

    return {
        "task": (
            "the MRD detector: flag residual disease before radiographic "
            "relapse, and separate the MRD-positive stratum into relapsers "
            "and persistent non-relapsers"
        ),
        "train_model": MODEL_VARIANTS[0].name,
        "published_model_published_detector": published_metrics,
        "evaluations": evaluations,
        "note": (
            "Three evaluations per variant. 'published' is the headline: the "
            "detector fitted on the published model, applied to the published "
            "model. 'transfer' applies that same detector, without refitting, "
            "to the variant's model -- the model gap with the detector held "
            "fixed. 'refit' recalibrates the threshold on the variant's model, "
            "so the difference between refit and transfer is what holding the "
            "published detector costs. The two differences answer different "
            "questions and are reported separately for that reason."
        ),
    }


def _delta_between(
    left: dict[str, object], right: dict[str, object], field: str
) -> float | None:
    a = left.get(field)
    b = right.get(field)
    if not isinstance(a, int | float) or not isinstance(b, int | float):
        return None
    return float(b) - float(a)


def summarise(variants: list[dict[str, object]]) -> str:
    """A one-line-per-variant summary, for the console."""
    lines = []
    for record in variants:
        requirement = record.get("depth_requirement_at_sensitivity")
        recommended = record.get("recommended_200k_200") or {}
        lines.append(
            "{name:<26} sens@200k/200={sens:<8} spec={spec:<8} lead={lead:<9} depth_req={req}".format(
                name=str(record.get("variant")),
                sens=_round(recommended.get("sensitivity")),
                spec=_round(recommended.get("specificity")),
                lead=_round(recommended.get("median_lead_time_days")),
                req=(
                    f"{requirement['sequencing_depth']}x{requirement['n_loci']}"
                    if requirement
                    else "none"
                ),
            )
        )
    return "\n".join(lines)


def _round(value: object) -> str:
    if not isinstance(value, int | float):
        return "n/a"
    return f"{value:.3f}"
