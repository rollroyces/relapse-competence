# GSE138474 — the treatment-naive SCLC comparator, and why it cannot answer the question

**Audit ID:** `gse138474-state-expression-2026-11`
**Date of run:** 2026-11-12
**Dataset:** GSE138474 — the GEO deposit of Stewart et al., *Single-cell analyses
reveal increasing intratumoral heterogeneity as an essential component of
treatment resistance in small cell lung cancer*, Cancer Res 2021
**Reproduce:** `python scripts/gse138474_state_expression.py`
**Machine-readable artefacts:** `results/gse138474/state_expression.json`,
`results/gse138474/state_expression.tsv`

---

## 1. The question

The gate review has two conditions it cannot test, and it names the way one
of them could be tested:

> **K2** | A primary-versus-relapsed tissue comparison showing no
> state-associated methylation delta, **or a treatment-naive SCLC cohort
> showing the state is already present before therapy**

and, in the same table, the reason the condition is untested:

> For relapsed SCLC there is no treatment-naive comparator at all.

This document supplies that comparator and asks the question the gate names.
**The answer is that the comparator cannot answer it, and the reason is
measurable rather than rhetorical: the cohort does not carry the state in
either arm.** That is a result about a cohort, not about the biology, and the
difference matters: K2 stays *not evaluable*, and the gap it covers is now
documented and closed with evidence rather than left open.

---

## 2. The dataset

GSE138474 is a SuperSeries of two sub-series (GSE138267 and GSE138418) holding
25 single-cell libraries with a deposited matrix. Every library is
*Homo sapiens* on GPL11154, and every one carries the treatment label in its
GEO record:

| Arm | Libraries | What the label means |
|---|---:|---|
| untreated | 13 | the model was never given a cytotoxic drug |
| vehicle-treated | 2 | the model was given vehicle |
| relapsed | 7 | the model relapsed after cisplatin, talazoparib or prexasertib |
| cisplatin, not relapsed (CTC) | 1 | circulating tumour cells, not a solid-tissue sample |
| untreated (CTC) | 1 | as above |
| cisplatin, relapsed (CTC) | 1 | as above |

Twenty-two libraries are solid tissue — a patient-derived SCLC model sampled
in a flank — and three are a circulating-tumour-cell series. Several models
appear in more than one arm, so the contrast is within-model as well as
between-arm: **SC4** contributes three untreated libraries and five relapsed
ones, **SC53** a vehicle and a cisplatin-relapsed library, and **SC68** a
vehicle and a cisplatin-relapsed library.

This is the cohort the gate review was missing, and it is the closest public
SCLC comparator that carries a treatment label. It is not a lung biopsy, and
the document says so wherever the distinction could carry a conclusion.

---

## 3. The ruler, and the reduction

**The ruler is imported, not re-implemented.** The state call, the cell-type
modules, the state-validation signature, the channel statistics and the
multiple-testing correction are loaded from
`scripts/gse299684_state_expression.py`, so the relapsed human cohort and
this cohort are measured on one definition and a difference between them
cannot be a difference in the definition. The state is **YAP1** expression,
as the state paper defines it, and the call is validated against an axis the
paper reports independently — YAP1(+) cells co-express CD276 (B7-H3),
TACSTD2 (TROP2) and ERBB2, and lose DLL3, SEZ6 and CEACAM5. None of those six
genes is an ion channel, so a channel cannot define the state it is then
tested in.

**Three state definitions are swept, not fixed.** "YAP1 detected" is
permissive; a cell with one transcript is not the same as a cell with fifty.
The three definitions are run — any detection, at least two transcripts, and
the top decile of expression — and every number below is reported under each,
so that no conclusion rests on one cut.

**The matrices are streamed, not stored.** Each library is a tarball whose
matrix is about 250 MB and twenty million non-zeros. The machine this ran on
had 1.1 GB of free disk, so the deposit is read over the network and reduced
in memory: only the genes the analysis needs are kept, together with the
per-cell library size, detected-gene count and mitochondrial count that the
quality filter needs. Nothing is written to disk except one small
per-library summary, which makes the run resumable.

**The deposit is not uniform, and the differences are recorded rather than
resolved silently.**

| Library | What the deposit does |
|---|---|
| `GSM4104163`, `GSM4104164`, `GSM4104165`, `GSM4104166` | ship the matrix as a **dense tab-separated table**, one row per gene and one column per cell, with no MatrixMarket header |
| `GSM4104165` | the deposited file is `GSM4104165_SC68_veh.LB19002.matrix.tar.gz` while the GEO title is *SC68. LB19002* — and the file name recorded in the GEO metadata matches neither |
| `GSM4851437`, `GSM4851438` | prefix the triplet members with the sample name (`SC53cis.genes.tsv`) rather than shipping them bare |

The file names are read from each sample's own directory rather than assumed
from its title, because in this deposit the title, the metadata and the file
on disk do not agree. The resolved names are kept in a manifest, so a re-run
does not ask the server again — GEO refuses directory listings after a burst
of requests, and this deposit is a burst. The matrix shape is checked against
the gene and barcode lists before it is read, so a transposed table is
refused rather than silently misread, and the dense tables are read as
dense tables rather than being mistaken for sparse ones.

Three more submission-side defects of the kind this programme has hit twice
before, in GSE299684 and GSE325242. The deposit has to be checked rather
than assumed.

---

## 4. The measurement

The state fraction is the YAP1(+) share of the malignant cells in a library,
under the primary definition (at least one YAP1 transcript).

| Arm | Libraries | Median state fraction | Range |
|---|---:|---:|---|
| untreated | 13 | **0.00193** | 0.00006 – 0.01187 |
| vehicle-treated | 2 | 0.00254 | 0.00000 – 0.00509 |
| relapsed | 7 | **0.00239** | 0.00000 – 0.00732 |
| untreated or vehicle | 15 | 0.00193 | 0.00000 – 0.01187 |

The untreated and the relapsed arms are indistinguishable: the rank-sum test
on the untreated-or-vehicle libraries against the relapsed ones gives
**p = 0.8051** (15 against 7 libraries). The within-model pairs agree:
**SC4** rises by 0.00042 from before to after (three libraries against five),
**SC53** falls by 0.00001 and **SC68** does not move at all. Nothing here
resembles the rise a relapse-associated state would produce.

The other two definitions agree with the first where they can be read at
all. Requiring at least two YAP1 transcripts puts the untreated and relapsed
medians both at **0.0**. The top-decile definition is **degenerate in every
library**: when the state is this rare the 90th percentile of a mostly-zero
distribution is zero, so the threshold selects every malignant cell and the
state fraction reads 1.0. That is an artefact of the definition and it is
flagged as such in the artefact (`degenerate_zero_threshold`), not reported
as a finding.

For scale, the same state call on the relapsed human cohort
([`GSE299684-STATE-EXPRESSION.md`](GSE299684-STATE-EXPRESSION.md)) gives
2,872 YAP1(+) cells in 27,608 malignant cells — a pooled state fraction of
**0.104**. The relapsed arm of *this* deposit reaches 0.00239, about
**44 times lower**.

---

## 5. The controls

**Depth.** A state that is simply harder to sequence would show fewer
detected genes everywhere, and the state fraction could fall without the
state being absent. The median library here detects **3,246 genes per cell**
in the untreated arm, 3,214 in the vehicle arm and 3,494 in the relapsed arm;
the relapsed human cohort's median is 3,787 genes per cell for YAP1(−) cells
and 5,574 for YAP1(+) cells. The libraries are of comparable depth, so the
low state fraction is not a sequencing-depth artefact. (Two libraries are
much shallower — `GSM4104147` at 456 genes per cell and the three circulating
tumour-cell libraries at 457–619 — and are excluded from the arm medians or
reported separately.)

**The state-validation signature.** The call reproduces the paper's
independent surface-target signature in the libraries where there are enough
YAP1(+) cells to test it: 6 of 6 in the two libraries that reach it, and 2–5
of 6 elsewhere, with the shortfall explained by how few cells the state
contains. Where the state is rare the validation has no power, and the
artefact says so by reporting the count rather than a verdict.

**The housekeeping controls** are carried per library so that a null can be
told apart from a broken pipeline.

**The compartment.** The solid-tissue libraries are 95.9% malignant by cell
count (105,324 of 109,839 cells after quality control), so the
state-to-immune contrast the relapsed cohort could make is not available
here. That contrast is not needed for this question, and it is stated rather
than glossed.

**The circulating-tumour-cell series** holds 624 cells across three
libraries, at 457–619 genes per cell, and is reported separately rather than
pooled into the arms.

---

## 6. The decision

The rule was fixed before the measurement: the state counts as **present
before therapy** if the untreated arm's median per-library state fraction
reaches **half the pooled relapsed-SCLC value measured on GSE299684**, that is
**0.052**.

| | |
|---|---|
| Threshold | 0.052 |
| Untreated arm median | 0.00193 |
| **Verdict on the untreated arm** | **the state is absent before therapy** |
| Relapsed arm median (same deposit) | 0.00239 |
| **Verdict on the cohort** | **not evaluable: the cohort carries the state in neither arm** |

The second verdict is the one that governs, and it is a statement about the
cohort's power rather than a change to the rule. If the relapsed arm of the
same deposit does not carry the state either, then a low untreated value
cannot be read as "absent before therapy": it would have been low before
therapy whether or not the state were relapse-associated. A null from a
cohort that cannot show the effect is not evidence of no effect, and writing
it up as one would be the same mistake the programme has made once already
and corrected — the raw-VAF version of the localisation statistic, which
looked decisive until a matched-state control showed it was measuring
burden.

So **the K2 route is closed with evidence, and K2 remains *not
evaluable*.** What has changed is that the gap is no longer an unsearched
one: the closest public treatment-naive SCLC comparator has been found,
measured on the programme's own ruler, and shown not to carry the state.

---

## 7. What this does and does not settle

**It does not show that the state is not relapse-associated.** It shows that
the one public comparator that could have tested it cannot. The relapsed
human cohort's own evidence — the state at 0.104 in relapsed tissue, at 20 of
23 libraries and 7 of 7 residual-disease libraries — is untouched by this
audit, and the K2 condition remains open on its other route, the
primary-versus-relapsed methylation comparison, which needs a dataset nobody
has identified yet.

**It does not change any published number.** The relapsed cohort's state
fraction, the per-patient audit, the channel measurements and the simulator's
outputs are all as they were.

**It does close the search.** The two open gates of the programme now have
documented reasons for being open:

- **K5** — the closest available perturbation system, the RORB-loss organoid
  dataset GSE325242, is unmeasurable from two independent directions: the
  GEO deposit carries no gene names, and the authors' own analysis
  repository carries code but no data
  ([`CHANNEL-TRANSFERABILITY.md`](CHANNEL-TRANSFERABILITY.md) §2).
- **K2** — the closest available treatment-naive SCLC comparator does not
  carry the state in either arm, so it cannot separate "absent before
  therapy" from "absent in this model system" (this document).

Neither of those is a pass, and neither is a failure. They are the two places
where a public measurement has been tried and the answer has been that the
data cannot carry it — which is what the gate review's own limitation says
about one of them and what the programme now says about both.

---

## 8. Reproducing

```bash
python scripts/gse138474_state_expression.py
```

The script downloads each library from GEO, reduces it in memory and writes
`results/gse138474/state_expression.json` and `results/gse138474/state_expression.tsv`.
The per-library summaries are cached under `data/gse138474/` (not committed),
so a re-run is instant; `--force` re-measures from the network. The
per-library table in the artefact and the TSV are checked against each other
in `tests/test_gse138474_state_expression.py`, and the report's numbers are
checked against the artefact in `scripts/verify_report_consistency.py`.
