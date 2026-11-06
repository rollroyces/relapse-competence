"""Literature-calibrated constants, with provenance.

Every constant here is anchored to a published value. The source string is
kept next to the number so that a reader can audit the calibration without
leaving the code, and so that :func:`calibration_provenance` can emit a
machine-readable record of what the run was anchored to.

Nothing in this module is a result. It is only the input side.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True)
class Anchor:
    """A literature value with its source."""

    key: str
    value: float
    source: str
    note: str = ""


#: cfDNA concentration, healthy cfDNA (ng/mL). Cristiano 2019; Bettegowda 2014.
CFDNA_CONCENTRATION_HEALTHY: Final = Anchor(
    "cfdna_concentration_healthy",
    5.5,
    "Cristiano 2019 (Nature 570:385); Bettegowda 2014 (Sci Transl Med 6:224ra24)",
    "Median; reported range 3.4-9.5 ng/mL.",
)

#: cfDNA concentration, cancer cfDNA (ng/mL).
CFDNA_CONCENTRATION_CANCER: Final = Anchor(
    "cfdna_concentration_cancer",
    8.2,
    "Cristiano 2019 (Nature 570:385); Bettegowda 2014 (Sci Transl Med 6:224ra24)",
    "Median; reported range 4.5-17.0 ng/mL.",
)

#: Genome equivalents per mL of plasma.
GENOME_EQUIVALENTS_PER_ML: Final = Anchor(
    "genome_equivalents_per_ml",
    300.0,
    "Snyder 2016 (Cell 164:57)",
    "300 +/- 80 per mL.",
)

#: Median ctDNA VAF by stage (fraction).
STAGE_VAF: Final = Anchor(
    "stage_i_median_vaf",
    0.0006,
    "Phallen 2017 (Sci Transl Med 9:eaan2415); Bettegowda 2014 (Sci Transl Med 6:224ra24)",
    "Stage I 0.0006%, II 0.002%, III 0.01%, IV 0.05%.",
)

#: Median ctDNA half-life (minutes).
CTDNA_HALF_LIFE_MIN: Final = Anchor(
    "ctdna_half_life_min",
    30.0,
    "Diehl 2008 (Nat Med 14:985)",
    "Reported range 16-120 minutes.",
)

#: Tumour doubling time (days) for early lung cancer.
TUMOR_DOUBLING_TIME_DAYS: Final = Anchor(
    "tumor_doubling_time_days",
    200.0,
    "Braun 2015 (Lancet 385:1116); range 50-350 days",
)

#: Median tumour-informed MRD lead time before radiographic relapse (days).
MRD_LEAD_TIME_DAYS: Final = Anchor(
    "mrd_lead_time_days",
    104.0,
    "Guardant Reveal post-treatment MRD, as catalogued in the predecessor benchmark registry",
    "The clinical bar this project aims at.",
)

#: Tumour-informed MRD assay sensitivity.
MRD_REFERENCE_SENSITIVITY: Final = Anchor(
    "mrd_sensitivity",
    0.813,
    "Guardant Reveal post-treatment MRD",
)

#: Tumour-informed MRD assay specificity.
MRD_REFERENCE_SPECIFICITY: Final = Anchor(
    "mrd_specificity",
    0.985,
    "Guardant Reveal post-treatment MRD",
)

#: CancerSEEK / Grail stage I sensitivity, for screening-regime context.
STAGE_I_REFERENCE_SENSITIVITY: Final = Anchor(
    "stage_i_sensitivity_grail",
    0.167,
    "Liu 2020 (Ann Oncol 31:745) CCGA sub-study",
)

#: DELFI LUCAS lung-cancer sensitivity.
LUCAS_SENSITIVITY: Final = Anchor(
    "lucas_sensitivity",
    0.82,
    "Mathios 2021 (Nat Commun 12:5060)",
)

#: Prevalence of clonal haematopoiesis in people over 60.
CHIP_PREVALENCE: Final = Anchor(
    "chip_prevalence_over_60",
    0.10,
    "Jaiswal 2014 (NEJM 371:2488)",
)

#: Typical persistent VAF of a CHIP mutation.
CHIP_VAF: Final = Anchor(
    "chip_vaf",
    1e-3,
    "Welch 2012 (NEJM 367:885); Genovese 2014 (NEJM 371:2488)",
    "Persistent 0.1-2% VAF.",
)

#: Genomic coordinates are not modelled; the tumour burden is modelled directly.
TUMOR_VAF_PER_MM3: Final = Anchor(
    "tumor_vaf_per_mm3",
    4.5e-10,
    "Derived: stage I burden ~14,000 mm3 -> 6e-6 VAF (Phallen 2017); stage IV ~1e6 mm3 -> 5e-4 VAF",
    "VAF = tumor_vaf_per_mm3 * tumour_volume_mm3.",
)

ALL_ANCHORS: Final = tuple(
    [
        CFDNA_CONCENTRATION_HEALTHY,
        CFDNA_CONCENTRATION_CANCER,
        GENOME_EQUIVALENTS_PER_ML,
        STAGE_VAF,
        CTDNA_HALF_LIFE_MIN,
        TUMOR_DOUBLING_TIME_DAYS,
        MRD_LEAD_TIME_DAYS,
        MRD_REFERENCE_SENSITIVITY,
        MRD_REFERENCE_SPECIFICITY,
        STAGE_I_REFERENCE_SENSITIVITY,
        LUCAS_SENSITIVITY,
        CHIP_PREVALENCE,
        CHIP_VAF,
        TUMOR_VAF_PER_MM3,
    ]
)


def calibration_provenance() -> dict[str, dict[str, object]]:
    """Return the calibration record for embedding in a results file."""
    return {
        anchor.key: {
            "value": anchor.value,
            "source": anchor.source,
            "note": anchor.note,
        }
        for anchor in ALL_ANCHORS
    }


def reference_benchmarks() -> list[dict[str, object]]:
    """Published benchmarks this project is measured against."""
    return [
        {
            "assay": "Guardant Reveal (MRD)",
            "regime": "post_treatment",
            "sensitivity": MRD_REFERENCE_SENSITIVITY.value,
            "specificity": MRD_REFERENCE_SPECIFICITY.value,
            "median_lead_time_days": MRD_LEAD_TIME_DAYS.value,
            "source": MRD_LEAD_TIME_DAYS.source,
        },
        {
            "assay": "Grail Galleri (CCGA)",
            "regime": "screening",
            "stage_i_sensitivity": STAGE_I_REFERENCE_SENSITIVITY.value,
            "specificity": 0.995,
            "source": STAGE_I_REFERENCE_SENSITIVITY.source,
        },
        {
            "assay": "DELFI LUCAS (lung)",
            "regime": "screening",
            "sensitivity": LUCAS_SENSITIVITY.value,
            "specificity": 0.87,
            "source": LUCAS_SENSITIVITY.source,
        },
    ]
