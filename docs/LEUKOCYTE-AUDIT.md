# The leukocyte audit: what a bulk plasma channel can actually read

**Audit ID:** `leukocyte-audit-2026-11`
**Date of run:** 2026-11-09
**Reproduce:** `python scripts/per_library_folds.py` is not needed for this
one; `python scripts/leukocyte_audit.py --patients 800`
**Artefacts:** `results/leukocyte_audit/leukocyte_audit.json`,
`results/leukocyte_audit/leukocyte_audit.tsv`

---

## 1. What this document is

The gate review's plasma numbers come from a model whose plasma cfDNA pool has
no leukocyte compartment: it is tumour-shed material plus a 1e-6
sequencing-error floor, so the electrical channel's signal is the tumour's
contribution alone.

In bulk plasma that is not the case. Most cfDNA is leukocyte-derived, and KCa3.1
is expressed in immune cells, so the channel locus carries a large leukocyte
background and the tumour's state is a small perturbation on it. The
per-patient audit established that the tumour's state fraction is the decisive
quantity for the readout, so what the plasma channel can resolve about the
state is the question this document answers.

The compartment was added default-off. With it off, the golden fixture is
**byte-identical** to the committed one -- 238,602 bytes, an exact match -- and
the audit's control reproduces the gate review's published operating-point AUCs
to the last digit: 0.992862 for
NSCLC/KCNN4, 0.706545 for SCLC/KCNN4
and 0.694505 for SCLC/PIEZO1.

The per-patient audit ([`PER-PATIENT-AUDIT.md`](PER-PATIENT-AUDIT.md)) is what
made the question necessary: it showed that the tumour's state fraction, and
how it varies between patients, is what decides whether the readout works, and
the plasma numbers are a projection of exactly that quantity.

## 2. The measurement that motivates it

Every number below is read from the committed state-expression artefacts.
State cells, neighbouring tumour cells and immune cells, in counts per 10,000
after normalisation, with the state fraction `f` among malignant cells.

| Configuration | State cells | Other tumour | Immune | f | State / immune | State's share at 1% tumour DNA | at 3% | at 10% | at 30% |
|---|---|---|---|---|---|---|---|---|---|
| NSCLC / KCNN4 | 0.5192 | 0.1404 | 0.2165 | 0.392 | 2.40 | 0.68% | 2.04% | 6.63% | 18.69% |
| SCLC / KCNN4 | 0.1935 | 0.0758 | 0.0787 | 0.104 | 2.46 | 0.16% | 0.46% | 1.54% | 4.51% |
| SCLC / PIEZO1 | 0.2591 | 0.0770 | 0.1386 | 0.104 | 1.87 | 0.14% | 0.41% | 1.41% | 4.52% |

The last four columns are the share of a bulk plasma channel measurement that
the state-bearing fraction contributes, if the plasma cfDNA pool is a fraction
tumour DNA and the rest leukocyte. At the tumour fractions a real MRD cohort
sits at, the state is a **two per cent** perturbation of a bulk KCa3.1
measurement in EGFR-mutant NSCLC, and half a per cent in relapsed SCLC. The
SCLC/Piezo1 row is the worse case: the tumour's *average* Piezo1 level there,
0.0960, is below the leukocyte level of 0.1386, so a bulk plasma Piezo1
measurement in that disease reads leukocyte rather than tumour.

## 3. The mechanism, in one paragraph

The programme's statistic is the electrical channel's per-locus signal divided
by the mutation channel's. The mutation channel is tumour-specific. The
electrical channel, once a leukocyte compartment exists, is the mixture of both
compartments. The ratio therefore carries the leukocyte contribution divided by
the tumour's own cfDNA share -- and that term is *inversely* related to tumour
burden. Relapsers carry more tumour, so the raw ratio is systematically lower
in relapsers: the statistic does not degrade, it inverts.

## 4. The sweep

Each row is the operating point (200,000x, 200 loci, 25% of the read budget on
the electrical channel) at a different tumour cfDNA yield and a different
leukocyte background. "Tumour share" is measured, not nominal: it is the
median of the mutation channel's per-locus VAF over the MRD-positive
population, so it is what the electrical channel is actually read against.

| Tumour yield x | Leukocyte background | Measured tumour share | MRD-positive | Raw AUC | Attributable AUC |
|---|---|---|---|---|---|
| 1 | 0.00 | 8.08e-05 | 508 | 0.9929 | 0.9929 |
| 1 | 0.50 | 4.59e-05 | 538 | 0.0053 | 0.5111 |
| 1 | 0.90 | 4.59e-05 | 538 | 0.0053 | 0.5034 |
| 1 | 0.99 | 6.55e-05 | 545 | 0.0057 | 0.5168 |
| 3 | 0.00 | 7.27e-05 | 663 | 0.9816 | 0.9816 |
| 3 | 0.50 | 6.13e-05 | 675 | 0.0019 | 0.4870 |
| 3 | 0.90 | 5.27e-05 | 675 | 0.0019 | 0.4845 |
| 3 | 0.99 | 5.58e-05 | 676 | 0.0025 | 0.4856 |
| 10 | 0.00 | 6.76e-05 | 734 | 0.9698 | 0.9698 |
| 10 | 0.50 | 4.79e-05 | 744 | 0.0023 | 0.5390 |
| 10 | 0.90 | 4.79e-05 | 744 | 0.0023 | 0.5357 |
| 10 | 0.99 | 3.91e-05 | 744 | 0.0038 | 0.5316 |
| 30 | 0.00 | 1.11e-04 | 756 | 0.9684 | 0.9684 |
| 30 | 0.50 | 5.71e-05 | 769 | 0.0022 | 0.5323 |
| 30 | 0.90 | 5.67e-05 | 769 | 0.0026 | 0.5146 |
| 30 | 0.99 | 5.67e-05 | 769 | 0.0029 | 0.4963 |
| 100 | 0.00 | 3.59e-04 | 766 | 0.9472 | 0.9472 |
| 100 | 0.50 | 2.55e-04 | 773 | 0.0024 | 0.5659 |
| 100 | 0.90 | 2.50e-04 | 774 | 0.0024 | 0.4998 |
| 100 | 0.99 | 2.17e-04 | 774 | 0.0023 | 0.4365 |
| 300 | 0.00 | 8.38e-04 | 787 | 0.7984 | 0.7984 |
| 300 | 0.50 | 5.85e-04 | 793 | 0.0027 | 0.5914 |
| 300 | 0.90 | 5.75e-04 | 794 | 0.0027 | 0.5121 |
| 300 | 0.99 | 5.64e-04 | 793 | 0.0025 | 0.4352 |
| 1000 | 0.00 | 1.94e-03 | 800 | 0.5425 | 0.5425 |
| 1000 | 0.50 | 1.62e-03 | 800 | 0.0013 | 0.4964 |
| 1000 | 0.90 | 1.54e-03 | 800 | 0.0017 | 0.4308 |
| 1000 | 0.99 | 1.26e-03 | 802 | 0.0025 | 0.3632 |
| 3000 | 0.00 | 5.37e-03 | 805 | 0.4482 | 0.4482 |
| 3000 | 0.50 | 4.81e-03 | 803 | 0.0026 | 0.4553 |
| 3000 | 0.90 | 4.81e-03 | 803 | 0.0025 | 0.3856 |
| 3000 | 0.99 | 4.40e-03 | 803 | 0.0046 | 0.3032 |
| 10000 | 0.00 | 2.04e-02 | 805 | 0.3918 | 0.3918 |
| 10000 | 0.50 | 1.45e-02 | 806 | 0.0034 | 0.3790 |
| 10000 | 0.90 | 1.52e-02 | 806 | 0.0033 | 0.3045 |
| 10000 | 0.99 | 1.41e-02 | 806 | 0.0032 | 0.2195 |

The two AUC columns are the raw statistic the programme publishes, and the
tumour-attributable statistic, which subtracts the leukocyte reads first and is
what a readout that localises the channel transcript to the tumour would
measure.

## 5. At the published operating point

| Configuration | Leukocyte background | Measured tumour share | MRD-positive | Raw AUC | Attributable AUC |
|---|---|---|---|---|---|
| NSCLC / KCNN4 | 0.00 | 8.08e-05 | 508 | 0.9929 | 0.9929 |
| NSCLC / KCNN4 | 0.50 | 4.59e-05 | 538 | 0.0053 | 0.5111 |
| NSCLC / KCNN4 | 0.90 | 4.59e-05 | 538 | 0.0053 | 0.5034 |
| NSCLC / KCNN4 | 0.99 | 6.55e-05 | 545 | 0.0057 | 0.5168 |
| SCLC / KCNN4 | 0.00 | 6.07e-05 | 518 | 0.7065 | 0.7065 |
| SCLC / KCNN4 | 0.50 | 4.59e-05 | 538 | 0.0053 | 0.4923 |
| SCLC / KCNN4 | 0.90 | 4.59e-05 | 538 | 0.0053 | 0.4878 |
| SCLC / KCNN4 | 0.99 | 6.55e-05 | 545 | 0.0057 | 0.5060 |
| SCLC / PIEZO1 | 0.00 | 1.09e-04 | 495 | 0.6945 | 0.6945 |
| SCLC / PIEZO1 | 0.50 | 4.59e-05 | 538 | 0.0053 | 0.4948 |
| SCLC / PIEZO1 | 0.90 | 4.59e-05 | 538 | 0.0053 | 0.4896 |
| SCLC / PIEZO1 | 0.99 | 6.55e-05 | 545 | 0.0057 | 0.5070 |

## 6. What this means

- **The published statistic does not survive.** At the published operating point
  the raw enrichment AUC for the surviving NSCLC readout falls from 0.9929 to
  0.0053 with a leukocyte background of 0.50. It is not degraded, it is
  inverted, for the reason in section 3.
- **Correcting for the leukocyte compartment does not rescue it either.** The
  attributable AUC is 0.5111 at the same operating point -- chance. At the
  measured tumour share of 8.08e-05 the tumour's contribution to the channel
  locus is about 1,700 reads out of ten million, against a counting noise of
  about 3,200 on the difference of two Poisson counts of five million each.
- **More tumour DNA does not fix it.** Raising the tumour's cfDNA yield
  changes the MRD-positive population as well as the channel's signal, and the
  two effects do not point the same way: with no leukocyte compartment the AUC
  falls from 0.9929 to 0.3918 across the sweep as the mutation channel's
  operating point moves, and with a leukocyte compartment the attributable AUC
  never rises above 0.59 anywhere in the sweep.
- **So the readout as modelled is a tumour-purified measurement, and plasma is
  not tumour-purified.** The programme's plasma numbers describe an assay that
  localises the channel transcript to the tumour -- by co-occurrence with a
  tumour-specific variant on the same molecule -- or that reads it after a
  leukocyte correction precise to about one part in a thousand. Neither is in
  the model, and neither is in the proposal.
- **This is a design requirement, not a refutation.** It says what the assay
  has to do, and it is cheap to state: one reference locus per leukocyte-
  expressed gene, and the tumour fraction from the somatic variants already
  being read.

## 7. Limitations

- The leukocyte compartment is a single parameter: the share of the electrical
  locus's signal that is leukocyte-derived. It does not model the cfDNA
  transcript pool's composition, so it is a bounding device rather than a
  measurement.
- The sweep's x-axis moves the mutation channel as well as the electrical one,
  because both read the same tumour cfDNA. That is why the no-leukocyte curve
  is not flat, and why the sweep cannot be read as a pure dose-response.
- The measured expression levels are from single-cell RNA-seq after
  per-sample normalisation to counts per 10,000; a cfDNA transcript assay has a
  different composition, and the leucocyte share in a real plasma library is
  not measured here.
- Nothing in this audit uses a real plasma sample.

## 8. Reproducing

```bash
python scripts/leukocyte_audit.py --patients 800            # the full sweep
python scripts/leukocyte_audit.py --patients 800 --control-only  # what CI runs
```

CI runs the control, which reproduces the published AUCs and fails if it ever
stops doing so. The sweep's artefact is committed.
