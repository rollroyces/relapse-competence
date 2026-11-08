# What the measured state enrichment means for a plasma assay

**Audit ID:** `plasma-readability-2026-11`
**Date of run:** 2026-11-08
**Inputs:** `results/gse299684/state_expression.json`, `results/gse353299/state_expression.json`
**Reproduce:** `python scripts/plasma_readability.py --patients 800`
**Artefact:** `results/plasma_readability/plasma_readability.json`

---

## 1. The gap this closes

The two state-resolved audits measured something about **cells in tissue**: the
relapse-competent population over-expresses ion channels relative to the
surrounding tumour. The programme's clinical path is a **plasma** assay, and
plasma integrates over every tumour cell in the circulation. A per-cell
enrichment is not the quantity that decides whether a channel is readable in
blood — and the simulator had been carrying an *assumed* electrical fold and an
*assumed* state fraction ever since D1.

This audit replaces both assumptions with measurements, for both diseases, and
re-runs the channel allocation sweep.

## 2. Two metrics, and they are not interchangeable

| Metric | What it governs |
|---|---|
| **Detection rate** — the fraction of cells with at least one transcript | a per-cell or tissue readout |
| **Abundance fold** — mean expression in counts per 10,000 | the bulk plasma signal |

They can disagree, and in one case they do. In EGFR-mutant NSCLC, PIEZO1 is
detected in 44.1% of state cells against 35.6% of the surrounding tumour — a
detection ratio of 1.24 — but the mean expression is 0.2310 against 0.2273
log-units, an **abundance fold of 0.84**. More state cells express PIEZO1 at
one or two counts; the average amount of PIEZO1 per cell is unchanged. For a
plasma assay, which sums transcripts over the tumour population, that is
**no state signal at all** — and the simulation confirms it (enrichment AUC
0.466, which is chance).

## 3. The measured parameters

| Dataset | State | Channel | Abundance fold, state vs tumour | State fraction | Bulk elevation |
|---|---|---|---:|---:|---:|
| SCLC | YAP1+ | KCNN4 | 2.554 | 0.104 (pooled) | 1.162 |
| SCLC | YAP1+ | PIEZO1 | 3.363 | 0.104 (pooled) | 1.246 |
| NSCLC | KRT17+ | KCNN4 | 3.698 | 0.392 (median, MRD) | **2.057** |
| NSCLC | KRT17+ | PIEZO1 | 0.839 | 0.392 (median, MRD) | 1.000 |
| *simulator's own assumption* | — | — | *3.000* | *0.250* | *1.750* |

The bulk elevation of a tumour with state fraction *f* whose state cells carry
the channel *d* times more than the rest is `(1 − f) + f·d`, i.e.
`1 + f·(d − 1)`, times the signal of a state-free tumour.

## 4. The simulator, re-run with the measured values

Channel allocation sweep at the recommended operating point (200,000× depth,
200 loci, 25% electrical allocation), 800 patients per arm. Only the two
parameters under test change; everything else is the simulator's default.

| Configuration | Bulk elevation | Enrichment AUC within MRD+ | MRD sensitivity | PPV within MRD+ |
|---|---:|---:|---:|---:|
| **Control** — the simulator's assumption | 1.750 | **0.9312** | 0.9256 | 0.7037 |
| SCLC, KCNN4 measured | 1.162 | 0.7065 | 0.9311 | 0.7046 |
| SCLC, PIEZO1 measured | 1.246 | 0.6945 | 0.9440 | 0.7495 |
| **NSCLC, KCNN4 measured** | 2.057 | **0.9929** | 0.9470 | 0.7382 |
| NSCLC, PIEZO1 measured | 1.000 | 0.4658 | 0.9400 | 0.7217 |

The simulator's fold parameter cannot be negative, so the NSCLC-PIEZO1 row is
run at fold 0 — the closest expressible value to the measured one. The
measured bulk elevation of 0.937 is the quantity that matters; the sweep row
shows what the readout does with no state signal at all.

**The control reproduces D1's published row exactly** — 0.9312, 0.9256 and
0.7037 against the same three numbers in
`results/channel_allocation_200k.json` — so every difference in the other rows
is attributable to the measured parameters and not to the re-run.

## 5. What this changes

1. **D1's headline enrichment AUC of 0.85–0.95 is not a single number; it is
   a disease- and channel-specific quantity.** With the measured parameters it
   is **0.993 in EGFR-mutant NSCLC** (where KCa3.1 carries the marking) and
   **0.70 in relapsed SCLC**. The published figure happens to be close to the
   NSCLC case and well above the SCLC one, because the simulator's assumed
   state fraction (0.25) is 2.4 times the measured SCLC fraction (0.104).
2. **The programme's readout is a biomarker, not a therapy, and it is
   strongest exactly where the drug window is worst.** The channel that reads
   the state in NSCLC lung (KCa3.1) is the channel the D0 window audit
   rejected for a systemic drug. A readout does not need a therapeutic window;
   a drug does. These are two different questions and the programme has been
   running them together.
3. **A channel can be a good tissue marker and a null plasma marker.** PIEZO1
   in NSCLC is the case: 1.24× on detection, 0.84× on abundance, 0.466 AUC on
   the simulated plasma readout. Any panel design that picks channels on
   detection rate in tissue would pick it wrongly.

## 6. Limitations

- **The plasma marker is not a single gene.** In a real assay the electrical
  channel is a bulk methylation or signature readout, not the transcript of
  one gene. This calculation assumes the signature's behaviour in state cells
  follows the measured gene's — the most favourable assumption available, since
  a signature aggregates several loci.
- **The refinement PPV of 1.000 is a known model artefact**, not a finding: the
  simulator gives persistent patients a 900-day doubling time and relapsing
  patients 60 days, so refinement separates them perfectly by construction. It
  is quoted here only because the artefact makes the column uninformative.
- **The SCLC state fraction is pooled** across libraries, because that dataset
  has no treatment timepoint; the NSCLC figure is a per-library median at the
  residual-disease timepoint. They are not the same statistic.
- **The mapping from a per-cell fold to the simulator's parameter assumes the
  state is uniformly distributed through the tumour.** Real tumours are
  mosaics, and the state fraction is measured per biopsy, not per cell.
- **Two diseases, two state definitions.** Neither is the programme's final
  population, and the channels differ.
- **No clinical claim.** Every number here is a simulation output informed by
  public measurements.

## 7. Reproducing

```bash
python scripts/plasma_readability.py --patients 800
```

The run takes a few minutes. Every number in this document is in
`results/plasma_readability/plasma_readability.json`.
