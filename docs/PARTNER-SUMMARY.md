# The relapse-competent state as an electrical readout: what is measured, projected and simulated

**One page, written so that you can check it.** Every number below is in one
of three columns, and the column is the claim. The programme's own kill
conditions are listed with their status, including the ones that went against
it. Nothing here has been submitted to any repository or company; the analysis
is public and the code is in the repository linked at the end.

The question: the drug-tolerant tumour state is marked by an ion channel.
Can that marking be read in blood, cheaply, in the pre-diagnosis window?

---

## 1. MEASURED — public single-cell deposits, this programme's code, no model

| Quantity | Value | Where |
|---|---|---|
| KCa3.1 elevation in the state, EGFR-mutant lung adenocarcinoma | **2.97×** (KRT17+ drug-tolerant persisters vs the surrounding tumour), p = 1.5e-275 | GSE353299 — 25 libraries, 87,628 cells, state defined independently of the channel |
| The marking is carried within an individual patient's tumour | **20 of 23** EGFR-mutant NSCLC libraries with within-tumour KCa3.1 fold above 1 | GSE353299, per library |
| Residual-disease libraries clearing the programme's own threshold | **7 of 7** | GSE353299 |
| The same marking in relapsed small-cell lung cancer | **does not hold** — Piezo1 6.91× there, KCa3.1 not | GSE299684 |
| Pooled vs per-patient | recomputed per library, the **SCLC readout does not survive**; the EGFR-mutant NSCLC readout does | per-patient audit |

## 2. PROJECTED — a model over the measured inputs above

| Quantity | Value | What it assumes |
|---|---|---|
| Bulk-plasma AUC, published statistic | **0.9929** (NSCLC/KCNN4) at 200,000× / 200 loci | the plasma pool has **no leukocyte compartment** — an assumption that does not hold |
| The same, with a realistic leukocyte compartment | **0.0053** — it inverts | KCa3.1 is expressed in immune cells, so the channel locus carries a large leukocyte background |
| Best reference-corrected AUC over the whole searched space | **0.5815** (depth 200,000–20,000,000, 5–50 reference loci) | still below the programme's own 0.65 bar |
| Ceiling for any bulk statistic | 0.5111 with a perfect tumour-cell oracle | — |
| Per-tumour projection | a band, not a point | the state fraction of MRD-positive patients who do **not** relapse has never been measured |

## 3. SIMULATED — a statistic that has never been applied to real plasma

| Quantity | Value | What is assumed |
|---|---|---|
| Attributed (per-molecule) AUC, NSCLC/KCNN4 | **0.9091** against a 0.65 bar | every participant has an informative position |
| The same, state matched away | **0.5170** — chance, so it measures the state and not the burden | the control that separates the two |
| At a 1% attribution rate | 0.7848 — still clears the bar | a 1% informative-position rate |
| With depth | 0.8841 at 2,000,000×, 0.9047 at 20,000,000× | depth cannot buy the attribution rate |
| Applicability rate 50% / 70% / 90% | 0.9098 / 0.8900 / 0.9105 | the statistic is computed over the applicable subset only |
| SCLC / KCNN4 and SCLC / PIEZO1 | 0.5373 and 0.5404 — chance | the attributed statistic does not rescue SCLC |

## 4. KILL CONDITIONS THAT HAVE FIRED

| # | Condition | Status | Fires for |
|---|---|---|---|
| K1 | the readout carries no information beyond tumour burden (AUC ≤ 0.6) | **FIRED** | NSCLC / PIEZO1 |
| K3 | the state cannot be inferred from plasma at an affordable read budget (AUC ≤ 0.65) | **FIRED** | the published statistic, all three state candidates |
| K4 | every candidate target has an unacceptable therapeutic window | **FIRED** | systemic delivery |
| K2 | the state is not present, or not relapse-associated, in lung | not evaluable | — |
| K5 | suppressing the state does not reduce relapse competence | not evaluable | — |

**K3 firing is why the programme changed statistic.** The attributed statistic
in §3 exists because the published one failed.

## 5. THE ASSAY, AND WHAT A PILOT WOULD HAVE TO SETTLE

200 loci at 200,000×: a 150-locus mutation panel (the participant's own
tumour cfDNA fraction, the MRD flag), 38 channel positions, and 12 leukocyte
reference positions — with 50 of the 200 loci, 25% of the read budget, on the
electrical channel. Attribution is **per molecule**: a channel-transcript read
counts only if it carries the tumour's own shift of a germline position, which
is why it needs a germline sample and the matched tumour. The specification
carries six stop rules; the first (S1) requires at least 70% of participants
with a measurable tumour cfDNA fraction to have an informative position, and
**that rate has never been measured**. It is the first thing a pilot has to
establish, and it is why ten tubes of feasibility material cannot settle the
readout.

## 6. WHAT I AM ASKING FOR

A ten-tube feasibility pilot, and not a stratum: is cell-free RNA recoverable
and sequenceable from this archive at all, and does what is recoverable decay
with the age of the specimen and the temperature it was held at. Ten is not
enough to estimate a recovery rate and I am not asking for one. Ten cannot
settle the readout. What it settles is whether the material is there.

I am not asking for partnership, exclusivity, intellectual property,
authorship, or a commitment. The full protocol, the analysis plan and the
stop rules are written down in advance and will be sent before anything is
requested or ordered.

## 7. DISCLOSURE

The programme's reference early-detection assay is PanSeer. Its DNA
methylation work was funded by Singlera Genomics; thirteen of its authors are
Singlera employees, two are board members, three are inventors on a Singlera
patent (US62/657,544) covering the library preparation, and one (Kun Zhang) is
a co-founder, equity holder and paid consultant, with UC San Diego managing
those arrangements. Its analysis code is public, at
`github.com/ncomms-20-10056-t/ncomms-20-10056-t`. This is a disclosure
rather than an objection: the measurement here is a channel transcript in
cell-free RNA, not methylation in cell-free DNA, and it is orthogonal.

My own position: no institutional appointment, no employer, no funding
attached to this work, no competing interest in any result. NIH's Cancer Data
Access System requires the person requesting a PLCO data-access proposal to be
part of the institution that submits it, which is why the request is addressed
to a company and not to a department.

---

*Sources and verification dates: `docs/GATE-REVIEW.md`,
`docs/LOCALISATION-AUDIT.md`, `docs/PER-PATIENT-AUDIT.md`,
`docs/GSE353299-STATE-EXPRESSION.md`, `docs/PLASMA-ASSAY-SPECIFICATION.md`,
`docs/DATA-ACCESS-APPLICATIONS.md` §2.4.*
