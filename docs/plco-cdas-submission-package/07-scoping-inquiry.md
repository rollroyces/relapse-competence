# Scoping inquiry to CDAS — the paste-ready version

**One action, two messages.** Send these before the proposal: the answer
decides whether the EEMS biospecimen route — four to six months — and the
assay budget are worth pursuing at all.

**Route:** `https://cdas.cancer.gov/contact/` — the form in the page body.
**Not the form in the footer:** that one posts the e-mail address to
`public.govdelivery.com` and signs the sender up to the NCI newsletter.
They are separate forms on the same page; use the one with *Your Email
Address*, *Select a Subject*, *Select a Topic* and *Message*.

**Send two messages, not one.** The form has a single Topic, and CDAS state
that a message is forwarded to the party best able to answer it. The two
questions below are answered by different parties, so one message with one
topic would leave half of it unanswered. The two messages below are split by
topic, and each is short.

---

## 1. The form, field by field

| Form field | What to do |
|---|---|
| **Your Email Address** | `roycelam@umich.edu` — required, and CDAS forwards the message to it, so it has to be one you read |
| **Select a Subject** | **PLCO** — required, and it is the only subject that routes the message to the PLCO team |
| **Select a Topic** | Message A: **Data Access/Availability**. Message B: **Biospecimen Availability** |
| **Message** | the block for that message, copied in full |
| the box next to *Your Email Address* but with no label | **leave it empty** |
| the other box with no label | **leave it empty** |

**About the two unlabelled boxes.** They are anti-spam traps: the one named
`name` sits in a container whose class is `antispam1`, and both are skipped
when tabbing through the form, so a person never reaches them. If one of them
carries a value the submission looks automated and may be discarded without a
reply. Do not fill in your name there — put it in the message.

## 2. Message A — data availability

Subject: **PLCO** · Topic: **Data Access/Availability** · Message:

<!-- BEGIN MESSAGE A -->
Dear CDAS team,

I am preparing a data-only project proposal for PLCO and would like to confirm the availability of one specific subset before submitting, so that the proposal requests only what exists.

The project would test whether a bulk transcript measurement of two ion channels (KCNN4 and PIEZO1) in serial plasma separates PLCO participants who are diagnosed with lung cancer from matched participants who are not. The analysis is pre-specified and the code is public. I would request serial plasma at screening visits, matched participants, and the clinical data needed to align each blood draw with diagnosis, treatment and mortality.

Before submitting, could you tell me, for PLCO participants diagnosed with lung cancer:

1. How many have plasma available from more than one screening visit, and how many from a single visit only?

2. How many of those have a diagnosis date that can be released in a Limited Data Set, and are matched participants who were not diagnosed with lung cancer available on the same basis?

3. Is the visit date of each blood draw available, so that each plasma sample can be aligned to the clinical timeline?

A count of participants rather than a file listing would be enough for me to size the request and the assays.

Thank you for your help.

Royce Lam
roycelam@umich.edu
<!-- END MESSAGE A -->

## 3. Message B — biospecimen availability

Subject: **PLCO** · Topic: **Biospecimen Availability** · Message:

<!-- BEGIN MESSAGE B -->
Dear CDAS team,

I am preparing a data-only project proposal for PLCO, and I am also scoping the separate biospecimen route that would give me access to the plasma aliquots. Before I draft the EEMS preliminary application, two questions:

1. For PLCO participants diagnosed with lung cancer, how many have primary tumour tissue archived and available with the study data?

2. Is a request for PLCO lung-cancer tumour tissue made through the EEMS preliminary application, and are the deadlines for the coming period published?

The project would use the tissue only to determine what fraction of tumours express the ion channels the plasma assay reads, so that the assay design can carry a tumour-expression gate rather than assume one.

A count of participants rather than a file listing would be enough.

Thank you for your help.

Royce Lam
roycelam@umich.edu
<!-- END MESSAGE B -->

## 4. Before you send

- **Both messages are plain text.** The field is a plain textarea; markdown
  will not render, and asterisks around a word look like noise.
- **The limit is 10,000 characters** per message. Both messages here are
  well inside it.
- **The fields are filled.** The name, the e-mail address and the form's own
  e-mail field carry `Royce Lam` and `roycelam@umich.edu`. The department
  and institution were left out of the sign-off; the institutional domain
  identifies the institution, and adding the department would give CDAS one
  more route to the right person. If you want it, it is one line:
  `Royce Lam — [department], University of Michigan`.
- **Do not paste the proposal.** This is a scope question and commits to
  nothing; it needs no CDAS account, no signature and no Signing Official.
  The proposal is a separate document and goes through the route in
  [`06-submission-runbook.md`](06-submission-runbook.md).
- **Expect the answer to change what you request.** If question 1 in message
  A comes back "one visit only" for most participants, the design has to
  change: a single pre-diagnosis draw cannot support a serial-plasma
  readout, and the proposal should say so rather than ask for what is not
  there.

## 5. Which question decides what

| Answer | What it changes |
|---|---|
| A1 — serial plasma from more than one visit | whether the proposal can ask for a serial readout at all |
| A2 — diagnosis dates in a Limited Data Set | whether the lead-time analysis is possible; the DTUA is what permits it |
| A3 — visit dates of the draws | whether each plasma can be aligned to the clinical timeline |
| B1 — archived primary tumour | whether the tumour-expression gate can be measured, and how many tumours the assay would have to run on |
| B2 — the EEMS route and its deadlines | whether the 4–6 month biospecimen route is worth starting, and when it has to start |
