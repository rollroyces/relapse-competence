# The leukocyte audit: what a bulk plasma channel can actually read

**Audit ID:** `leukocyte-audit-2026-11`
**Date of run:** 2026-11-09
**Reproduce:** `python scripts/leukocyte_audit.py --patients 800`
**Artefacts:** `results/leukocyte_audit/leukocyte_audit.json`,
`results/leukocyte_audit/leukocyte_audit.tsv`,
`results/leukocyte_audit/operating_point.json`

---

## 1. What this document is

The gate review's plasma numbers come from a model whose plasma cfDNA pool has
no leukocyte compartment: it is tumour-shed material plus a 1e-6
sequencing-error floor, so the electrical channel's signal is the tumour's
contribution alone.

In bulk plasma that is not the case. Most cfDNA is leukocyte-derived, and KCa3.1
is expressed in immune cells, so the channel locus carries a large leukocyte
background and the tumour's state is a small perturbation on it. The
per-patient audit ([`PER-PATIENT-AUDIT.md`](PER-PATIENT-AUDIT.md))
established that the tumour's state fraction is the decisive quantity for the
readout, so what the plasma channel can resolve about the state is the
question this document answers.

The compartment was added default-off. With it off, the golden fixture is
**byte-identical** to the committed one -- 238,602 bytes, an exact match -- on
the machine that captured it. On another platform the simulator's last-bit
float output differs by the one or two units in the last place that `exp` and
`log` produce differently there, which is what the repository's existing
golden check already tolerates; the invariant that holds on every platform is
that the model reproduces the published reference exactly as it did before the
extension. The extra random draw that carries the compartment is inside a
guard, so with it off no measurement records any leukocyte reads at all.

The audit's control reproduces the gate review's published operating-point AUCs
to the last digit: 0.992862 for
NSCLC/KCNN4, 0.706545 for SCLC/KCNN4
and 0.694505 for SCLC/PIEZO1.

The panel was then re-allocated to carry a leukocyte reference set, the
operating point re-derived against it, and the audit re-run. Section 6 is the
answer, and it is a negative one.

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

## 3. Why the published statistic cannot survive this

The programme's statistic is the electrical channel's per-locus signal divided
by the mutation channel's. The mutation channel is tumour-specific. The
electrical channel, once a leukocyte compartment exists, is the mixture of both
compartments. The ratio therefore carries the leukocyte contribution divided by
the tumour's own cfDNA share -- and that term is *inversely* related to tumour
burden. Relapsers carry more tumour, so the raw ratio is systematically lower
in relapsers: the statistic does not degrade, it inverts.

The reason the published statistic works so well without the compartment is
worth stating, because it is the same reason it cannot be repaired by
correcting the background afterwards. In the model without a leukocyte
compartment, the electrical channel's signal is proportional to the tumour's
cfDNA share, so the ratio cancels the burden **and its noise**: both numerator
and denominator carry counting noise proportional to the square root of that
share, and dividing removes it. With a leukocyte compartment the electrical
channel's noise is proportional to the square root of the *whole* pool, which is
not proportional to the tumour's share -- so dividing by the mutation channel
amplifies it by the inverse of that share. The statistic stops being
burden-invariant in the only sense that mattered.

## 4. The assay design this forces

Three elements, and only one of them is a correction:

1. **Localise the channel transcript to the tumour.** Only reads at the
   channel locus that also carry a tumour-specific somatic variant on the
   same molecule are counted. This restores the proportionality the published
   statistic depends on, because those reads are tumour-derived by
   construction, so the ratio cancels the burden and the noise as it did
   before. It requires the participant's own somatic variant set, which is
   what the matched primary tumour provides.
2. **Estimate each participant's tumour cfDNA fraction** from the somatic
   variants the mutation panel already reads. This is the denominator the
   enrichment statistic divides by, and it is a quantity the programme has
   never had a measurement of.
3. **Include leukocyte reference loci** -- positions in transcripts the immune
   cells express and the tumour does not. These are *not* the correction.
   They measure each library's leukocyte contribution and the tumour fraction
   independently, so a library's background can be checked rather than
   assumed, and a failed or inconsistent library can be caught.

## 5. The sweep, with the reference set

Each row is the operating point at a different tumour cfDNA yield, leukocyte
background and reference-set size. "Tumour share" is measured, not nominal:
the median of the mutation channel's per-locus VAF over the MRD-positive
population.

| Tumour yield x | Leukocyte background | Reference loci | Measured tumour share | MRD-positive | Raw AUC | Oracle-corrected AUC | Reference-corrected AUC |
|---|---|---|---|---|---|---|---|
| 1 | 0.00 | 0 | 8.08e-05 | 508 | 0.9929 | 0.9929 | 0.9929 |
| 1 | 0.00 | 20 | 7.50e-05 | 533 | 0.9949 | 0.9949 | 0.9949 |
| 1 | 0.50 | 0 | 4.59e-05 | 538 | 0.0053 | 0.5111 | 0.0053 |
| 1 | 0.50 | 20 | 6.73e-05 | 525 | 0.0042 | 0.5179 | 0.4405 |
| 1 | 0.90 | 0 | 4.59e-05 | 538 | 0.0053 | 0.5034 | 0.0053 |
| 1 | 0.90 | 20 | 9.22e-05 | 529 | 0.0053 | 0.5273 | 0.4424 |
| 1 | 0.99 | 0 | 6.55e-05 | 545 | 0.0057 | 0.5168 | 0.0057 |
| 1 | 0.99 | 20 | 9.44e-05 | 525 | 0.0055 | 0.5221 | 0.4475 |
| 3 | 0.00 | 0 | 7.27e-05 | 663 | 0.9816 | 0.9816 | 0.9816 |
| 3 | 0.00 | 20 | 3.96e-05 | 655 | 0.9822 | 0.9822 | 0.9822 |
| 3 | 0.50 | 0 | 6.13e-05 | 675 | 0.0019 | 0.4870 | 0.0019 |
| 3 | 0.50 | 20 | 7.27e-05 | 661 | 0.0025 | 0.5363 | 0.5091 |
| 3 | 0.90 | 0 | 5.27e-05 | 675 | 0.0019 | 0.4845 | 0.0019 |
| 3 | 0.90 | 20 | 8.00e-05 | 700 | 0.0020 | 0.5310 | 0.5406 |
| 3 | 0.99 | 0 | 5.58e-05 | 676 | 0.0025 | 0.4856 | 0.0025 |
| 3 | 0.99 | 20 | 8.60e-05 | 689 | 0.0040 | 0.5292 | 0.5378 |
| 10 | 0.00 | 0 | 6.76e-05 | 734 | 0.9698 | 0.9698 | 0.9698 |
| 10 | 0.00 | 20 | 5.44e-05 | 727 | 0.9670 | 0.9670 | 0.9670 |
| 10 | 0.50 | 0 | 4.79e-05 | 744 | 0.0023 | 0.5390 | 0.0023 |
| 10 | 0.50 | 20 | 5.01e-05 | 735 | 0.0022 | 0.5485 | 0.5397 |
| 10 | 0.90 | 0 | 4.79e-05 | 744 | 0.0023 | 0.5357 | 0.0023 |
| 10 | 0.90 | 20 | 4.05e-05 | 752 | 0.0025 | 0.5570 | 0.5445 |
| 10 | 0.99 | 0 | 3.91e-05 | 744 | 0.0038 | 0.5316 | 0.0038 |
| 10 | 0.99 | 20 | 4.75e-05 | 742 | 0.0029 | 0.5375 | 0.5440 |
| 30 | 0.00 | 0 | 1.11e-04 | 756 | 0.9684 | 0.9684 | 0.9684 |
| 30 | 0.00 | 20 | 1.08e-04 | 769 | 0.9532 | 0.9532 | 0.9532 |
| 30 | 0.50 | 0 | 5.71e-05 | 769 | 0.0022 | 0.5323 | 0.0022 |
| 30 | 0.50 | 20 | 9.67e-05 | 758 | 0.0027 | 0.5549 | 0.5415 |
| 30 | 0.90 | 0 | 5.67e-05 | 769 | 0.0026 | 0.5146 | 0.0026 |
| 30 | 0.90 | 20 | 8.50e-05 | 765 | 0.0025 | 0.5317 | 0.5224 |
| 30 | 0.99 | 0 | 5.67e-05 | 769 | 0.0029 | 0.4963 | 0.0029 |
| 30 | 0.99 | 20 | 9.67e-05 | 765 | 0.0027 | 0.5152 | 0.5055 |
| 100 | 0.00 | 0 | 3.59e-04 | 766 | 0.9472 | 0.9472 | 0.9472 |
| 100 | 0.00 | 20 | 2.09e-04 | 773 | 0.9448 | 0.9448 | 0.9448 |
| 100 | 0.50 | 0 | 2.55e-04 | 773 | 0.0024 | 0.5659 | 0.0024 |
| 100 | 0.50 | 20 | 2.99e-04 | 761 | 0.0026 | 0.5836 | 0.5392 |
| 100 | 0.90 | 0 | 2.50e-04 | 774 | 0.0024 | 0.4998 | 0.0024 |
| 100 | 0.90 | 20 | 2.99e-04 | 769 | 0.0013 | 0.5273 | 0.4849 |
| 100 | 0.99 | 0 | 2.17e-04 | 774 | 0.0023 | 0.4365 | 0.0023 |
| 100 | 0.99 | 20 | 3.03e-04 | 768 | 0.0026 | 0.4778 | 0.4695 |
| 300 | 0.00 | 0 | 8.38e-04 | 787 | 0.7984 | 0.7984 | 0.7984 |
| 300 | 0.00 | 20 | 8.29e-04 | 789 | 0.8132 | 0.8132 | 0.8132 |
| 300 | 0.50 | 0 | 5.85e-04 | 793 | 0.0027 | 0.5914 | 0.0027 |
| 300 | 0.50 | 20 | 6.28e-04 | 794 | 0.0022 | 0.5961 | 0.5650 |
| 300 | 0.90 | 0 | 5.75e-04 | 794 | 0.0027 | 0.5121 | 0.0027 |
| 300 | 0.90 | 20 | 5.68e-04 | 792 | 0.0023 | 0.5133 | 0.5076 |
| 300 | 0.99 | 0 | 5.64e-04 | 793 | 0.0025 | 0.4352 | 0.0025 |
| 300 | 0.99 | 20 | 6.29e-04 | 796 | 0.0015 | 0.4475 | 0.4635 |
| 1000 | 0.00 | 0 | 1.94e-03 | 800 | 0.5425 | 0.5425 | 0.5425 |
| 1000 | 0.00 | 20 | 1.86e-03 | 802 | 0.5699 | 0.5699 | 0.5699 |
| 1000 | 0.50 | 0 | 1.62e-03 | 800 | 0.0013 | 0.4964 | 0.0013 |
| 1000 | 0.50 | 20 | 2.10e-03 | 798 | 0.0005 | 0.4704 | 0.5227 |
| 1000 | 0.90 | 0 | 1.54e-03 | 800 | 0.0017 | 0.4308 | 0.0017 |
| 1000 | 0.90 | 20 | 1.69e-03 | 803 | 0.0015 | 0.4134 | 0.4576 |
| 1000 | 0.99 | 0 | 1.26e-03 | 802 | 0.0025 | 0.3632 | 0.0025 |
| 1000 | 0.99 | 20 | 1.85e-03 | 803 | 0.0018 | 0.3492 | 0.4036 |
| 3000 | 0.00 | 0 | 5.37e-03 | 805 | 0.4482 | 0.4482 | 0.4482 |
| 3000 | 0.00 | 20 | 6.18e-03 | 806 | 0.4691 | 0.4691 | 0.4691 |
| 3000 | 0.50 | 0 | 4.81e-03 | 803 | 0.0026 | 0.4553 | 0.0026 |
| 3000 | 0.50 | 20 | 4.99e-03 | 805 | 0.0015 | 0.4325 | 0.4544 |
| 3000 | 0.90 | 0 | 4.81e-03 | 803 | 0.0025 | 0.3856 | 0.0025 |
| 3000 | 0.90 | 20 | 4.55e-03 | 809 | 0.0021 | 0.3724 | 0.3996 |
| 3000 | 0.99 | 0 | 4.40e-03 | 803 | 0.0046 | 0.3032 | 0.0046 |
| 3000 | 0.99 | 20 | 4.57e-03 | 809 | 0.0014 | 0.3425 | 0.3190 |
| 10000 | 0.00 | 0 | 2.04e-02 | 805 | 0.3918 | 0.3918 | 0.3918 |
| 10000 | 0.00 | 20 | 1.77e-02 | 804 | 0.4099 | 0.4099 | 0.4099 |
| 10000 | 0.50 | 0 | 1.45e-02 | 806 | 0.0034 | 0.3790 | 0.0034 |
| 10000 | 0.50 | 20 | 1.77e-02 | 806 | 0.0012 | 0.3448 | 0.3572 |
| 10000 | 0.90 | 0 | 1.52e-02 | 806 | 0.0033 | 0.3045 | 0.0033 |
| 10000 | 0.90 | 20 | 1.65e-02 | 808 | 0.0016 | 0.2648 | 0.2753 |
| 10000 | 0.99 | 0 | 1.41e-02 | 806 | 0.0032 | 0.2195 | 0.0032 |
| 10000 | 0.99 | 20 | 1.54e-02 | 808 | 0.0017 | 0.2073 | 0.2113 |

"Oracle-corrected" subtracts the leukocyte contribution with foreknowledge,
which no assay has. "Reference-corrected" subtracts what the reference loci
actually measured. Both are in the table because the gap between them is the
cost of measuring the background rather than subtracting it with foreknowledge.

### At the published operating point, without a reference set

| Configuration | Leukocyte background | Measured tumour share | MRD-positive | Raw AUC | Oracle-corrected AUC |
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

## 6. The re-derived operating point, and why there is not one

The panel was re-allocated to carry a leukocyte reference set, and the
operating point re-derived by searching the panel space against the
programme's own criterion: the reference-corrected enrichment AUC has to
clear K3 in the bulk-plasma regime, at the measured tumour share. The search
covers sequencing depth from 200,000x to 20,000,000x and reference sets from 5
to 50 loci, with the electrical allocation unchanged at 25%.

| Depth | Reference loci | Reads per draw | Measured tumour share | Raw AUC | Oracle-corrected AUC | Reference-corrected AUC | Clears K3? |
|---|---|---|---|---|---|---|---|
| 200,000 | 5 | 40,000,000 | 6.49e-05 | 0.0057 | 0.5016 | 0.3771 | **no** |
| 200,000 | 20 | 40,000,000 | 9.44e-05 | 0.0055 | 0.5221 | 0.4475 | **no** |
| 200,000 | 50 | 40,000,000 | 1.17e-04 | 0.0075 | 0.4656 | 0.5133 | **no** |
| 2,000,000 | 5 | 400,000,000 | 4.49e-05 | 0.0047 | 0.4872 | 0.5011 | **no** |
| 2,000,000 | 20 | 400,000,000 | 7.34e-05 | 0.0034 | 0.5796 | 0.5815 | **no** |
| 2,000,000 | 50 | 400,000,000 | 5.85e-05 | 0.0056 | 0.5670 | 0.5506 | **no** |
| 20,000,000 | 5 | 4,000,000,000 | 6.92e-05 | 0.0072 | 0.5495 | 0.4681 | **no** |
| 20,000,000 | 20 | 4,000,000,000 | 6.71e-05 | 0.0105 | 0.5386 | 0.5364 | **no** |
| 20,000,000 | 50 | 4,000,000,000 | 5.24e-05 | 0.0092 | 0.5426 | 0.5115 | **no** |

**Nothing in that space clears K3.** The best reference-corrected AUC found is
0.5815, at 2,000,000x with
20 reference loci -- against a threshold
of 0.65. Deepening the panel by a hundredfold, to
4,000,000,000 reads per
draw, does not change the verdict.

## 7. Why more depth does not help

Because the limitation is structural rather than budgetary. The noise in the
burden-normalised enrichment is amplified by the inverse of the patient's own
tumour cfDNA share, and the two arms of an MRD-positive cohort do not sit at
the same share. Measured in the model at the published operating point, the
relapsing arm's median tumour cfDNA share is 3.09e-04 and the
non-relapsing arm's is 1.70e-06 -- two orders of magnitude
apart. The non-relapsing arm's statistic is therefore noise-dominated at any
depth, which is why the best oracle-corrected AUC in the whole search is
0.5796 and the best reference-corrected one 0.5815:
subtracting the background perfectly does not help either.

The same arithmetic says what would work. Under localisation the counted
reads are tumour-derived by construction, so their noise is proportional to
the square root of the tumour's share again, the ratio cancels it as it did
in the published model, and the published AUC of 0.9929 is the projection --
with one caveat that the model cannot check. Localisation keeps only the
reads that happen to carry a variant, so it divides the effective depth by
the localisation rate, and the quantity that sets the readout's precision is
depth times that rate. The localisation rate is set by how many tumour-specific
variants the mutation panel reads per participant, which is a property of the
data being requested.

## 8. What this means

- **The panel re-allocation does not rescue the readout, and that is the
  useful result.** It was the obvious thing to try, and it does not work: the
  correction is limited by the statistic, not by the read budget.
- **The leukocyte reference set is a QC and tumour-fraction tool, not the
  correction.** It belongs in the panel because each library's background and
  tumour fraction should be measured rather than assumed, and because a
  library whose background is inconsistent with its tumour fraction should be
  caught. It does not belong in the panel as a way of making an unlocalised
  readout work.
- **Localisation is the correction, and it is what the proposal has to
  specify.** The matched primary tumour stops being optional: the
  participant's own somatic variant set is what localises the channel
  transcript to the tumour.
- **The published projection is an upper bound, for a localised assay.** It is
  the right number for an assay that localises; it is the wrong number for one
  that does not.

## 9. Limitations

- The leukocyte compartment is a single parameter: the share of the electrical
  locus's signal that is leukocyte-derived. It does not model the cfDNA
  transcript pool's composition, so it is a bounding device rather than a
  measurement.
- The reference loci are assumed to carry the same leukocyte signal as the
  channel, which is the optimistic case: a leukocyte-restricted transcript such
  as PTPRC is more abundant in leukocytes than KCa3.1 is, so a real reference
  set would overestimate the background rather than match it.
- The sweep's x-axis moves the mutation channel as well as the electrical one,
  because both read the same tumour cfDNA. That is why the no-leukocyte curve
  is not flat, and why the sweep cannot be read as a pure dose-response.
- The model does not simulate per-read tumour assignment, so the projection
  under localisation is an argument from the structure of the statistic rather
  than a simulated measurement.
- The measured expression levels are from single-cell RNA-seq after
  per-sample normalisation to counts per 10,000; a cfDNA transcript assay has a
  different composition, and the leukocyte share in a real plasma library is
  not measured here.
- Nothing in this audit uses a real plasma sample.

## 10. Reproducing

```bash
python scripts/leukocyte_audit.py --patients 800            # the full sweep
python scripts/leukocyte_audit.py --patients 800 --control-only  # what CI runs
```

CI runs the control, which reproduces the published AUCs and fails if it ever
stops doing so. The sweep and the derivation are committed as artefacts.
