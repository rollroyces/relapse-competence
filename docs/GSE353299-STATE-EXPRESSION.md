# GSE353299 — does the electrical reading cross to EGFR-mutant NSCLC?

**Audit ID:** `gse353299-state-expression-2026-11`
**Date of run:** 2026-11-08
**Dataset:** GSE353299 — 25 single-cell libraries of EGFR-mutant lung adenocarcinoma, public (deposited 2026-11-06)
**Reproduce:** `python scripts/download_gse353299.py && python scripts/gse353299_state_expression.py`
**Machine-readable artefact:** `results/gse353299/state_expression.json`

---

## 1. The question

[GSE299684-STATE-EXPRESSION.md](GSE299684-STATE-EXPRESSION.md) established
that the relapse-competent state of **relapsed SCLC** is electrically marked:
PIEZO1 in 39% of state cells against 6% of the surrounding tumour, KCa3.1 in
31% against 9%. But the programme's target is lung **adenocarcinoma**, and its
risk register lists *"the state is not present in NSCLC (only SCLC)"* as a
Medium-likelihood, High-impact risk.

This dataset tests the hypothesis in the right disease, with a state defined
by a completely different gene:

> In EGFR-mutant NSCLC, does an independently-defined drug-tolerant persister
> population show the same electrical marking?

**Short answer: yes, but the channel that carries it is not the same one.**
KCa3.1 marks the state in NSCLC lung at 2.97× — where it did **not** mark it
in SCLC lung. Piezo1 marks it, but at 1.24× rather than 6.91×, weakly enough
that the result depends on how the state is called. **This forces a correction
to a conclusion the SCLC analysis had drawn**, and §6 states it.

---

## 2. The dataset

Twenty-five libraries of EGFR-mutant lung adenocarcinoma, collected at three
clinical timepoints:

| Timepoint | Libraries | Malignant cells | KRT17+ fraction of malignant (per-library median) |
|---|---:|---:|---:|
| `treatment_naive` — treatment naive | 11 | 4,069 | **0.125** (0.00–0.44) |
| `osi_mrd` — osimertinib, minimal residual disease | 7 | 3,115 | **0.392** (0.28–0.65) |
| `osi_progression` — osimertinib, progression | 6 | 2,655 | **0.101** (0.01–0.93) |
| `progression` — progression, regimen unspecified | 1 | 879 | **0.488** |

The per-library median is quoted rather than the pooled figure on purpose:
pooled, the osimertinib-progression group reads 0.491 because one library holds
1,238 of that group's 1,304 KRT17+ cells. Pooling a heavy-tailed group and
quoting the result is the mistake the SCLC analysis was caught for.

87,628 cells passed QC; 10,718 were called malignant, with 42,096 T/NK cells,
13,202 myeloid, 17,536 B/plasma, 8,965 fibroblasts and 3,121 endothelial — so
the immune context needed for a state-to-immune comparison is present.

**The source of the state definition.** The paper is not yet indexed: the
deposit is dated 2026-11-06 and PubMed and Europe PMC have no record, so the
paper's own methods could not be consulted. The GEO record is the source used
here, and it states the study's own dichotomy plainly: the series summary says
the study was designed to *"quantify the number of KRT17+ and KRT17- cells"*,
and the title calls them a *"keratin 17+ aberrant basaloid drug tolerant
persister population"*. The state is therefore KRT17+ cells, and it is
**orthogonal to the hypothesis**: KRT17 is a keratin, and the channels under
test are an ion channel and a mechanosensitive channel.

---

## 3. The state call, and how it was validated

The KRT17+ population is not taken on trust. The dataset's own title says the
population is *aberrant basaloid*, so the basaloid programme (KRT5, KRT6A,
KRT14, KRT15) is checked to be co-expressed in the KRT17+ cells. It is, and
strongly:

| State definition | KRT17+ cells | Basaloid programme, state+ | state− | Enriched |
|---|---:|---:|---:|:--:|
| any transcript | 3,978 | 0.444 | 0.051 | yes |
| ≥2 transcripts | 3,526 | 0.489 | 0.054 | yes |
| top decile | 1,072 | 0.919 | 0.117 | yes |

The gate recovers a transcriptionally distinct, basaloid population — the
population the dataset's title names. That is the validation, and it does not
use an ion channel.

**And the population is drug-emergent, on the authors' own data.** Every one of
the seven MRD libraries has a KRT17+ fraction between 0.28 and 0.65, against a
treatment-naive median of 0.125 (range 0.00–0.44). The osimertinib-progression
group is heterogeneous — two libraries at 0.74 and 0.92, four at 0.01–0.10 —
which is reported rather than smoothed.

---

## 4. The electrical result

KRT17+ against KRT17− malignant cells from the same biopsies:

| Channel | Detection: state | Detection: other tumour | Detection: immune | Detection ratio | p (Mann-Whitney) | q (FDR) |
|---|---:|---:|---:|---:|---:|---:|
| **KCNN4** | 0.459 | 0.154 | 0.098 | **2.97** | 1.5e-275 | 1.1e-274 |
| **PIEZO1** | 0.441 | 0.356 | 0.077 | **1.24** | 9.0e-11 | 2.1e-10 |
| PIEZO2 | 0.020 | 0.010 | 0.003 | 1.96 | 3.0e-05 | 4.1e-05 |
| TMEM150C | 0.050 | 0.062 | 0.009 | 0.80 | 5.4e-03 | 6.3e-03 |
| STOML3 | 0.005 | 0.005 | 0.000 | 1.00 | 0.99 | 0.99 |
| CACNA1E | 0.006 | 0.018 | 0.001 | 0.34 | 2.2e-07 | 3.9e-07 |
| KCNA3 | 0.006 | 0.043 | 0.079 | 0.14 | 4.8e-28 | 1.7e-27 |

**KCa3.1 is the channel that marks the state in NSCLC lung.** Its detection
ratio is 2.97, and it is the most robust result in the dataset: leaving out
any one of the 25 patients moves the ratio only within **2.69–3.64**, the
ratio exceeds 1 in **25 of 25** patients, the sign never flips, and the largest
p-value is 3.6e-169.

**Piezo1's marking is real but weak.** Its ratio is 1.24 and it survives
leave-one-patient-out (1.15–1.33, above 1 in 25 of 25, largest p 4.1e-4) — but
under the strictest state definition (top decile) the ratio falls to 1.06 and
the result is not significant. In SCLC, PIEZO1's marking was large (6.91) and
definition-insensitive. **The Piezo1 marking is a SCLC feature that is only
weakly present in NSCLC.**

The other candidates behave as they did in SCLC: KCNA3 is an immune channel
(7.9% of immune cells against 0.6% of state cells, depleted in the state), and
CACNA1E is depleted, consistent with the D0 window audit's finding that it is
not a lung target.

**Not a depth artefact.** The state cells are not harder to sequence: ACTB is
detected in 99.5% of state cells against 95.5% of the other tumour cells, and
EPCAM in 85.8% against 74.1%. The state cells are slightly *more* complex.

---

## 5. Cross-disease comparison

| Channel | SCLC, YAP1+ state (n=27,608 malignant) | NSCLC, KRT17+ state (n=10,718 malignant) | Verdict |
|---|---:|---:|---|
| KCNN4 | 3.64 | **2.97** | carries over |
| PIEZO1 | **6.91** | 1.24 | much weaker, definition-sensitive |
| PIEZO2 | 0.48 | 1.96 | direction flips |
| TMEM150C | 0.76 | 0.80 | depleted in both |
| CACNA1E | 0.89 | 0.34 | not a lung target in either |
| KCNA3 | 0.54 | 0.14 | immune channel in both |
| STOML3 | 0.04 | 1.00 | null in NSCLC |

The two state definitions are different genes in different diseases, so this is
not a replication of one population — it is the same hypothesis tested on an
independently defined population in the disease the programme is about. The
asymmetry is itself the finding: **the electrical channel that marks a
drug-tolerant persister population is disease-specific.**

---

## 6. What this corrects

The SCLC report closed the KCa3.1 arm for the lung indication, on the
grounds that *"the state does not express KCNN4 more than the surrounding lung
tumour"*, citing the SCLC lung detection ratios of 0.92, 0.00 and 0.37.

**That conclusion was drawn from one disease and does not hold in the other.**
In EGFR-mutant NSCLC lung, the state expresses KCNN4 2.97× more than the
surrounding tumour, in 25 of 25 patients. The corrected statement is:

> The state's KCa3.1 expression is disease-specific: absent in relapsed SCLC
> lung, present in EGFR-mutant NSCLC lung. The KCa3.1 drug arm is therefore
> **not** closed on expression grounds in NSCLC.

What does not change is the window audit. D0 measured lung KCNN4 expression at
12× below minor salivary gland, the gene to be loss-of-function intolerant
(LOEUF 0.515), and Open Targets to carry on-target neurological and cardiac
liabilities. So the arm's difficulty moves from *"the target is not there"* to
*"the target is there and the window is not"* — which is a different problem
with a different solution space (tumour-directed delivery, or a local
modality), and a weaker reason to stop.

**The D0 window verdict and the SCLC measurement both stand as written.** They
are measurements; this is a measurement that does not agree with one of their
implications, and the implication is the thing that changes.

---

## 7. Limitations

- **The state definitions are not the same population.** YAP1+ in relapsed
  SCLC; KRT17+ in EGFR-mutant NSCLC. Cross-disease agreement is agreement of
  a *hypothesis*, not of a cell type.
- **The paper could not be read.** The deposit is dated 2026-11-06 and is not
  yet indexed, so the authors' own markers, thresholds and caveats are
  unknown. The KRT17+ definition and the basaloid validation come from the
  GEO record.
- **EGFR-mutant disease is a specific population.** These are all EGFR
  mutant; the programme's target population is broader.
- **No lineage and no plasma.** Both datasets are tissue.
- **The Piezo1 result is definition-sensitive** in this dataset, so it should
  not be quoted without the sweep.
- **7.6% of the state cells express the pan-immune gene** (against 5.2% of the
  other malignant calls), so there is some contamination; it would bias the
  result towards immune expression, which would understate rather than
  overstate the tumour-specific enrichment.
- **No clinical claim.** Every number here is a simulation-independent but
  observational measurement on public data.

---

## 8. Reproducing

```bash
python scripts/download_gse353299.py --outdir data/gse353299
python scripts/gse353299_state_expression.py --datadir data/gse353299 --outdir results/gse353299
```

The download is about 790 MB and the analysis about ten seconds. The raw
matrices are not committed; every number in this document is in
`results/gse353299/state_expression.json`.

---

**Bottom line.** The electrical reading of a drug-tolerant persister
population crosses into EGFR-mutant NSCLC — through KCa3.1, 2.97× and in 25 of
25 patients — where it had failed in relapsed SCLC lung. Piezo1 crosses only
weakly. The programme's conclusion about KCa3.1 has to be re-opened on the
expression question and closed on the window question instead, and the
persister population's own emergence with drug exposure is visible in the
authors' data without any of this.
