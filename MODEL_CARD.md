# Model card — relapse-competence v0.1.0

## Intended use

Research and education. Provides a transparent, executable model of
longitudinal cfDNA detection for post-treatment MRD and for screening, so
that assay design choices (sequencing depth, panel size, sampling interval,
detection threshold) can be reasoned about quantitatively before any sample
is drawn.

**Not intended for:** clinical decision-making, patient stratification, any
regulatory or diagnostic use, or any claim about the performance of a specific
commercial assay.

## Model type

A mechanistic generative model of cfDNA detection, not a predictor fitted to
data.

- **Ground truth:** exponential tumour growth, a therapy-surviving residual
  clone, and a radiographic-relapse threshold.
- **Observation:** Poisson sampling of mutant reads at tracked loci, plus an
  assay background floor.
- **Detection:** a read-count threshold (MRD) or a CUSUM over excess reads
  (screening), with thresholds calibrated on a held-out split.

There is no training data. The model has no fitted parameters beyond the
literature-calibrated constants listed below.

## Calibration sources

Every constant carries its source in `src/relapse_competence/calibration.py`
and is emitted into each results file under `calibration`.

| Quantity | Value | Source |
|---|---|---|
| cfDNA concentration | 5.5 (healthy) / 8.2 (cancer) ng/mL | Cristiano 2019; Bettegowda 2014 |
| Genome equivalents | 300 ± 80 /mL | Snyder 2016 |
| Stage I median ctDNA VAF | 0.0006% | Phallen 2017; Bettegowda 2014 |
| ctDNA half-life | 16–120 min (median 30) | Diehl 2008 |
| Tumour doubling time | 200 days median | Braun 2015 |
| CHIP prevalence (>60) | 10% | Jaiswal 2014 |
| CHIP VAF | 0.1–2% | Welch 2012; Genovese 2014 |
| MRD reference | 81.3% sens / 98.5% spec / 104 d lead | Guardant Reveal, as catalogued in the reference registry |
| Stage I reference (screening) | 16.7% sens / 99.5% spec | Liu 2020 CCGA |
| Lung-specific screening reference | 82% sens / 87% spec | Mathios 2021 (DELFI LUCAS) |

## Performance

See the README for the full table. Headline: at 50,000× depth on a 50-locus
panel, simulated post-treatment MRD reaches 51.5% sensitivity at 98.5%
specificity with a 41-day median lead time; reaching the 104-day published
bar requires roughly 200,000× depth on a 200-locus panel.

**These are simulation outputs under stated parameters. They are not
measurements of any assay.**

## Evaluation protocol

1. Thresholds are selected on even-indexed controls only.
2. Evaluation uses odd-indexed controls plus all case patients.
3. The threshold rule is fixed in advance: the smallest threshold meeting the
   target specificity.
4. A detection at or after radiographic relapse counts as a false negative for
   sensitivity and is reported separately as `n_flagged_late`.
5. Lead time is continuous: `T · log2(V_relapse / V_flag)`.

## Known limitations

- **Simulated, not measured.** No clinical sample has been processed.
- **Single-compartment tumour biology.** One tumour, one residual clone, one
  doubling time. Real resistant disease is heterogeneous, with multiple clones
  of differing fitness and shedding.
- **Uniform shedding.** ctDNA shedding is modelled as a per-patient
  multiplicative factor with log-normal spread, not as a function of tumour
  site, size, or histology. Lung, bone and liver metastases shed very
  differently, and this is not captured.
- **The background floor is a single scalar.** Real error floors vary by
  locus, by batch, and by whether the site is a known germline variant.
- **Chip is either fully filtered or fully present.** Real CHIP management is
  per-patient and per-locus.
- **No assay-specific bias.** Extraction efficiency, index hopping, and
  capture efficiency are not modelled.
- **The growth model is exponential with a constant doubling time.** Real
  growth is Gompertzian, and doubling time shortens with burden.

## Ethical and safety notes

This package handles no patient data. It contains no identifiers, no clinical
records, and no protected health information. It does not fetch data from any
external service.

## Maintenance

Alpha status. Version 0.1.0. See `docs/ROADMAP.md` for open dependencies and
planned work.

## Citation

See `CITATION.cff`.
