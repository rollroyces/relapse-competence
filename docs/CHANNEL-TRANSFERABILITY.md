# Channel transferability: does the ion-channel readout carry to a third dataset?

**Audit ID:** `channel-transferability-2026-11`
**Date of run:** 2026-11-08
**Datasets:** GSE324849 (executed); GSE325242 (executed to the limit the deposit allows)
**Reproduce:** `python scripts/gse324849_state_expression.py`
**Artefacts:** `results/gse324849/state_expression.json`

---

## 1. The question

Two state-resolved audits found the relapse-competent population to be
electrically marked:

| Dataset | Disease | State | Channel | Abundance fold, state vs tumour |
|---|---|---|---|---:|
| GSE299684 | relapsed SCLC | YAP1+ | PIEZO1 | 3.36 |
| GSE353299 | EGFR-mutant NSCLC | KRT17+ | KCNN4 | 3.70 |

The channel differed between the two, so the honest question is not "is there
an electrical signature" but **"does the readout transfer to a third dataset,
and if not, why?"** This audit answers that with two deposits: the one that
was specified, and the one that could actually carry the measurement.

## 2. GSE325242 — the deposit cannot carry the measurement

GSE325242 ("Transcriptional networks underlying tumour plasticity in
small-cell lung cancer", preprint PPR1330822) was the dataset specified for
this test. It is **mouse** SCLC organoids (`Rbf/fp53f/fRbl2f/f` lines),
profiled on the Parse Biosciences Evercode WT platform after **RORB loss**, and
it is exactly the kind of dataset the question needs: a plasticity axis
(neuroendocrine → Intermediate → nonNE) in SCLC, with the Intermediate state
described by the authors as immunogenic and bipotent.

**The deposit has no gene annotation.** It contains three files:

| File | Contents |
|---|---|
| `GSE325242_count_matrix.mtx.gz` | 74,971 cells × 57,012 genes, 205,520,745 non-zeros, **no gene names** |
| `GSE325242_cell_metadata.csv.gz` | barcodes, wells, per-cell QC counts — no cell-state annotation |
| `GSE325242_sample_barcode_mapping.csv.gz` | sample ↔ well barcode mapping (5 lines × 3 conditions) |

The whole 2.7 GB of decompressed matrix was scanned: **exactly two lines
contain any letter** — the MatrixMarket header and the dimension comment.
There is no gene list in the matrix, no separate annotation file in the
deposit, and every sample record lists `!Sample_supplementary_file_1 = NONE`.
The columns are therefore anonymous, and KCNN4, PIEZO1 and every other gene
are unmeasurable from this deposit. Reconstructing the column order from the
Parse panel would be guesswork, and a wrong mapping would silently produce
plausible-looking numbers, which is the one thing this repository does not do.

**What it would have answered**, had the annotation been deposited: whether the
channels track the loss of the neuroendocrine programme itself — the
general-plasticity reading of the hypothesis, which the two patient datasets
cannot separate from the relapse-state-specific reading.

This is the third submission-side defect in these deposits (after the
file-name swap in GSE299684 and the two file names in GSE299684 that belong to
the other accession): GEO deposits in this programme are not uniformly
self-describing, and the deposit has to be checked rather than assumed.

## 3. GSE324849 — the test that could run

GSE324849 ("Transcription Factor Subtype Governs Response and Resistance to
DLL3-Directed T-Cell Engagement in Small Cell Lung Cancer") profiles a
**human** relapsed SCLC adrenal-gland metastasis (patient 7373) from a patient
treated with **tarlatamab**, the DLL3×CD3 bispecific. The paper's central
finding is that one mode of acquired resistance is *therapeutic selection for a
NEUROD1-high state with concomitant DLL3 downregulation* — a state definition,
and a validation axis, both independent of the ion channels.

1,896 cells passed QC: 424 malignant, 1,449 immune, 23 stromal.

### 3.1 This tumour is ASCL1-subtype, and the state is not in it

| Gene | Detected in malignant | Detected in immune |
|---|---:|---:|
| ASCL1 | **364 / 424** | 63 / 1,449 |
| NEUROD1 | 1 / 424 | 0 / 1,449 |
| POU2F3 | 0 / 424 | 0 / 1,449 |
| DLL3 | 51 / 424 | 4 / 1,449 |
| SYP | 158 / 424 | 25 / 1,449 |

The tumour is an ASCL1-subtype SCLC — which the paper predicts responds best
to tarlatamab, and which is consistent with DLL3 being an ASCL1 transcriptional
target. The paper's NEUROD1-high acquired-resistance population is **not in
this sample**: one cell in 424 expresses NEUROD1 at all. The state-level
contrast is therefore impossible here, and no conclusion is drawn from it.

### 3.2 Neither channel is expressed in this tumour

| Gene | Detected in malignant | Detected in immune |
|---|---:|---:|
| **KCNN4** | **0 / 424** | 130 / 1,449 (9.0%) |
| **PIEZO1** | **0 / 424** | 173 / 1,449 (11.9%) |

Both channels that marked the state in the other two datasets are **completely
absent from this tumour's malignant compartment**, while both are comfortably
detected in the immune compartment of the same library.

This is not a depth artefact. The tumour cells here are *better* covered than
the immune cells: 2,756 genes detected per malignant cell against 2,663 per
immune cell (median), and the tumour's own markers are strong (ASCL1 in 86% of
malignant cells). The channels are simply not on in these cells.

### 3.3 The readout therefore does not transfer — and why that matters

The channel that marked the state in relapsed SCLC (PIEZO1) is absent from
this relapsed SCLC tumour, and the channel that marked the state in NSCLC
(KCNN4) is absent here too. The readout is **not a property of the disease**.

That is a negative result with a design consequence. If the plasma electrical
assay keys on PIEZO1, its tumour-level sensitivity is limited by how many
tumours express PIEZO1 at all — in the 40 tumours measured across the three
datasets, one has neither channel. A plasma assay therefore needs a
**tumour-expression gate** (the way EGFR or PD-L1 status gates a targeted
therapy) or a multi-channel signature, rather than an assumption that the
channel is universal.

The programme already reaches the same conclusion from a different direction:
[D0-TARGET-WINDOW-AUDIT.md](D0-TARGET-WINDOW-AUDIT.md) found that the
tumour's own bulk tissue expression is not informative about the state, and
[PLASMA-READABILITY.md](PLASMA-READABILITY.md) found the plasma consequence
to be disease- and channel-specific. This third dataset adds the
tumour-specific term: **the channel has to be measured in the tumour before
it can be used as a plasma marker.**

## 4. What this does not establish

- **The state contrast is untested here.** One NEUROD1-high cell in 424; the
  paper's resistance state is absent from this sample.
- **One patient, one metastasis.** This is a case report of the dataset, not
  a cohort.
- **A different platform.** 10x GEM-X 5′ rather than the 3′ chemistry of the
  other two datasets. The immune-compartment detection rates are comparable
  (PIEZO1 11.9% here against 5.6% in GSE299684), which argues against a
  depth artefact, but a chemistry difference remains a caveat.
- **The absent channels are not evidence that the channels are irrelevant.**
  They are evidence that they are not universal.
- **No clinical claim.** Every number here is an observation on public data.

## 5. Where this leaves the transferability question

| Question | Answer |
|---|---|
| Is the state electrically marked? | Yes, in the two datasets that have the state: relapsed SCLC (PIEZO1) and EGFR-mutant NSCLC (KCNN4) |
| Does one channel serve both diseases? | **No.** PIEZO1 in SCLC, KCNN4 in NSCLC |
| Is the readout universal across tumours? | **No.** Absent in a third SCLC tumour entirely |
| Is the readout universal across states? | **Untested** — the third dataset has no state population in it |

The programme's own position is now: *the electrical state is real and
measurable, but the channel that carries it is neither disease-specific nor
tumour-specific, and a plasma assay keyed on one channel will miss the
tumours that do not express it.* That is a concrete design requirement, and it
is the kind of thing that only shows up when the same measurement is repeated
in a third place.

## 6. Reproducing

```bash
# GSE324849 (three files, 20 MB)
for f in GSE324849_barcodes.tsv.gz GSE324849_features.tsv.gz GSE324849_matrix.mtx.gz; do
    curl -O "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE324nnn/GSE324849/suppl/$f"
done
python scripts/gse324849_state_expression.py
```

GSE325242's matrices are 626 MB compressed and 2.7 GB uncompressed; the
deposit is not usable for gene-level measurement, as §2 records.
