# Gate review: the programme's own killing conditions, against measured inputs

**Audit ID:** `gate-review-2026-11`
**Date of run:** 2026-11-09
**Reproduce:** `python scripts/gate_review.py --patients 800`
**Artefacts:** `results/gate_review/gate_review.json`,
`results/gate_review/gate_matrix.tsv`

---

## 1. What this document is

The research plan states five conditions under which the programme is dead
([`RESEARCH-PLAN.md`](RESEARCH-PLAN.md) §0). Until now, two of them had never
been evaluated against anything but the simulator's assumptions. The
state-resolved audits replaced those assumptions with measurements — the
per-cell fold of the state over the surrounding tumour, and the state
fraction — and the window audit produced a verdict per candidate target.

This document applies the plan's own conditions to that evidence and writes the
verdicts down. It is deliberately unflattering in two directions:

- a condition that **cannot be evaluated** is recorded as *not evaluable*,
  never as passed;
- a condition that rests on a **model-based projection** rather than a
  measurement says so, and the projection's inputs are stated.

The headline: **three conditions have fired, two cannot yet be tested, and the
one readout that survives is a tissue-level readout, not a plasma one.**

### A qualification added after this document was first written

The projection in this document uses a **pooled** per-cell fold and a **pooled**
state fraction for every simulated patient. Both pooled values are cell-count
weighted, and in the relapsed-SCLC deposit three libraries hold 86.4% of the
state cells while the channel's baseline expression differs by metastatic site
by up to 65-fold. The per-patient audit
([`PER-PATIENT-AUDIT.md`](PER-PATIENT-AUDIT.md)) recomputes both inputs per
library and re-runs the projection for each tumour, and it narrows how the
SCLC rows here may be read:

- the SCLC rows are the pooled projection, and they stand as that;
- per tumour, the SCLC/KCNN4 readout clears K3 in **1 of 12** libraries and the
  SCLC/PIEZO1 readout in **4 of 14**, because the pooled fold is a contrast
  between metastatic sites rather than a contrast within one tumour;
- the NSCLC/KCNN4 readout holds: all **7** MRD libraries clear K3, with per-
  patient AUCs from 0.9491 to 0.9991, and the pooled fold is representative of
  the individual libraries there.

So the programme has **one** established readout — KCa3.1 in EGFR-mutant
NSCLC — not three. The numbers in this document are unchanged; the reading is
narrower.

### A second qualification added after the leukocyte audit

The plasma numbers in this document come from a model whose plasma cfDNA pool
has **no leukocyte compartment**: it is tumour-shed material plus a 1e-6
sequencing-error floor, so the electrical channel's signal is the tumour's
contribution alone. In bulk plasma that is not the case. Most cfDNA is
leukocyte-derived and KCa3.1 is expressed in immune cells, so the channel
locus carries a large leukocyte background and the tumour's state is a small
perturbation on it.

The leukocyte audit ([`LEUKOCYTE-AUDIT.md`](LEUKOCYTE-AUDIT.md)) added that
compartment and re-ran the projection. With a realistic background the
statistic does not degrade, it **inverts**: NSCLC/KCNN4 goes from 0.9929 to
0.0053, and with a perfect tumour-cell oracle it reaches only 0.5111. Across
the whole searched operating space — depth 200,000 to 20,000,000, five to
fifty reference loci — the best reference-corrected AUC is **0.5815** against
K3's 0.65. Nothing in that space clears K3, and deepening the panel a
hundredfold does not change the verdict.

**What this means for the reading of this document.** The AUC column in
section 2's configurations table, the prose in section 3, and the K1 and K3
rows in section 4 describe the review **as it stood before** the leukocyte
compartment existed. The verdicts table in section 2 is the verdict of record:
K3 has fired for all three state candidates. Where the two differ, the
verdicts table governs, and the audit is the document to read for the plasma
arm.

### A third qualification added after the localisation audit

The leukocyte audit searched the space of *background-subtraction* statistics.
The assay specification's own answer is different: per-molecule attribution,
counting the channel-transcript reads that carry an informative tumour
signature. That mechanism had never been simulated, and the leukocyte audit
said so: the projection under localisation was "an argument from the structure
of the statistic rather than a simulated measurement".

The localisation audit ([`LOCALISATION-AUDIT.md`](LOCALISATION-AUDIT.md))
simulated it. A leukocyte-derived channel molecule carries the germline
allele, not the tumour's shift of it, so it is never counted, and the
compartment is removed **by construction** rather than by subtraction. For the
one readout the programme has — KCa3.1 in EGFR-mutant NSCLC — the attributed
statistic clears K1 and K3 at the published operating point (0.9091 against
K3's 0.65), where the bulk statistic inverts to 0.0053.

So **K3's verdict in section 2 stands for the bulk statistic, and the plasma
arm is not dead.** The gate review's own kill condition is not about whether
the state can be read from plasma; it is about whether the programme's
published statistic can read it. A different statistic, which the assay
specification already prescribes, does.

What the localisation audit does not do is measure the attribution rate or
the fraction of participants who have an informative position. Those are the
pilot's to establish, and the specification's first stop rule is about the
second. The audit says the statistic survives across the plausible range of
both, which is a statement about the arithmetic and not about the biology.

## 2. The verdicts

| Condition | What it kills | Status | Fires for |
|---|---|---|---|
| **K1** | The state-specific readout carries no information beyond tumour burden (enrichment AUC ≤ 0.6) | **fired** | every configuration whose channel does not over-express the state — including **NSCLC / PIEZO1** |
| **K2** | The state is not present, or not relapse-associated, in lung (no state-associated methylation delta between primary and relapsed tissue) | **not evaluable** | — |
| **K3** | The state cannot be inferred from plasma at an affordable read budget (enrichment AUC ≤ 0.65 at 200,000× / 200 loci) | **fired** | the same configurations as K1; **none of the three state candidates** |
| **K4** | Every candidate target has an unacceptable therapeutic window | **fired** | — for systemic delivery |
| **K5** | Suppressing the state does not reduce relapse competence in patient-derived models | **not evaluable** | — |

Two of the three K1 firings are the same fact: a channel that does not
over-express the state carries no state information, and no readout can be
built on it. The consequence is not cosmetic.

### The configurations that matter

| Dataset | Channel | Tissue fold | State fraction | Bulk elevation | AUC at 200k× / 200 | K1 | K3 |
|---|---|---:|---:|---:|---:|:--:|:--:|
| NSCLC | **KCNN4** | 3.698 | 0.392 | 2.057 | **0.9929** | pass | pass |
| SCLC | **KCNN4** | 2.554 | 0.104 | 1.162 | 0.7065 | pass | pass |
| SCLC | **PIEZO1** | 3.363 | 0.104 | 1.246 | 0.6945 | pass | pass |
| SCLC | CACNA1E | 1.112 | 0.104 | 1.012 | 0.5727 | **fire** | **fire** |
| NSCLC | PIEZO2 | 1.009 | 0.392 | 1.003 | 0.4930 | **fire** | **fire** |
| NSCLC | PIEZO1 | 0.839 | 0.392 | 0.937 | 0.4658 | **fire** | **fire** |

The three state candidates are the configurations whose channel over-expresses
the state in tissue. **In the projection this table was built from, all three
survive K1 and K3** — that projection has no leukocyte compartment, and the
leukocyte audit overturns it. The configurations that fire are the ones with
nothing to measure. The marginal entries (CACNA1E in SCLC, fold 1.112;
PIEZO2 in NSCLC, fold 1.009) are artefacts of a mechanical threshold —
CACNA1E was ruled out as a lung target at D0 regardless.

These are **pooled** verdicts. Read per tumour, and against the per-patient
audit, the two SCLC candidates do not hold: the channel's within-tumour fold
exceeds 1 in 3 of 12 libraries for SCLC/KCNN4 and 11 of 14 for SCLC/PIEZO1, and
the projection clears K3 in 1 of 12 and 4 of 14 respectively. The NSCLC row is
representative of its individual libraries.

## 3. What follows

This section is the review as it stood **before** the leukocyte compartment
was added to the plasma pool. Where it differs from the verdicts table in
section 2, that table governs; the qualification in section 1 says what
changed and why.

**1. The readout for EGFR-mutant NSCLC is KCa3.1, and PIEZO1 is dead there.**
The NSCLC state does not over-express PIEZO1 (fold 0.839), so the enrichment
AUC is 0.4658 — chance — and both K1 and K3 fire. Had the programme chosen
PIEZO1 as the NSCLC readout on the strength of the SCLC result, **its own kill
conditions would have ended the programme.** The channel that works there is
KCa3.1, at a projected AUC of 0.9929 — a projection with no leukocyte
background, which the leukocyte audit overturned: with a realistic
background the same statistic inverts to 0.0053, and a perfect tumour-cell
oracle reaches only 0.5111.

**2. The relapsed-SCLC readout survives, but only just.** 0.6945 (PIEZO1) and
0.7065 (KCNN4) against K3's 0.65. That margin is thin: the SCLC state
fraction used here is 0.104, pooled over fifteen libraries of seven different
metastatic sites, and a plasma cohort with a lower state fraction would push
the AUC under the threshold. The honest reading is that **the SCLC readout is
not yet established** — it is above the bar on the evidence available, and the
evidence is thin. The per-patient audit makes this quantitative: the readout
clears K3 in 4 of 14 SCLC libraries for PIEZO1 and 1 of 12 for KCNN4, and
KCNN4's within-tumour fold exceeds 1 in 3 of 12 libraries, so the SCLC/KCNN4
candidate does not survive per tumour at all. And with the leukocyte
compartment in the pool, both projections invert to 0.0053.

**3. K4 has fired, so the systemic drug arm is dead.** No candidate channel has
a bulk-tissue therapeutic window: CACNA1E and STOML3 are not lung targets at
all, and KCNN4, PIEZO1, KCNA3, TMEM150C and PIEZO2 all fail the specificity
verdict. KCa3.1's lung expression is 12× below minor salivary gland, the gene
is loss-of-function intolerant (LOEUF 0.515), and on-target neurological and
cardiac liabilities are recorded; Piezo1 has no separation from PIEZO2 (window
fold 0.851) and no clinical-stage asset.

The state-resolved audits supply the one piece of counter-evidence: the state
itself is channel-high in the target tissue for the matched disease and channel
(NSCLC/KCNN4, 2.97× on detection; SCLC/PIEZO1, 6.91×). So **a state-directed
modality is not excluded by the expression evidence** — but it does not exist,
and nothing in this repository builds one.

**4. Two conditions remain untested, so the programme is not dead.** K2 is the
condition that would say the state is not in lung or not relapse-associated, and
the evidence so far points the other way: in EGFR-mutant NSCLC every
minimal-residual-disease library has a KRT17+ fraction between 0.28 and 0.65,
against a treatment-naive pooled fraction of 0.137. That is not the methylation
delta the condition names, and there is no primary-versus-relapsed methylation
comparison in this repository, so it is recorded as not evaluable rather than
passed. For relapsed SCLC there is no treatment-naive comparator at all. K5
needs a perturbation experiment; the closest available system was the
RORB-loss organoid dataset GSE325242, whose deposit carries no gene annotation
and cannot be measured.

## 4. What would change each verdict

| Condition | What would change it |
|---|---|
| **K1** | A measured plasma cohort in which the matched channel separates relapsers from MRD-positive non-relapsers with an enrichment AUC above 0.6. The projection that reached 0.9929 for NSCLC/KCNN4 had no leukocyte compartment, so what a measured cohort would have to beat is the audit's inverted 0.0053 with an oracle ceiling of 0.5111, not 0.9929 |
| **K2** | A primary-versus-relapsed tissue comparison showing no state-associated methylation delta, or a treatment-naive SCLC cohort showing the state is already present before therapy |
| **K3** | A measured plasma cohort in which the matched channel clears AUC 0.65. The projection cleared it at every configuration tested, but only because the pool had no leukocyte compartment; with one, no configuration in the searched space clears it, the best being 0.5815 |
| **K4** | A modality that reaches the state selectively: a state-directed conjugate, a tumour-localised agent, or an allele-selective channel modulator. Bulk-tissue specificity alone will not rescue it |
| **K5** | A patient-derived model in which suppressing the state does **not** reduce relapse competence. No such experiment has been run |

## 5. Limitations

- **K1 and K3 are model-based projections, not plasma measurements.** They are
  the simulator run with the measured per-cell fold and the measured state
  fraction, at 800 patients per arm, with thresholds calibrated on a held-out
  split. A real plasma cohort could move them, and the SCLC margins are small
  enough that it could. **The projection also had no leukocyte compartment**,
  which the leukocyte audit later added; with one, the same statistic inverts
  and K3 fires for all three state candidates. The verdicts table in section 2
  is the current state; the AUC column above is the pre-audit projection.
- **The verdict uses the plan's own operating point**, not the best
  configuration in the grid. A configuration with a handful of MRD-positive
  patients can produce an AUC of 1.0 by chance; the best-in-grid column is
  reported as context only, and several of its values are artefacts of small
  MRD-positive populations.
- **The SCLC state fraction is pooled** over fifteen libraries of seven
  metastatic sites, because that dataset has no treatment timepoint. The
  NSCLC figure is a per-library median at the residual-disease timepoint.
  They are not the same statistic.
- **"Not evaluable" is not "passed".** Two of the five conditions have not been
  tested, and one of them (K5) cannot be tested with public data at all.
- **The pooled inputs do not describe a patient.** The per-cell fold and the
  state fraction here are cell-count weighted. Per tumour, the SCLC rows do not
  hold: see the per-patient audit
  ([`PER-PATIENT-AUDIT.md`](PER-PATIENT-AUDIT.md)) and the qualification in
  section 1. The NSCLC row is representative of its individual libraries.
- **The state candidates are mechanical.** A channel counts as a candidate
  when its measured abundance fold exceeds 1; two entries clear that bar by
  less than 12% and one of them was already ruled out at D0.
- **No clinical claim.** Every number is a simulation output informed by public
  measurements, or a measurement on a public deposit.

## 6. Reproducing

```bash
python scripts/gate_review.py --patients 800
```

The run takes about ten minutes: fourteen configurations, each over the
5,000×/50,000×/200,000×/500,000× depth grid at 50 and 200 loci, with the
measured per-cell fold and state fraction injected. The inputs come from
`results/gse299684/state_expression.json`,
`results/gse353299/state_expression.json` and
`results/d0_window_audit/d0_window_audit.json`; the outputs are
`results/gate_review/gate_review.json` and
`results/gate_review/gate_matrix.tsv`, and every number quoted here is checked
against them in CI.

The per-tumour layer that qualifies the SCLC rows is produced separately:

```bash
python scripts/per_library_folds.py
python scripts/per_patient_audit.py --patients 800
```

which write `results/per_library_folds/` and `results/per_patient_audit/`, and
are documented in [`PER-PATIENT-AUDIT.md`](PER-PATIENT-AUDIT.md). Every number
in that document is checked against its artefacts in CI as well.
