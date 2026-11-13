# Invitation to a laboratory: the KCNN4 question

**Status:** draft, not sent. No one has received this.
**Held rather than sent, and the reason is the host conversation.** This
letter asks a specific laboratory about a specific system: whether
perturbing KCa3.1 in a model that carries the relapse-competent state would
show whether the channel is an axis or a passenger. No such model has been
identified — the closest available perturbation system, GSE325242, cannot be
measured at all, from its deposit and from its authors' repository alike
([`CHANNEL-TRANSFERABILITY.md`](CHANNEL-TRANSFERABILITY.md) §2) — so the
letter would arrive without a named laboratory, and a question about a
system nobody has is not one a stranger can act on. It is therefore held
behind [`HOST-INVITATION.md`](HOST-INVITATION.md): a laboratory carrying the
state is most likely inside the host's own institution, and one letter to
one person is a smaller ask than two. The propositions, the perturbation and
the decision table below are ready to travel as an enclosure.
**Distinct from** [`HOST-INVITATION.md`](HOST-INVITATION.md), which asks a
professor to be the institutional Principal Investigator for a data-access
application. That letter asks for a signature; this one asks for a
measurement.
**Carries:** the propositions in
[`PERTURBATION-QUESTION.md`](PERTURBATION-QUESTION.md), resting on
[`KCNN4-DRIVER-OR-PASSENGER.md`](KCNN4-DRIVER-OR-PASSENGER.md) and
[`KCNN4-COPY-NUMBER.md`](KCNN4-COPY-NUMBER.md).

---

## 1. Before you send — five things to set

1. **`[LAB]`** — the recipient's name and the salutation.
2. **Why this person.** One line, and it has to be true: a shared paper, a
   seminar, a field they work in, a model they use. A question of this kind
   lands differently on someone whose lab already has the right system than
   on someone whose field is merely adjacent.
3. **Whether the last paragraph goes in.** It says that you hold no
   institutional appointment. It is there because the arrangement depends on
   it — the application side needs an institution, the science does not — and
   because a collaborator who discovers it in the fourth exchange has wasted
   an exchange. Reword it if you prefer, but dropping it does not remove the
   question, it only moves it later.
4. **What to attach.** The three documents below. They are the substance: a
   reader who wants to check the arithmetic can.
5. **Do not send it while the scoping answers are outstanding.** The letter
   tells the recipient that the programme intends to apply for PLCO
   biospecimens. If the scope answers come back with nothing usable, the
   letter is a question about a programme that does not exist. Wait for the
   answer; the Feb 18 deadline is real but a letter sent into a programme
   that has just collapsed is worse than a late one.

## 2. The letter

Plain text, ready to paste. The subject line is separate.

**Subject:** A falsifiable question about KCa3.1 and the relapse-competent state

<!-- BEGIN LABORATORY LETTER -->
Dear Professor [LAB],

I would like to put a specific question to you, and to find out whether it is worth your lab's time before either of us commits to anything.

The background. The relapse-competent state is a drug-tolerant subpopulation of tumour cells. Its definition is transcriptional — the paper that defines the population never mentions an ion channel — but across three public single-cell deposits the state carries an unmistakable electrical signature: it over-expresses the potassium channel KCa3.1, KCNN4, 3.7-fold in EGFR-mutant lung adenocarcinoma; the marking is carried inside an individual patient's tumour in 20 of 23 libraries and in all 7 residual-disease libraries; and it does not hold in relapsed small-cell lung cancer, where the state is too rare to read. We want to read that state in plasma, in a screening cohort, because it is the only setting where enough people are followed long enough for a lead time to mean anything.

What we have measured, and why the question is still open. Inside the state cells, KCNN4's expression tracks the strength of the transcriptional programme that defines the state — the coupling is 6.8 times the null spread in a cohort where the housekeeping control stays flat. So the channel does not appear to be an axis of its own; it travels with the programme. That admits two readings. Either KCNN4 is a transcriptional output of the programme, a passenger, and reading it in plasma would add nothing that reading the programme's own keratins would not give more of; or the channel and the programme share an upstream cause, and the channel reports an upstream state the downstream programme has not yet shown — which is the entire reason a plasma assay would be worth building. We have ruled out the broad copy-number explanations for the elevation: the region around KCNN4 rises 1.05-fold while the gene itself rises 3.5-fold, and the locus shows no significant excess among three hundred control loci. What remains would be an event affecting the gene alone, which transcript counts cannot distinguish from transcriptional regulation and which would need DNA.

The question. In a tumour cell model that carries the state, knock KCNN4 down — CRISPR interference, a degron, or a channel blocker with a characterised on-target effect — and ask whether the state programme and the drug-tolerant phenotype follow it down. If they do, the channel is instructive. If they do not, it is a passenger, and the premise of our plasma assay has to be rewritten. The specificity arm matters as much as the perturbation: a knockdown that only reduces viability has not tested the state, and a comparison without cells that do not carry the state cannot separate "the programme collapsed" from "the cell died".

Two things I want to be straight about. First, we have not identified a cell line or a patient-derived model that carries the relapse-competent state; the closest available system cannot be measured, because its deposit carries no gene annotation. Establishing one is part of the work rather than a preliminary to it, and it is the part I most want your judgement about. Second, I hold no institutional appointment, so the application side — a biospecimen application through the National Cancer Institute's EEMS programme — is being handled separately and is not what this message is about. What I am asking is whether the science is worth doing in your hands.

What I am asking for. Not a commitment. A twenty-minute conversation about whether the perturbation is feasible in the models you work with, and what it would take to try. If the answer is that it is not worth doing, that is a complete answer and I will not follow up. If it is worth doing, I will send the full specification before anything is started.

With thanks for reading this far.

Royce Lam
roycelam@umich.edu
<!-- END LABORATORY LETTER -->

## 3. What to attach

| Document | What it gives the reader |
|---|---|
| [`PERTURBATION-QUESTION.md`](PERTURBATION-QUESTION.md) | The propositions P1 to P3, the system, the perturbation and its arms, the predictions written so that either can fail, the decision table, and the four things that would make the answer uninterpretable |
| [`KCNN4-DRIVER-OR-PASSENGER.md`](KCNN4-DRIVER-OR-PASSENGER.md) | The measurement the propositions rest on: the coupling inside state cells, with the controls that calibrate it, and the cohort that was set aside because its controls failed |
| [`KCNN4-COPY-NUMBER.md`](KCNN4-COPY-NUMBER.md) | The copy-number audit: what it excludes, what it cannot reach, and why the remainder needs DNA rather than an argument |

Attach the first at minimum. The other two are what make the first checkable.

## 4. The decision table, in the form the letter refers to

| Outcome of knocking KCNN4 down | Reading | What it does to the programme |
|---|---|---|
| The state programme and the drug-tolerant phenotype **collapse** | The channel is **instructive**: P1 is false, P2 holds | The plasma assay keeps its premise — the channel reports an upstream state the downstream programme has not yet shown — and the application proceeds on the specification as written |
| Both are **unchanged**, with the knockdown confirmed effective | The channel is a **passenger**: P1 is true | A plasma panel measuring the programme's own keratins would carry the same information and more of it, so the readout has to be re-stated as a transcriptional measurement that happens to use a channel transcript, or dropped |
| The phenotype falls but the programme does not, or neither moves | Mixed, or the perturbation is not doing what it claims | The specificity arm distinguishes these, and the channel is coupled to something upstream of both |

## 5. What this letter deliberately does not do

- It does not ask for a commitment. The ask is a conversation, and it is
  small enough to be worth twenty minutes.
- It does not promise a result, a paper, or a position.
- It does not hide the obstacle. A collaborator who is told the state-carrying
  model has not been found can decide whether finding one is interesting;
  one who is told later has wasted a meeting.
- It does not claim the channel is electrical in a way the data does not
  support. It says the channel travels with the programme and asks which of
  the two readings is right, because that is the question with the
  consequence.
