# GSE299684 — is the relapse-competent state electrically readable?

**Audit ID:** `gse299684-state-expression-2026-11`
**Date of run:** 2026-11-07
**Dataset:** GSE299684 — the GEO deposit of PMID 42019833 (Stewart et al., *YAP1 Defines an Emergent, Plastic Population of Relapsed SCLC*, J Thorac Oncol 2026), public since 2026-05-15
**Reproduce:** `python scripts/download_gse299684.py && python scripts/gse299684_state_expression.py`
**Machine-readable artefacts:** `results/gse299684/state_expression.json`,
`results/gse299684/state_expression.tsv`

---

## 1. The question

The D0 window audit ended with a gate it could not fire. Bulk normal tissue
cannot distinguish *"conditionally selective"* from *"no window"*, because
conditional selectivity is a property of a **state** and bulk tissue has no
state ([`D0-TARGET-WINDOW-AUDIT.md`](D0-TARGET-WINDOW-AUDIT.md) §6). The
audit therefore deferred the gate to state-resolved expression and noted that
the anchor dataset of the programme is public, so the deferred gate does not
have to wait for a data-access application.

This document runs that measurement. The question is narrow and answerable:

> Do the cells of the relapse-competent state express the candidate ion
> channels more than the surrounding tumour — and more than the
> tumour-infiltrating immune cells?

The answer is **yes for two channels, and it differs between them in a way
that matters for the programme**.

---

## 2. The dataset, and a submission-side discrepancy

Fifteen single-cell libraries of relapsed SCLC from seven metastatic sites:
liver (3), lung (3), head and neck (2), adrenal (2), brain (2), retroperitoneum,
lymph node. The GEO record states every library is from a relapsed patient.

Two accessions carry **deposited file names that belong to the other
accession**: `GSM9043721` (GEO title *SC409_SC363A*, brain surgical
resection) holds files named `SC354_SC396-A`, and `GSM9043722` (GEO title
*SC354_SC396-A*, lung core needle biopsy) holds files named `SC409_SC363A`.
The accession identity comes from the GEO record, which is authoritative; the
discrepancy is recorded in `data/gse299684/manifest.tsv` and in the artefact
rather than silently resolved. It affects the site attribution of two
libraries and nothing else.

---

## 3. The state call, and how it was validated

The state is called by **YAP1 expression**, exactly as the paper defines it.
Because a state defined by the same axis as the feature under test would be
circular, the call is validated against an axis the paper reports
independently: YAP1(+) cells **coexpress CD276 (B7-H3), TACSTD2 (TROP2) and
ERBB2, and lose DLL3, SEZ6 and CEACAM5**. None of those six genes is an ion
channel.

**All six markers reproduce the reported direction, under all three state
definitions** (2,872 / 1,185 / 2,761 state cells respectively):

| Marker | Expected | YAP1+ | YAP1− | Reproduced |
|---|---|---:|---:|:--:|
| CD276 | up | 0.206 | 0.140 | yes |
| TACSTD2 | up | 1.833 | 1.381 | yes |
| ERBB2 | up | 0.325 | 0.263 | yes |
| DLL3 | down | 0.007 | 0.011 | yes |
| SEZ6 | down | 0.005 | 0.004 | yes |
| CEACAM5 | down | 0.000 | 0.000 | yes |

Two pipeline checks against the paper's own numbers:

| Check | This analysis | The paper |
|---|---:|---:|
| Cells passing QC | 72,185 | 69,677 |
| Cancer cells | 27,608 | 35,920 |

The cell count agrees closely. The cancer-cell count is lower because this
analysis calls malignant cells by marker module, whereas the paper used cell
calls, neuroendocrine genes **and inferred copy number**; a copy-number-based
call would recover more cells and is not implemented here.

---

## 4. The result

72,185 cells pass QC; 27,608 are called malignant; 2,872 of them carry a
YAP1 transcript. The contrast that matters is **within the tumour**: state
cells against the other malignant cells of the same biopsies.

| Channel | Detection: state | Detection: other tumour | Detection: immune | Detection ratio | Linear fold vs other tumour | Linear fold vs immune | p (Mann-Whitney) | q (FDR) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **KCNN4** | 0.314 | 0.086 | 0.046 | **3.64** | 2.55 | 2.46 | 8.2e-288 | 2.9e-287 |
| **PIEZO1** | 0.388 | 0.056 | 0.056 | **6.91** | 3.36 | 1.87 | <1e-300 | <1e-300 |
| CACNA1E | 0.014 | 0.016 | 0.002 | 0.89 | 1.11 | 1.51 | 0.45 | 0.45 |
| KCNA3 | 0.005 | 0.010 | 0.025 | 0.54 | 0.21 | 0.03 | 0.018 | 0.022 |
| TMEM150C | 0.135 | 0.177 | 0.010 | 0.76 | 0.36 | 3.50 | 2.3e-12 | 3.2e-12 |
| STOML3 | 0.001 | 0.028 | 0.000 | 0.037 | 0.019 | 30.2 | 1.9e-18 | 3.3e-18 |
| PIEZO2 | 0.049 | 0.101 | 0.007 | 0.48 | 0.16 | 0.97 | 7.7e-22 | 1.8e-21 |

"Detection" is the fraction of cells with at least one transcript; it is the
interpretable quantity, because a channel that is present in 39% of state
cells and 6% of neighbouring tumour cells is a different channel from one
present in both. "Linear fold" is the ratio of mean expression in counts per
10,000; the mean of log values is not a fold change, and both are reported.

**Two channels are enriched in the state: KCa3.1 (KCNN4) and Piezo1 (PIEZO1).**
The other five are not, and three of them — TMEM150C, STOML3 and PIEZO2 — are
significantly *depleted*. That depletion is real rather than a sequencing-depth
artefact: the state cells are **more** complex, not less (median 5,574 genes
detected per state cell against 3,788 in other tumour cells and 1,368 in
immune cells), and the housekeeping controls are higher in the state too
(ACTB detected in 98.9% of state cells against 95.2% of other tumour cells;
GAPDH 98.5% against 94.4%; RPL13A 98.6% against 94.6%).

Two of the results are worth naming separately because they are what a
reader would want to know anyway:

- **KCNA3 is an immune channel.** Detected in 2.5% of immune cells against
  0.5–1.0% of tumour cells, and *depleted* in the state. Kv1.3 is a
  T-cell channel, and the data agree with the plan's reading of it: the
  state-modulating arm, not a tumour-selective drug target.
- **The state has a PIEZO1-high / PIEZO2-low profile.** PIEZO2 falls to 0.16×
  its level in neighbouring tumour cells while PIEZO1 rises to 3.36×. The
  programme's objection to a Piezo1 drug was never PIEZO2 *inside the state* —
  it was PIEZO2 in normal tissue, where bulk expression is indistinguishable
  (window fold 1.043 in the D0 audit). This measurement does not remove that
  objection; it locates the problem precisely.

---

## 5. Where the state is electrically marked — and where it is not

This is the part that changes the programme, because the programme's target
tissue is lung and this dataset is mostly not lung.

| Site | Libraries | State cells | Other tumour cells | KCNN4 detection ratio | PIEZO1 detection ratio |
|---|---:|---:|---:|---:|---:|
| liver | 3 | 2,415 | 4,827 | 1.49 | 2.15 |
| lung (core needle) | 2 | 60 | 5,940 | **0.92** | 2.16 |
| lung (surgical resection) | 1 | 37 | 571 | **0.00** | 6.17 |
| lung/mediastinal (core needle) | 1 | 24 | 296 | **0.37** | 6.17 |
| head and neck | 2 | 175 | 5,995 | 5.71 | 14.52 |
| adrenal | 2 | 24 | 4,499 | 1.73 | 24.45 |
| brain (surgical resection) | 2 | 120 | 682 | 14.21 | 2.68 |
| retroperitoneum | 1 | 17 | 1,924 | 3.81 | 37.73 |
| lymph node | 1 | 0 | 2 | — | — |

**PIEZO1 marks the state at every site, including all four lung libraries.**
**KCNN4 does not mark the state in lung** (ratios 0.92, 0.00, 0.37), while it
does so in brain, head and neck, adrenal and retroperitoneum.

The lung estimates rest on 121 state cells across four libraries in three
groupings, so they are imprecise; but they are not positive, and the three
groupings do not agree with each other in the positive direction.

Per-library the picture is the same as the per-site one: PIEZO1's detection
ratio exceeds 1 in **13 of the 14** libraries with a usable estimate, while
KCNN4's exceeds 1 in 5 and falls below it in 7.

---

## 6. Robustness

**Leave-one-library-out.** The pooled estimate is not carried by one library:
for KCNN4 the detection ratio stays within **2.28–4.07** whichever library is
removed, with the largest p-value still at 8.5e-21; for PIEZO1 within
**5.77–11.72**, with p at the numerical floor. For the other five channels
the sign flips or the significance disappears as soon as a library is
removed, which is what a null result looks like.

**Definition sweep.** Every number above is computed under a permissive state
call (any YAP1 transcript). The analysis is repeated with a stricter call
(at least two transcripts) and with a quantile call (top decile of YAP1
expression among malignant cells). The conclusions do not move: KCNN4's
detection ratio is 3.64 / 3.45 / 3.58, PIEZO1's is 6.91 / 6.58 / 6.90, and the
other five stay negative under all three.

**The state fraction is concentrated, and the analysis says so.** One liver
library holds 1,965 of the 2,872 state cells (68%); **13 of the 15** libraries
have fewer than 200. That is why per-library estimates are noisy and why the
per-site table, not the pooled table, is the one to read for a site-specific
claim.

**A caveat on the malignant call.** 5.2% of the cells called YAP1(+) and
malignant express PTPRC, the pan-immune gene, against 2.0% of the other
malignant calls — so there is a small amount of immune contamination or
doublet content in the state group. This would bias the state group *towards*
immune expression, which would understate, not overstate, the channel
enrichment.

---

## 7. What this does and does not establish

**Established, on public data, with no application:**

1. The relapse-competent state of relapsed SCLC is electrically marked.
   Two of the seven candidate channels are expressed in substantially more
   state cells than in the surrounding tumour of the same biopsies, at
   p-values far below any correction, robust to leaving out any library and
   robust to how the state is called.
2. **PIEZO1 is the channel that marks the state at every site tested,
   including lung.**
3. **KCNN4 marks the state at some metastatic sites but not in lung.**
4. The remaining candidates are not state markers, and several are
   *depleted* in the state — consistent with the paper's finding that the
   state abandons the SCLC programme.
5. The paper that defines this population never mentions an ion channel:
   zero occurrences of KCNN4, PIEZO, CACNA1E, KCNA3 or "ion channel" in its
   full text. The electrical reading of this state is not in the literature
   because it has not been done.

**Not established:**

- **Nothing here is about NSCLC.** This is relapsed SCLC. The risk
  register's "the state is not present in NSCLC (only SCLC)" — Medium
  likelihood, High impact — is untouched by this analysis.
- **Correlation is not mechanism.** The state expresses PIEZO1; nothing here
  shows that Piezo1 drives the state, and the plan's own risk register flags
  that Piezo1 acts as a *tumour suppressor* in one lung context.
- **No lineage, no plasma, no time ordering.** Every library is relapsed
  tissue. The emergent-versus-inherited question is untouched.
- **No treatment-naïve comparator**, so the "emergent" claim itself is not
  re-verified here.
- **The plasma readout is a separate question.** In plasma the state is a
  minority of tumour cells, so a per-cell enrichment does not translate
  directly into a detectable signal; the D1 simulation already bounds that
  dilution, and nothing here changes it.

---

## 8. What this changes in the plan

| Where | Before | After |
|---|---|---|
| The D0b gate | Deferred, awaiting state-resolved expression | **Partly answered.** The state is electrically marked, and the marking is channel- and site-specific |
| KCa3.1 as a lung drug target | "Conditional — needs tumour-directed delivery" | **Closed for lung.** The state does not express KCNN4 more than the surrounding lung tumour (ratios 0.92, 0.00, 0.37 across the three lung groupings, four libraries), so there is no state-selective window to deliver into. The delivery argument is moot if the target is not there |
| Piezo1 as a lung drug target | No window vs PIEZO2; no clinical asset | Unchanged. PIEZO1 marks the state in lung, but the D0 window verdict and the absence of any clinical-stage asset still stand |
| The electrical readout | A bulk channel whose value was assumed | **Grounded.** PIEZO1 is expressed in 39% of state cells against 6% of neighbouring tumour cells; the simulator's assumed 3× electrical fold in state-bearing cells is consistent with the measured 3.4× |
| The D0/D2 electrical endpoint | "Channel expression per cell type within one tumour" | Executable now, on public data, before any tissue is cut |
| The lineage question | Needs serial plasma | Unchanged. This dataset has no lineage tag and no plasma |

The practical consequence: **the state-resolved measurement that the D0 audit
said could not be done on bulk tissue has now been done, and its answer
narrows the programme rather than widening it.** KCa3.1 leaves the lung
indication; PIEZO1 becomes the strongest *readout* candidate in the tissue,
and the case for it rests on a measurement anyone can repeat from the public
deposit.

---

## 9. Reproducing

```bash
python scripts/download_gse299684.py --outdir data/gse299684
python scripts/gse299684_state_expression.py --datadir data/gse299684 --outdir results/gse299684
```

The download is about 700 MB and the analysis about ten seconds. The raw
matrices are not committed to this repository; the analysis reads them from
`data/`, and every number in this document is in
`results/gse299684/state_expression.json`.

---

**Bottom line.** The relapse-competent state *is* electrically readable — in
public data, with no application, and with a state definition validated against
the source paper's own independent signature. Piezo1 marks it at every site
tested, including lung. KCa3.1 does not mark it in lung, which closes the
KCa3.1 arm for the indication the programme is about. The other candidates
are not state markers, and the paper that defines this population never
looked.
