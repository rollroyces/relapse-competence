# The question put to a laboratory: is KCNN4 instructive, or a passenger?

**Status:** pre-registered. Not yet run.
**Companion:** [`KCNN4-DRIVER-OR-PASSENGER.md`](KCNN4-DRIVER-OR-PASSENGER.md)
carries the public-data measurement this is built on.
**Artefact of that measurement:**
`results/driver_passenger_audit/driver_passenger_audit.json`

This document is written to be quoted. It states what is already known, what
remains open, the experiment that would settle it, and what each outcome
means for the programme. It exists because a request to a collaborator that
does not carry a specific question, a specific prediction, and a stated
consequence for each answer is a request for attention, and attention is the
only thing a stranger's e-mail can buy.

---

## 1. What is already known, and what that changes

The programme's readout rests on an ion channel marking the relapse-competent
state — a drug-tolerant subpopulation of tumour cells — in a way that a
screening cohort's plasma could carry. KCa3.1 (KCNN4) is the channel that
survives the programme's own audits: the state over-expresses it 3.7-fold in
EGFR-mutant lung adenocarcinoma, the marking is carried inside an individual
patient's tumour in 20 of 23 libraries and in all 7 residual-disease
libraries, and it does not hold in relapsed small-cell lung cancer, where
the state is too rare to read.

The public single-cell data also says something that has to be said before
anybody is asked anything. In EGFR-mutant NSCLC state cells, KCNN4's
expression **co-allocates with the basaloid programme** beyond what cell
complexity explains — 6.8 null standard deviations, in the cohort where a
gene inside the programme score is found at 29.3 and a housekeeping gene
stays flat at -0.5. So in the cells where the readout works, the channel is
**not demonstrably an axis of its own**.

That does not settle the question, and the reason is the interesting part.
Co-expression is equally compatible with two stories:

- **passenger.** KCNN4 is a transcriptional output of the basaloid programme,
  downstream of the state. The electrical framing is decoration on a
  transcriptional marker.
- **shared upstream cause.** The channel and the programme are both
  downstream of something else — a bioelectric state — and co-expression is
  exactly what that would look like.

Public data cannot separate these. Only a perturbation can.

**What this changes about the invitation.** The invitation cannot be the claim
that the electrical mark is a separate axis; this repository's own data does
not support that claim for the one marker that works, and a collaborator who
did the arithmetic would find it in an afternoon. What the invitation can be
is this question, which is sharper and which the collaborator's own field
has the tools to answer.

## 2. The propositions

| | Proposition | Status |
|---|---|---|
| **P1** | KCNN4's elevation in the relapse-competent state is a transcriptional output of the basaloid programme, not a separate electrical axis | **Supported in cells, direction not settled.** Co-allocation is established; membership is not |
| **P2** | If P1 is false, the channel and the programme share an upstream cause, and the channel's plasma readout can report the state *earlier* than the programme's own transcripts can | **Untested.** This is what the plasma arm's premise rests on |
| **P3** | The state's KCNN4 elevation is not explained by copy-number amplification at the KCNN4 locus | **Untested.** A local copy-number estimate would settle it from the same public data |

## 3. The experiment

### 3.1 The system

A tumour cell model that carries the relapse-competent state, so that the
state can be destroyed by an intervention and not merely correlated with it.

**This is the first practical obstacle, and it has not been solved.** The
state has been characterised in patient tumour deposits; this repository has
not identified a cell line or a patient-derived model that carries it. The
closest available system is the RORB-loss organoid dataset (GSE325242), whose
deposit carries no gene annotation and so cannot be measured — the same
reason K5 is recorded as not evaluable. Establishing a model that carries the
state is therefore part of the question, not a preliminary to it, and it
should be scoped before anyone is asked to take it on.

### 3.2 The perturbation

Knock KCNN4 down in state-carrying cells — by CRISPR interference, by a
degron, or by a channel blocker with a characterised on-target effect — and
measure:

1. **The state programme.** KRT17 and the basaloid markers KRT5, KRT6A,
   KRT14 and KRT15, by transcript.
2. **The drug-tolerant phenotype** itself: survival under the therapy the
   state is defined by, and the persister fraction.
3. **The channel**, to confirm the perturbation did what it claimed: KCNN4
   transcript, and the channel's own activity.
4. **A specificity arm**, because a knockdown that kills the cell proves
   nothing: the same perturbation in cells that do not carry the state, and
   in a non-targeting control.

### 3.3 The predictions, stated so that either can fail

| Outcome | Reading | What it does to the programme |
|---|---|---|
| Knocking KCNN4 down **collapses** the programme and the drug-tolerant phenotype | The channel is **instructive**. P1 is false, P2 holds | The plasma assay keeps its premise: the channel reports an upstream state the downstream programme has not yet shown. The EEMS application proceeds on the specification as written |
| Knocking KCNN4 down **leaves both intact**, and the knockdown is confirmed effective | The channel is a **passenger**. P1 is true | A plasma panel measuring the programme's own keratins would carry the same information and more of it — they are far more abundant. The "electrical readout" has to be re-stated as a transcriptional readout that happens to use a channel transcript, or dropped |
| The perturbation **reduces the phenotype but not the programme**, or neither | Mixed or off-target | The channel is coupled to something upstream of both, or the perturbation is not doing what it claims. The specificity arm distinguishes these |

### 3.4 What would make the answer uninterpretable

- A perturbation that reduces viability in both arms is not a test of the
  state; it is a cytotoxic drug.
- A state-carrying model that does not actually carry the state in the
  conditions of the experiment.
- A knockdown with no transcript-level confirmation.
- Any comparison that does not include cells that do not carry the state, in
  which case "the programme collapsed" cannot be separated from "the cell
  died".

## 4. Why the timing is what it is

The PLCO EEMS application period closes on **18 February**, and the
preliminary application — which is rolling, but whose acceptance is what lets
a final application be filed by that date — has to be in first. A proposal
built on the wrong premise is worse than a late one: the programme's claim to
be about an electrical state rather than a transcriptional one is the whole
reason the plasma arm is worth a screening cohort, and the audit above shows
that claim is conditional.

So the order is:

1. **Now.** The public-data side is done: the coupling is measured, the
   controls are calibrated, the proposition is written down. What remains
   public-data work is P3, the local copy-number estimate at the KCNN4 locus,
   which uses the same cached deposits and would remove one more passenger
   route.
2. **Before the laboratory question is put to anyone.** Find or build a
   model that carries the state, and decide whether the perturbation is
   feasible in it.
3. **Then, and only then.** The invitation goes out, carrying this document's
   propositions, the measurement they rest on, and the decision table above.
4. **In parallel, and independently of all of it.** The CDAS eligibility
   question, the institutional PI, the Signing Official, and the Taizhou
   direct request. None of them waits on the perturbation, and the deadline
   does not move for it.

## 5. What this document does not claim

- It does not claim the channel is a passenger. It claims the direction is
  open and the experiment that closes it is named.
- It does not claim the programme is over. Both branches have a stated next
  step, and one of them is the programme as designed.
- It does not claim the plasma arm cannot work. It claims that the arm's
  premise is conditional on P2, and that the condition should be tested
  while there is still time to act on it.
