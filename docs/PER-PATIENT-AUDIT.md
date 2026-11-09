# The per-patient audit: the readout, tumour by tumour

**Audit ID:** `per-patient-audit-2026-11`
**Date of run:** 2026-11-09
**Reproduce:** `python scripts/per_library_folds.py` then
`python scripts/per_patient_audit.py --patients 800`
**Artefacts:** `results/per_library_folds/per_library_folds.json`,
`results/per_library_folds/per_library_folds.tsv`,
`results/per_patient_audit/per_patient_audit.json`,
`results/per_patient_audit/per_patient_audit.tsv`

---

## 1. What this document is, and what it qualifies

The gate review applied the programme's five killing conditions to the measured
evidence and reported three state candidates that survive K1 and K3: SCLC/KCNN4,
SCLC/PIEZO1 and NSCLC/KCNN4. Its projection used a **pooled** per-cell fold and
a **pooled** state fraction for every simulated patient.

Both pooled values are cell-count weighted, and in the relapsed-SCLC deposit
that is decisive. Three libraries hold 2,482 of the deposit's 2,872 state cells
(86.4%), and the channel's baseline expression differs by metastatic site:
across the SCLC libraries the mean expression in non-state cells spans 0.0093
to 0.2421 for KCNN4 (26-fold) and 0.0091 to 0.5888 for PIEZO1 (65-fold). A pooled
fold therefore compares the state cells of one library against the non-state
cells of another, which is not the quantity a patient's own plasma would carry.

This document recomputes both inputs per library and re-runs the projection for
each tumour, over the same depth x panel-size grid the gate review uses. It
keeps two layers apart that the gate review merged:

- the **measurement** -- a library's own fold and state fraction. This needs no
  assumption at all.
- the **projection** -- what a plasma assay would score given that tumour. This
  needs the state fraction of the MRD-positive patients who do *not* relapse,
  which this repository has never measured, so it is swept over and reported as
  a band rather than as a point.

The headline: **the SCLC readout does not survive per tumour; the EGFR-mutant
NSCLC readout does.** The gate review's published numbers are not wrong -- they
are the pooled projection -- but reading them as a statement about patients is
not supportable, and this document says so with the per-tumour numbers.

Two controls hold the new layer to the old one. The pooled folds recomputed
here reproduce the published state-expression artefacts with a maximum absolute
difference of 0.0, and the recomputed per-library detection-ratio sign counts
reproduce the published SCLC per-sample sign counts exactly for all seven
channels. The pooled inputs re-projected on the audit's own code path
reproduce the gate review's published operating-point AUCs exactly: 0.706545
for SCLC/KCNN4, 0.694505 for SCLC/PIEZO1 and 0.992862 for NSCLC/KCNN4.

## 2. The measurement layer: each tumour's own fold and state fraction

The fold is the ratio of the means in linear (counts per 10,000) space, state
cells over neighbouring tumour cells, computed **within one library**. It is
`n/a` where the library has no state cells at all, because there is then nothing
to compare.

| Dataset | Library | Site | State cells | State fraction | KCNN4 fold | PIEZO1 fold |
|---|---|---|---:|---:|---:|---:|
| SCLC | GSM9043712 | liver core needle biopsy | 1965 | 0.3742 | 1.037 | 0.823 |
| SCLC | GSM9043713 | liver core needle biopsy | 105 | 0.1045 | 0.276 | 6.000 |
| SCLC | GSM9043714 | lymph node core needle biopsy | 0 | 0.0000 | n/a | n/a |
| SCLC | GSM9043715 | head and neck core needle biopsy | 3 | 0.0006 | 0.000 | 5.763 |
| SCLC | GSM9043716 | adrenal gland core needle biopsy | 18 | 0.0130 | 0.820 | 1.798 |
| SCLC | GSM9043717 | liver core needle biopsy | 345 | 0.3499 | 0.588 | 2.735 |
| SCLC | GSM9043718 | lung core needle biopsy | 51 | 0.0099 | 0.577 | 1.293 |
| SCLC | GSM9043719 | lung surgical resection | 37 | 0.0609 | 0.000 | 1.129 |
| SCLC | GSM9043720 | brain surgical resection | 23 | 0.0523 | n/a | 0.967 |
| SCLC | GSM9043721 | brain surgical resection | 97 | 0.2680 | 2.182 | 1.080 |
| SCLC | GSM9043722 | lung core needle biopsy | 9 | 0.0104 | n/a | 0.000 |
| SCLC | GSM9043723 | lung/mediastinal core needle biopsy | 24 | 0.0750 | 0.063 | 18.996 |
| SCLC | GSM9043724 | head and neck core needle biopsy | 172 | 0.1847 | 0.911 | 3.560 |
| SCLC | GSM9043725 | retroperitoneal core needle biopsy | 17 | 0.0088 | 2.206 | 4.523 |
| SCLC | GSM9043726 | adrenal gland core needle biopsy | 6 | 0.0019 | 0.000 | 19.296 |
| NSCLC | GSM10173924 | Right lung / treatment_naive | 12 | 0.0538 | 0.388 | 0.685 |
| NSCLC | GSM10173925 | Pleura / osi_progression | 4 | 0.0070 | 5.348 | 1.888 |
| NSCLC | GSM10173926 | Liver / osi_progression | 23 | 0.0480 | 2.737 | 1.607 |
| NSCLC | GSM10173927 | Left interlobar station 11L lymph node / treatment_naive | 0 | 0.0000 | n/a | n/a |
| NSCLC | GSM10173928 | Liver / treatment_naive | 32 | 0.1616 | 2.690 | 0.516 |
| NSCLC | GSM10173929 | Liver / treatment_naive | 5 | 0.0379 | 0.731 | 1.545 |
| NSCLC | GSM10173930 | Liver / osi_progression | 3 | 0.0390 | 0.000 | 0.688 |
| NSCLC | GSM10173931 | Lung / treatment_naive | 57 | 0.4419 | 1.485 | 1.213 |
| NSCLC | GSM10173932 | Lung / treatment_naive | 59 | 0.3665 | 16.331 | 1.167 |
| NSCLC | GSM10173933 | Lung / osi_mrd | 118 | 0.2790 | 32.164 | 1.505 |
| NSCLC | GSM10173934 | Lung / osi_mrd | 20 | 0.3125 | 1.867 | 1.234 |
| NSCLC | GSM10173935 | Liver / osi_progression | 1238 | 0.9246 | 3.310 | 1.088 |
| NSCLC | GSM10173936 | Left lung lymph nodes / osi_progression | 20 | 0.7407 | n/a | n/a |
| NSCLC | GSM10173937 | Lung / progression | 429 | 0.4881 | 6.162 | 0.607 |
| NSCLC | GSM10173938 | Lung / treatment_naive | 159 | 0.4297 | 3.504 | 0.774 |
| NSCLC | GSM10173939 | Lung / osi_mrd | 132 | 0.3917 | 3.558 | 0.695 |
| NSCLC | GSM10173940 | Lung / treatment_naive | 168 | 0.3443 | 1.119 | 0.702 |
| NSCLC | GSM10173941 | Lung / osi_progression | 16 | 0.1006 | 1.339 | 1.138 |
| NSCLC | GSM10173942 | Lung / treatment_naive | 3 | 0.1250 | 1.158 | 1.114 |
| NSCLC | GSM10173943 | Lung / treatment_naive | 10 | 0.0195 | 64.207 | 0.895 |
| NSCLC | GSM10173944 | Lung / treatment_naive | 54 | 0.0776 | 4.851 | 1.673 |
| NSCLC | GSM10173945 | Lung / osi_mrd | 187 | 0.6192 | 3.979 | 0.462 |
| NSCLC | GSM10173946 | Lung / osi_mrd | 1058 | 0.6491 | 1.312 | 0.931 |
| NSCLC | GSM10173947 | Lung / osi_mrd | 127 | 0.5314 | 6.873 | 0.432 |
| NSCLC | GSM10173948 | Lung / osi_mrd | 44 | 0.3667 | 11.952 | 1.745 |

What the table says:

- **SCLC / KCNN4: the fold exceeds 1 in 3 of the 12 libraries with a computable
  fold**, and the median is 0.583. The channel is not on in the state in most
  relapsed-SCLC tumours.
- **SCLC / PIEZO1: the fold exceeds 1 in 11 of 14**, median 2.267. Piezo1 is a
  consistent state marker in SCLC, which is the published finding and it
  survives.
- **NSCLC / KCNN4: the fold exceeds 1 in 20 of 23**, median 3.310 against a
  pooled 3.698. Here the pooled number *is* representative, because the deposit
  is one tissue and the state cells are not concentrated in a few libraries.

Two libraries carry no state cells at all: one lymph node metastasis
(GSM9043714) and one left interlobar lymph node (GSM10173927).

## 3. The projection layer: what a plasma assay would score, per tumour

The projection holds the relapsers' state fraction at the library's measured
value with no between-patient spread, so the cohort is homogeneous in the way
that matters. The MRD-positive patients who do not relapse are assigned a state
fraction of 0.10 -- the simulator's default, and an assumption this repository
has never measured. The last two columns give the band over the sweep.

| Dataset | Library | Channel | Fold | State fraction | AUC | K1 | K3 | MRD sensitivity | Specificity | PPV | AUC min (sweep) | AUC max (sweep) |
|---|---|---|---:|---:|---:|:--:|:--:|---:|---:|---:|---:|---:|
| SCLC | GSM9043712 | KCNN4 | 1.037 | 0.3742 | 0.5569 | fire | fire | 0.9406 | 0.9900 | 0.7251 | 0.5231 | 0.5971 |
| SCLC | GSM9043712 | PIEZO1 | 0.823 | 0.3742 | 0.4658 | fire | fire | 0.9400 | 0.9900 | 0.7217 | 0.4658 | 0.4658 |
| SCLC | GSM9043713 | KCNN4 | 0.276 | 0.1045 | 0.4658 | fire | fire | 0.9400 | 0.9900 | 0.7217 | 0.4658 | 0.4658 |
| SCLC | GSM9043713 | PIEZO1 | 6.000 | 0.1045 | 0.8427 | pass | pass | 0.9490 | 0.9900 | 0.7323 | 0.6020 | 0.9644 |
| SCLC | GSM9043715 | KCNN4 | 0.000 | 0.0006 | 0.4658 | fire | fire | 0.9400 | 0.9900 | 0.7217 | 0.4658 | 0.4658 |
| SCLC | GSM9043715 | PIEZO1 | 5.763 | 0.0006 | 0.2563 | fire | fire | 0.9264 | 0.9900 | 0.7185 | 0.1141 | 0.3581 |
| SCLC | GSM9043716 | KCNN4 | 0.820 | 0.0130 | 0.4658 | fire | fire | 0.9400 | 0.9900 | 0.7217 | 0.4658 | 0.4658 |
| SCLC | GSM9043716 | PIEZO1 | 1.798 | 0.0130 | 0.5268 | fire | fire | 0.9487 | 0.9900 | 0.7255 | 0.3776 | 0.5268 |
| SCLC | GSM9043717 | KCNN4 | 0.588 | 0.3499 | 0.4658 | fire | fire | 0.9400 | 0.9900 | 0.7217 | 0.4658 | 0.4658 |
| SCLC | GSM9043717 | PIEZO1 | 2.735 | 0.3499 | 0.9961 | pass | pass | 0.9144 | 0.9900 | 0.7174 | 0.9899 | 0.9981 |
| SCLC | GSM9043718 | KCNN4 | 0.577 | 0.0099 | 0.4658 | fire | fire | 0.9400 | 0.9900 | 0.7217 | 0.4658 | 0.4658 |
| SCLC | GSM9043718 | PIEZO1 | 1.293 | 0.0099 | 0.4767 | fire | fire | 0.9365 | 0.9900 | 0.7124 | 0.3976 | 0.5264 |
| SCLC | GSM9043719 | KCNN4 | 0.000 | 0.0609 | 0.4658 | fire | fire | 0.9400 | 0.9900 | 0.7217 | 0.4658 | 0.4658 |
| SCLC | GSM9043719 | PIEZO1 | 1.129 | 0.0609 | 0.5469 | fire | fire | 0.9337 | 0.9900 | 0.7291 | 0.5003 | 0.5469 |
| SCLC | GSM9043720 | PIEZO1 | 0.967 | 0.0523 | 0.4658 | fire | fire | 0.9400 | 0.9900 | 0.7217 | 0.4658 | 0.4658 |
| SCLC | GSM9043721 | KCNN4 | 2.182 | 0.2680 | 0.9802 | pass | pass | 0.9160 | 0.9900 | 0.7214 | 0.9501 | 0.9916 |
| SCLC | GSM9043721 | PIEZO1 | 1.080 | 0.2680 | 0.5744 | fire | fire | 0.9258 | 0.9900 | 0.7043 | 0.5744 | 0.6372 |
| SCLC | GSM9043722 | PIEZO1 | 0.000 | 0.0104 | 0.4658 | fire | fire | 0.9400 | 0.9900 | 0.7217 | 0.4658 | 0.4658 |
| SCLC | GSM9043723 | KCNN4 | 0.063 | 0.0750 | 0.4658 | fire | fire | 0.9400 | 0.9900 | 0.7217 | 0.4658 | 0.4658 |
| SCLC | GSM9043723 | PIEZO1 | 18.996 | 0.0750 | 0.7380 | pass | pass | 0.9440 | 0.9900 | 0.7246 | 0.4862 | 0.9310 |
| SCLC | GSM9043724 | KCNN4 | 0.911 | 0.1847 | 0.4658 | fire | fire | 0.9400 | 0.9900 | 0.7217 | 0.4658 | 0.4658 |
| SCLC | GSM9043724 | PIEZO1 | 3.560 | 0.1847 | 0.9263 | pass | pass | 0.9444 | 0.9900 | 0.7083 | 0.8992 | 0.9879 |
| SCLC | GSM9043725 | KCNN4 | 2.206 | 0.0088 | 0.3368 | fire | fire | 0.9145 | 0.9900 | 0.6854 | 0.2327 | 0.4524 |
| SCLC | GSM9043725 | PIEZO1 | 4.523 | 0.0088 | 0.2980 | fire | fire | 0.9410 | 0.9900 | 0.7112 | 0.1671 | 0.4287 |
| SCLC | GSM9043726 | KCNN4 | 0.000 | 0.0019 | 0.4658 | fire | fire | 0.9400 | 0.9900 | 0.7217 | 0.4658 | 0.4658 |
| SCLC | GSM9043726 | PIEZO1 | 19.296 | 0.0019 | 0.1771 | fire | fire | 0.9116 | 0.9900 | 0.7037 | 0.0745 | 0.3802 |
| NSCLC | GSM10173924 | KCNN4 | 0.388 | 0.0538 | 0.4658 | fire | fire | 0.9400 | 0.9900 | 0.7217 | 0.4658 | 0.4658 |
| NSCLC | GSM10173925 | KCNN4 | 5.348 | 0.0070 | 0.3017 | fire | fire | 0.9357 | 0.9900 | 0.7109 | 0.1447 | 0.4481 |
| NSCLC | GSM10173926 | KCNN4 | 2.737 | 0.0480 | 0.6483 | pass | fire | 0.9241 | 0.9900 | 0.7449 | 0.4000 | 0.7235 |
| NSCLC | GSM10173928 | KCNN4 | 2.690 | 0.1616 | 0.8902 | pass | pass | 0.9488 | 0.9900 | 0.7053 | 0.8252 | 0.9700 |
| NSCLC | GSM10173929 | KCNN4 | 0.731 | 0.0379 | 0.4658 | fire | fire | 0.9400 | 0.9900 | 0.7217 | 0.4658 | 0.4658 |
| NSCLC | GSM10173930 | KCNN4 | 0.000 | 0.0390 | 0.4658 | fire | fire | 0.9400 | 0.9900 | 0.7217 | 0.4658 | 0.4658 |
| NSCLC | GSM10173931 | KCNN4 | 1.485 | 0.4419 | 0.9634 | pass | pass | 0.9275 | 0.9900 | 0.7247 | 0.9495 | 0.9814 |
| NSCLC | GSM10173932 | KCNN4 | 16.331 | 0.3665 | 0.9972 | pass | pass | 0.9359 | 0.9900 | 0.7006 | 0.9972 | 0.9999 |
| NSCLC | GSM10173933 | KCNN4 | 32.164 | 0.2790 | 0.9933 | pass | pass | 0.9275 | 0.9900 | 0.6938 | 0.9933 | 0.9972 |
| NSCLC | GSM10173934 | KCNN4 | 1.867 | 0.3125 | 0.9884 | pass | pass | 0.9364 | 0.9900 | 0.7273 | 0.9713 | 0.9885 |
| NSCLC | GSM10173935 | KCNN4 | 3.310 | 0.9246 | 0.9957 | pass | pass | 0.9194 | 0.9900 | 0.7143 | 0.9946 | 0.9980 |
| NSCLC | GSM10173937 | KCNN4 | 6.162 | 0.4881 | 0.9959 | pass | pass | 0.9268 | 0.9900 | 0.7099 | 0.9937 | 0.9976 |
| NSCLC | GSM10173938 | KCNN4 | 3.504 | 0.4297 | 0.9945 | pass | pass | 0.9213 | 0.9900 | 0.7160 | 0.9937 | 0.9976 |
| NSCLC | GSM10173939 | KCNN4 | 3.558 | 0.3917 | 0.9936 | pass | pass | 0.9361 | 0.9900 | 0.7219 | 0.9880 | 0.9973 |
| NSCLC | GSM10173940 | KCNN4 | 1.119 | 0.3443 | 0.7211 | pass | pass | 0.9256 | 0.9900 | 0.7177 | 0.6774 | 0.7211 |
| NSCLC | GSM10173941 | KCNN4 | 1.339 | 0.1006 | 0.6305 | pass | fire | 0.9328 | 0.9900 | 0.7065 | 0.5040 | 0.6464 |
| NSCLC | GSM10173942 | KCNN4 | 1.158 | 0.1250 | 0.5920 | fire | fire | 0.9478 | 0.9900 | 0.7202 | 0.5119 | 0.6785 |
| NSCLC | GSM10173943 | KCNN4 | 64.207 | 0.0195 | 0.4037 | fire | fire | 0.9107 | 0.9900 | 0.7331 | 0.1788 | 0.6440 |
| NSCLC | GSM10173944 | KCNN4 | 4.851 | 0.0776 | 0.7450 | pass | pass | 0.9203 | 0.9900 | 0.7203 | 0.4700 | 0.9079 |
| NSCLC | GSM10173945 | KCNN4 | 3.979 | 0.6192 | 0.9977 | pass | pass | 0.9443 | 0.9900 | 0.7314 | 0.9913 | 0.9977 |
| NSCLC | GSM10173946 | KCNN4 | 1.312 | 0.6491 | 0.9491 | pass | pass | 0.9437 | 0.9900 | 0.7278 | 0.9434 | 0.9699 |
| NSCLC | GSM10173947 | KCNN4 | 6.873 | 0.5314 | 0.9991 | pass | pass | 0.9229 | 0.9900 | 0.7464 | 0.9928 | 0.9991 |
| NSCLC | GSM10173948 | KCNN4 | 11.952 | 0.3667 | 0.9931 | pass | pass | 0.9114 | 0.9900 | 0.7186 | 0.9890 | 0.9936 |

- **SCLC / KCNN4 clears K3 in 1 of 12 libraries** (GSM9043721, brain surgical
  resection, fold 2.182, AUC 0.9802).
- **SCLC / PIEZO1 clears K3 in 4 of 14** (GSM9043713, GSM9043717, GSM9043723,
  GSM9043724).
- **NSCLC / KCNN4 clears K3 in 15 of 23 libraries, and in all 7 of the MRD
  libraries**, which is the cohort the programme projects: AUC 0.9491 to 0.9991.

One number deserves its own note. Where the fold does not exceed 1 the channel
carries no signal, and the enrichment AUC settles at **0.4658** -- below
chance, because what is left of the "enrichment" is a tumour-burden confound.
That is the baseline any configuration with no usable signal scores, and most
SCLC libraries score it.

## 4. The full depth x panel-size grid

The whole affordability space, per tumour, at the plan's electrical fraction of
0.25. The operating point the gate review uses -- 200,000x and 200 loci -- is
the sixth column.

| Dataset | Library | Channel | 5k/50 | 5k/200 | 50k/50 | 50k/200 | 200k/50 | 200k/200 | 500k/50 | 500k/200 |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| SCLC | GSM9043712 | KCNN4 | 0.7146 | 0.6501 | 0.6919 | 0.6077 | 0.5969 | 0.5569 | 0.5894 | 0.6013 |
| SCLC | GSM9043712 | PIEZO1 | 0.8885 | 0.7056 | 0.6545 | 0.5997 | 0.5663 | 0.4658 | 0.5617 | 0.4852 |
| SCLC | GSM9043713 | KCNN4 | 0.8885 | 0.7056 | 0.6545 | 0.5997 | 0.5663 | 0.4658 | 0.5617 | 0.4852 |
| SCLC | GSM9043713 | PIEZO1 | 0.8345 | 0.7895 | 0.7326 | 0.8411 | 0.8570 | 0.8427 | 0.8675 | 0.8542 |
| SCLC | GSM9043715 | KCNN4 | 0.8885 | 0.7056 | 0.6545 | 0.5997 | 0.5663 | 0.4658 | 0.5617 | 0.4852 |
| SCLC | GSM9043715 | PIEZO1 | 0.6734 | 0.4703 | 0.4247 | 0.2245 | 0.2173 | 0.2563 | 0.2408 | 0.1819 |
| SCLC | GSM9043716 | KCNN4 | 0.8885 | 0.7056 | 0.6545 | 0.5997 | 0.5663 | 0.4658 | 0.5617 | 0.4852 |
| SCLC | GSM9043716 | PIEZO1 | 0.7861 | 0.6264 | 0.5967 | 0.5494 | 0.4651 | 0.5268 | 0.5273 | 0.4083 |
| SCLC | GSM9043717 | KCNN4 | 0.8885 | 0.7056 | 0.6545 | 0.5997 | 0.5663 | 0.4658 | 0.5617 | 0.4852 |
| SCLC | GSM9043717 | PIEZO1 | 0.8903 | 0.8585 | 0.9425 | 0.9794 | 0.9805 | 0.9961 | 0.9909 | 0.9962 |
| SCLC | GSM9043718 | KCNN4 | 0.8885 | 0.7056 | 0.6545 | 0.5997 | 0.5663 | 0.4658 | 0.5617 | 0.4852 |
| SCLC | GSM9043718 | PIEZO1 | 0.8512 | 0.6213 | 0.5077 | 0.5711 | 0.5161 | 0.4767 | 0.5364 | 0.4796 |
| SCLC | GSM9043719 | KCNN4 | 0.8885 | 0.7056 | 0.6545 | 0.5997 | 0.5663 | 0.4658 | 0.5617 | 0.4852 |
| SCLC | GSM9043719 | PIEZO1 | 0.8473 | 0.6767 | 0.6030 | 0.5618 | 0.5866 | 0.5469 | 0.6008 | 0.4826 |
| SCLC | GSM9043720 | PIEZO1 | 0.8885 | 0.7056 | 0.6545 | 0.5997 | 0.5663 | 0.4658 | 0.5617 | 0.4852 |
| SCLC | GSM9043721 | KCNN4 | 0.8956 | 0.8313 | 0.9021 | 0.9383 | 0.8910 | 0.9802 | 0.9515 | 0.9912 |
| SCLC | GSM9043721 | PIEZO1 | 0.6550 | 0.6852 | 0.5458 | 0.7010 | 0.6098 | 0.5744 | 0.6067 | 0.6472 |
| SCLC | GSM9043722 | PIEZO1 | 0.8885 | 0.7056 | 0.6545 | 0.5997 | 0.5663 | 0.4658 | 0.5617 | 0.4852 |
| SCLC | GSM9043723 | KCNN4 | 0.8885 | 0.7056 | 0.6545 | 0.5997 | 0.5663 | 0.4658 | 0.5617 | 0.4852 |
| SCLC | GSM9043723 | PIEZO1 | 0.7282 | 0.7249 | 0.7440 | 0.6834 | 0.6221 | 0.7380 | 0.7436 | 0.7867 |
| SCLC | GSM9043724 | KCNN4 | 0.8885 | 0.7056 | 0.6545 | 0.5997 | 0.5663 | 0.4658 | 0.5617 | 0.4852 |
| SCLC | GSM9043724 | PIEZO1 | 0.7544 | 0.7019 | 0.8951 | 0.9346 | 0.9166 | 0.9263 | 0.9629 | 0.9815 |
| SCLC | GSM9043725 | KCNN4 | 0.7222 | 0.5552 | 0.5330 | 0.4564 | 0.4009 | 0.3368 | 0.4289 | 0.3226 |
| SCLC | GSM9043725 | PIEZO1 | 0.8311 | 0.6021 | 0.4594 | 0.4059 | 0.3274 | 0.2980 | 0.3821 | 0.2374 |
| SCLC | GSM9043726 | KCNN4 | 0.8885 | 0.7056 | 0.6545 | 0.5997 | 0.5663 | 0.4658 | 0.5617 | 0.4852 |
| SCLC | GSM9043726 | PIEZO1 | 0.6192 | 0.2850 | 0.3801 | 0.2221 | 0.2176 | 0.1771 | 0.2386 | 0.1776 |
| NSCLC | GSM10173924 | KCNN4 | 0.8885 | 0.7056 | 0.6545 | 0.5997 | 0.5663 | 0.4658 | 0.5617 | 0.4852 |
| NSCLC | GSM10173925 | KCNN4 | 0.7871 | 0.5579 | 0.4473 | 0.3869 | 0.3358 | 0.3017 | 0.3369 | 0.2698 |
| NSCLC | GSM10173926 | KCNN4 | 0.7830 | 0.6308 | 0.6985 | 0.5333 | 0.5759 | 0.6483 | 0.5322 | 0.4932 |
| NSCLC | GSM10173928 | KCNN4 | 0.8556 | 0.7317 | 0.8203 | 0.8650 | 0.8521 | 0.8902 | 0.9252 | 0.9488 |
| NSCLC | GSM10173929 | KCNN4 | 0.8885 | 0.7056 | 0.6545 | 0.5997 | 0.5663 | 0.4658 | 0.5617 | 0.4852 |
| NSCLC | GSM10173930 | KCNN4 | 0.8885 | 0.7056 | 0.6545 | 0.5997 | 0.5663 | 0.4658 | 0.5617 | 0.4852 |
| NSCLC | GSM10173931 | KCNN4 | 0.8855 | 0.7964 | 0.8240 | 0.8966 | 0.8777 | 0.9634 | 0.9363 | 0.9944 |
| NSCLC | GSM10173932 | KCNN4 | 0.9927 | 0.9789 | 0.9940 | 0.9917 | 0.9954 | 0.9972 | 0.9962 | 0.9947 |
| NSCLC | GSM10173933 | KCNN4 | 0.9739 | 0.9699 | 0.9664 | 0.9969 | 0.9918 | 0.9933 | 0.9994 | 0.9955 |
| NSCLC | GSM10173934 | KCNN4 | 0.8894 | 0.7903 | 0.8460 | 0.9005 | 0.8746 | 0.9884 | 0.9558 | 0.9925 |
| NSCLC | GSM10173935 | KCNN4 | 0.9815 | 0.9730 | 0.9996 | 0.9975 | 0.9959 | 0.9957 | 0.9958 | 0.9954 |
| NSCLC | GSM10173937 | KCNN4 | 0.9807 | 0.9771 | 0.9914 | 0.9926 | 0.9971 | 0.9959 | 0.9996 | 0.9949 |
| NSCLC | GSM10173938 | KCNN4 | 0.9561 | 0.9184 | 0.9848 | 0.9834 | 0.9983 | 0.9945 | 0.9936 | 0.9935 |
| NSCLC | GSM10173939 | KCNN4 | 0.8280 | 0.8945 | 0.9920 | 0.9982 | 0.9939 | 0.9936 | 0.9999 | 0.9996 |
| NSCLC | GSM10173940 | KCNN4 | 0.6667 | 0.7040 | 0.5960 | 0.6358 | 0.6993 | 0.7211 | 0.7256 | 0.7307 |
| NSCLC | GSM10173941 | KCNN4 | 0.8637 | 0.6059 | 0.6169 | 0.6601 | 0.5919 | 0.6305 | 0.5993 | 0.6261 |
| NSCLC | GSM10173942 | KCNN4 | 0.8421 | 0.7071 | 0.5897 | 0.6554 | 0.6357 | 0.5920 | 0.5472 | 0.5970 |
| NSCLC | GSM10173943 | KCNN4 | 0.9029 | 0.4215 | 0.4350 | 0.3607 | 0.4328 | 0.4037 | 0.4838 | 0.3460 |
| NSCLC | GSM10173944 | KCNN4 | 0.8711 | 0.7050 | 0.6814 | 0.6710 | 0.6842 | 0.7450 | 0.7491 | 0.7711 |
| NSCLC | GSM10173945 | KCNN4 | 0.9633 | 0.9678 | 0.9769 | 0.9939 | 0.9953 | 0.9977 | 0.9971 | 0.9982 |
| NSCLC | GSM10173946 | KCNN4 | 0.8933 | 0.6954 | 0.7759 | 0.8575 | 0.8812 | 0.9491 | 0.9378 | 0.9871 |
| NSCLC | GSM10173947 | KCNN4 | 0.9911 | 0.9678 | 0.9976 | 0.9985 | 0.9927 | 0.9991 | 0.9987 | 0.9988 |
| NSCLC | GSM10173948 | KCNN4 | 0.9529 | 0.9907 | 0.9957 | 0.9940 | 0.9939 | 0.9931 | 0.9926 | 0.9971 |

## 5. What the configurations say

| Dataset | Channel | Libraries | Fold computable | Fold > 1 | Clears K3 | Fires K1 | AUC min | AUC median | AUC max | State fraction median |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| SCLC | KCNN4 | 12 | 12 | 3 | 1 | 11 | 0.3368 | 0.4658 | 0.9802 | 0.0679 |
| SCLC | PIEZO1 | 14 | 14 | 11 | 4 | 10 | 0.1771 | 0.5017 | 0.9961 | 0.0566 |
| NSCLC | KCNN4 | 23 | 23 | 20 | 15 | 6 | 0.3017 | 0.9491 | 0.9991 | 0.3125 |

The SCLC configurations are not marginal; they are one-sided. SCLC/KCNN4 has
the channel on in 3 of 12 tumours and clears the threshold in 1. SCLC/PIEZO1 has
the channel on in 11 of 14 but clears in 4, because most relapsed-SCLC tumours
carry too little of the state for any plasma signal to exist. NSCLC/KCNN4 has
the channel on in 20 of 23 and clears in 15, including every MRD library.

## 6. Why the pooled numbers do not describe a patient

| Dataset | Channel | Pooled fold | Per-library fold median | Per-library fold min | Per-library fold max | Libraries with fold > 1 | Pooled fold with one library removed: min | max |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| SCLC | KCNN4 | 2.5539 | 0.5825 | 0.0000 | 2.2061 | 3/12 | 1.3702 | 2.8122 |
| SCLC | PIEZO1 | 3.3631 | 2.2665 | 0.0000 | 19.2957 | 11/14 | 2.8094 | 6.2977 |
| SCLC | CACNA1E | 1.1123 | 0.9213 | 0.0000 | 12.4259 | 4/11 | 0.8139 | 3.0542 |
| SCLC | KCNA3 | 0.2113 | 0.0870 | 0.0000 | 2.5307 | 2/10 | 0.1353 | 0.5107 |
| SCLC | TMEM150C | 0.3601 | 0.6217 | 0.0000 | 4.0751 | 3/13 | 0.2564 | 0.7897 |
| SCLC | STOML3 | 0.0194 | 0.0000 | 0.0000 | 49.5658 | 2/8 | 0.0041 | 1.8270 |
| SCLC | PIEZO2 | 0.1555 | 0.6051 | 0.0000 | 24.7024 | 5/12 | 0.0944 | 0.4232 |
| NSCLC | KCNN4 | 3.6979 | 3.3102 | 0.0000 | 64.2074 | 20/23 | 2.8536 | 4.5038 |
| NSCLC | PIEZO1 | 0.8387 | 1.0879 | 0.4322 | 1.8880 | 12/23 | 0.7747 | 0.9514 |
| NSCLC | CACNA1E | 0.3578 | 1.0212 | 0.0000 | 8.5966 | 5/10 | 0.2687 | 0.9354 |
| NSCLC | KCNA3 | 0.1077 | 0.0757 | 0.0000 | 52.0344 | 5/22 | 0.0855 | 0.1801 |
| NSCLC | TMEM150C | 0.5022 | 0.9044 | 0.0000 | 3.5687 | 11/22 | 0.4356 | 0.6046 |
| NSCLC | STOML3 | 0.7572 | 0.3613 | 0.0000 | 1.2348 | 1/11 | 0.6298 | 1.0828 |
| NSCLC | PIEZO2 | 1.0087 | 0.0491 | 0.0000 | 5.2936 | 4/12 | 0.6816 | 1.2450 |

The SCLC pooled folds are stable to dropping any single library: with one
library removed, the pooled KCNN4 fold stays within 1.3702 and 2.8122, and the
pooled PIEZO1 fold within 2.8094 and 6.2977. A pooled number that does not move
is not necessarily wrong, but here it is stable *and* unrepresentative, because
it is a contrast between libraries rather than a contrast within one. The
NSCLC row is the control that shows the difference: its pooled fold is close to
its per-library median, and its leave-one-out range brackets it.

## 7. What this changes

1. **The SCLC / KCa3.1 arm is closed on the measurement, not on the window.**
   Within a tumour, the state does not over-express KCa3.1 in 9 of 12 relapsed
   SCLC libraries. The gate review's SCLC/KCNN4 projection does not describe
   any individual tumour, and the arm it was carrying is not real.
2. **SCLC / PIEZO1 survives as a marker but not as an established readout.**
   The channel is on in the state in 11 of 14 libraries -- the published
   finding holds -- but the readout clears the programme's own threshold in 4
   of 14, because most relapsed-SCLC tumours carry too little state.
3. **NSCLC / KCa3.1 is the programme's readout.** Every MRD library clears K3 at
   the operating point, the per-patient AUCs run from 0.9491 to 0.9991, and the
   pooled fold is representative of the individual libraries.
4. **The programme has one readout, not three.** Every downstream design
   question -- panel size, read depth, the gate, the cohort -- is now a
   question about EGFR-mutant NSCLC.

## 8. Limitations

- **The projection layer is conditional on an unmeasured counterfactual.** The
  MRD-positive non-relapser arm's state fraction has never been measured in
  this repository; the sweep in section 3 gives the band, and for several SCLC
  libraries the verdict moves inside it.
- **Folds from fewer than 30 state cells are not stable estimates.** They are
  reported with their cell counts and flagged as unstable in the artefact.
- **The measurement layer is a correlation, not a mechanism.** It says the
  state-bearing cells express the channel differently from the surrounding
  tumour, in the same patient, at the same time. It does not say the channel
  carries the state.
- **The gate review's published numbers stand.** They are the pooled
  projection, and the gate review artefact remains their record. This document
  adds a per-tumour layer and qualifies how they may be read.
- **No clinical claim.** Every number is a measurement on a public deposit, or
  a simulation output informed by those measurements.

## 9. Reproducing

```bash
python scripts/per_library_folds.py
python scripts/per_patient_audit.py --patients 800
```

The first script recomputes the per-library folds and state fractions from the
raw count matrices, and checks them against the published state-expression
artefacts. The second runs the projection for each library over the full grid
and checks its pooled control against the gate review. Every number in this
document is checked against the artefacts in CI.
