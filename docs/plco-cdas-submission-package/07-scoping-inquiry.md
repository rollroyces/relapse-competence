# Scoping inquiry to CDAS — the paste-ready version

**One action, two messages.** Send these before the proposal: the answers
decide whether the EEMS biospecimen route — four to six months — is worth
pursuing at all, and how large a pilot it has to be.

**Route:** `https://cdas.cancer.gov/contact/` — the form in the page body.
**Not the form in the footer:** that one posts the e-mail address to
`public.govdelivery.com` and signs the sender up to the NCI newsletter.
They are separate forms on the same page; use the one with *Your Email
Address*, *Select a Subject*, *Select a Topic* and *Message*.

**Send two messages, not one.** The form has a single Topic, and CDAS state
that a message is forwarded to the party best able to answer it. The clinical
data and the archived material are answered by different parties, so the
questions are split by topic below.

---

## 0. The sending record

Both messages were submitted on **2026-11-11**, from `roycelam@umich.edu`,
through the form in the page body. Each submission came back with the banner
*"Your message was sent successfully. We will respond to your inquiry as
soon as possible."*

| Message | Subject | Topic | Characters | Sent (HKT) |
|---|---|---|---|---|
| A | PLCO | Data Access/Availability | 1152 | 2026-11-11 12:27 |
| B | PLCO | Biospecimen Availability | 1789 | 2026-11-11 12:28 |
| C | PLCO | Data Access/Availability | 2121 | 2026-11-11 16:45 |

Message C is the eligibility question, sent later the same day after CDAS's
own instructions turned out to require an institutional PI; it is in §6.

The character counts are the lengths of the two message blocks below, and
`scripts/verify_report_consistency.py` checks them against those blocks, so
this table cannot drift away from the text that was actually sent.

**There is no inquiry number, and none is recorded here.** The contact form
issues no reference: the only thing it returns is the banner quoted above,
and the reply arrives by e-mail at `roycelam@umich.edu`. If CDAS quotes a
reference in the reply, that belongs with the reply, not here.

## 1. The form, field by field

| Form field | What to do |
|---|---|
| **Your Email Address** | `roycelam@umich.edu` — required, and CDAS forwards the message to it, so it has to be one you read |
| **Select a Subject** | **PLCO** — required, and it is the only subject that routes the message to the PLCO team. Choose it **first**: the topic list is not on the page until a subject has been picked, and it appears with `-------` and the five topics. |
| **Select a Topic** | Message A: **Data Access/Availability**. Message B: **Biospecimen Availability** |
| **Message** | the block for that message, copied in full. The field carries `maxlength="10000"`, so the limit is enforced by the browser as well as by the server. |
| the box next to *Your Email Address* but with no label | **leave it empty** |
| the other box with no label | **leave it empty** |

**About the two unlabelled boxes.** They are anti-spam traps: the one named
`name` sits in a container whose class is `antispam1`, and both are skipped
when tabbing through the form, so a person never reaches them. If one of them
carries a value the submission looks automated and may be discarded without a
reply. Do not fill in your name there — put it in the message.

Read from the live form on 2026-11-11, the two are `id_name` (class
`antispam1`) and `id_phone` (class `antispam2`), both with `tabindex="-1"`.

**The form also renders ten hidden decoy submit buttons.** All of them are
labelled *Send Message*, and they differ only in their `name` and in whether
their class is `antispam1` or `antispam2`; the CSS keeps them out of sight.
The visible button is the one whose class is `antispam3`. Press the visible
one. A submission that arrives with one of the hidden button names in it is
the shape the server is checking for, and it will not be treated as a
message.

## 2. Message A — the clinical data

Subject: **PLCO** · Topic: **Data Access/Availability** · Message:

<!-- BEGIN MESSAGE A -->
Dear CDAS team,

I am preparing a data-only project proposal for PLCO and would like to confirm the availability of one specific subset before submitting, so that the proposal requests only what exists.

The project would test whether a transcript measurement of two ion channels (KCNN4 and PIEZO1) in serial plasma separates PLCO participants who are diagnosed with lung cancer from matched participants who are not. The analysis is pre-specified and the code is public.

Before submitting, could you tell me, for the PLCO lung-cancer stratum:

1. How many participants were diagnosed with lung cancer, and how many matched participants without lung cancer are available on the same basis?

2. How many of those have a diagnosis date that can be released in a Limited Data Set?

3. Is the visit date of each blood draw available, so that each plasma sample can be aligned to the clinical timeline?

4. Are treatment history and mortality with follow-up time available for both groups?

A count of participants rather than a file listing would be enough for me to size the request and the assays.

Thank you for your help.

Royce Lam
roycelam@umich.edu
<!-- END MESSAGE A -->

## 3. Message B — the archived material

Subject: **PLCO** · Topic: **Biospecimen Availability** · Message:

<!-- BEGIN MESSAGE B -->
Dear CDAS team,

I am preparing a data-only project proposal for PLCO, and I am also scoping the separate biospecimen route that would give me access to the plasma aliquots and the matched tumour material. Before I draft the EEMS preliminary application, five questions about the lung-cancer stratum:

1. How many lung-cancer participants have plasma archived, and for how many is it available from more than one screening visit rather than one?

2. How many have primary tumour tissue archived and available with the study data? For how many is the archived tissue the primary tumour, rather than a recurrence or a metastasis?

3. What profiling exists for that tissue: whole-exome sequencing, whole-genome sequencing, or targeted sequencing? If more than one is available, please say which. The answer changes how much somatic information I can use.

4. Is a germline DNA sample available for PLCO participants, or a germline genotype set released with the study data? I need to know which positions are heterozygous in each participant, and which of those their tumour has shifted.

5. Is a request for PLCO lung-cancer tumour tissue and germline DNA made through the EEMS preliminary application, and are the deadlines for the coming period published?

The tumour material would be used in two ways: to measure what fraction of tumours express the ion channels the plasma assay reads, so that the assay design carries a tumour-expression gate rather than assuming one, and to establish each participant's own somatic profile, so that plasma reads can be attributed to the tumour rather than to the white cells that make up most of the circulating nucleic acid.

A count of participants rather than a file listing would be enough.

Thank you for your help.

Royce Lam
roycelam@umich.edu
<!-- END MESSAGE B -->

## 4. Before you send — and the record of what was sent

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
- **Questions 2 to 4 of message B are now required, not optional.** The assay
  specification
  ([`PLASMA-ASSAY-SPECIFICATION.md`](../PLASMA-ASSAY-SPECIFICATION.md))
  attributes the plasma signal to the tumour per molecule, by a heterozygous
  germline SNP that the participant's own tumour shifts. The matched tumour and
  a germline sample are what make that possible, which is why the data
  request carries them as required elements rather than as a convenience.
- **The two blocks above are now the record of what was sent.** They were
  submitted verbatim on 2026-11-11 (see §0). Do not edit them to improve the
  wording: they are the evidence of what CDAS received. If a question has to
  change, that is a new message, and the old one stays as it was.

## 5. Which answer decides what

| Answer | What it changes |
|---|---|
| A1 — lung-cancer and matched comparator counts | the size of the pilot, and whether the comparison is possible at all |
| A2 — diagnosis dates in a Limited Data Set | whether the lead-time analysis is possible; the DTUA is what permits it |
| A3 — visit dates of the draws | whether each plasma can be aligned to the clinical timeline |
| A4 — treatment and mortality | the outcome window for the non-progressing comparator |
| B1 — plasma from more than one visit | whether the proposal can ask for a serial readout at all |
| B2 — archived primary tumour | **required** for the per-molecule attribution and the tumour-expression gate; a count of zero ends the plasma arm |
| B3 — WES or WGS | how much somatic information is available; WES covers coding exons only, which may leave too few informative positions near the channel transcript |
| B4 — germline sample or genotype set | whether each participant's heterozygous positions can be read at all |
| B5 — the EEMS route and its deadlines | whether the 4–6 month biospecimen route is worth starting, and when it has to start |

Three of these answers are decisive on their own. If B2 comes back with no
usable tumour material, the per-molecule attribution has no basis and the
programme's plasma arm cannot be attempted as specified. If B4 comes back
with no germline information, the same is true, because the attribution needs
to know which positions are heterozygous in each participant. And if B3
answers "whole-exome only", the informative positions may be too few near the
channel transcript, which is the condition the specification's first stop rule
is about.

## 6. Message C — the eligibility question

This one is not about the data. It is about who is allowed to ask for it, and
it was found by reading CDAS's own instructions for accessing data on
2026-11-11: the Principal Investigator — the Data Access Requestor — "must be
a permanent employee of your institution at a level equivalent to... an
academic professor... or senior researcher", cannot be "a post-doc, trainee,
or lab technician", and "will register and be responsible for the project,
its submission, renewals and close-out". The Signing Official is likewise
"permanently employed at the institution".

The person writing to CDAS holds no current institutional appointment, so
the question is not academic: the answer decides whether this route is open
at all, and it has to be answered well before the EEMS deadline of Feb 18.

Subject: **PLCO** · Topic: **Data Access/Availability** · Message:

<!-- BEGIN MESSAGE C -->
Dear CDAS team,

I am preparing a data-only project proposal for PLCO and have one eligibility question before I go further.

The instructions for accessing data say that the Principal Investigator, the Data Access Requestor, must be a permanent employee of your institution at a level equivalent to that of an academic professor or a senior researcher, that this individual cannot be a post-doc, trainee or lab technician, and that this individual will register and be responsible for the project, its submission, renewals and close-out. The Signing Official is likewise permanently employed at the institution.

My own situation: I studied at the institution whose e-mail address I am writing from, but I hold no current appointment there and no institutional position at all. I am doing the research myself, and what CDAS requires of the person who submits decides whether this route is open to me, so I would rather ask than have the proposal turned down.

1. Must the Data Access Requestor be a current permanent employee of some institution at professor level or senior-researcher level, with no exception for an individual researcher who holds no institutional appointment?

2. The instructions say the PI will register and that the PI must submit the proposal, while the project overview also says that a proposal may be filled in by someone who is not the PI, for the PI to review and submit. If a professor at an institution is the PI, may that professor register and submit, while I do the work of filling in the fields?

3. For the approved-users list: must every approved user hold a current appointment at the PI's institution, and is an institutional e-mail address at an institution where the person no longer holds an appointment acceptable for that list?

4. If the Data Access Requestor must be a current permanent employee, is there any route by which a researcher without an institutional appointment can take part in a PLCO project, for instance as a collaborator named on a proposal submitted by someone else?

Any of these answers would help. Thank you for your help.

Royce Lam
roycelam@umich.edu
<!-- END MESSAGE C -->

