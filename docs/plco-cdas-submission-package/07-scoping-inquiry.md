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
| D | PLCO | Biospecimen Application Process | 1866 | 2026-11-12 09:11 |

Message C asked about the data route's own eligibility requirement; it is in
§6. Message D, which asks whether an applicant with no institutional
appointment may submit an EEMS application at all, was sent on 2026-11-11 US
Eastern and is in §7. Message E, which asks who may sign the transfer
agreement, is drafted in the same section and **has not been sent**: it is
conditional on the first answer to D.

**The timing, for anyone reading the record.** A, B and C were all sent
outside CDAS's working hours — 23:27, 23:28 and 03:45 US Eastern — so they
were all queued for the same morning. D was sent at 20:11 US Eastern and is
queued for the next one. The form forwards each message by Topic, so D went
to the EEMS programme desk rather than to whoever answers A or C.

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
| **Select a Topic** | Message A: **Data Access/Availability**. Message B: **Biospecimen Availability**. The five topics are `Data Access/Availability`, `Biospecimen Availability`, `Biospecimen Application Process`, `Biospecimen Transfer Agreements` and `Tech Support` (read from the live form on 2026-11-13). **There is a dedicated topic for transfer agreements**, which is where message E would have gone: E asked who may sign the transfer agreement, and it would have been filed under `Biospecimen Transfer Agreements` rather than under `Biospecimen Application Process` |
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
Re-read on 2026-11-13, both were still present and still empty, and the
field ids are `id_email`, `id_subject`, `id_topic` and `id_message`.

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

## 7. Messages D and E — the biospecimen route

These two ask whether the **biospecimen** route is open to an applicant
with no current institutional appointment. They are separate messages because
the form carries one Topic and CDAS forward a message to the party best
able to answer it: who may apply is a question for the EEMS programme, and
who may sign the transfer agreement is a question for the agreements side.
A and B were split for the same reason.

**D was sent on 2026-11-12 09:11 HKT (2026-11-11 US Eastern). E is
drafted and held**, because it is conditional on D's first answer: if an
applicant with no institutional appointment may not apply, the question of
who signs the transfer agreement is not yet a live one.

### Message D — who may apply — sent

Subject: **PLCO** · Topic: **Biospecimen Application Process** · Message:

<!-- BEGIN MESSAGE D -->
Dear CDAS team,

I am preparing a preliminary EEMS application for PLCO and have one eligibility question before I go further.

The application process says that if you have your own source of funding and wish to obtain PLCO biospecimens, you should register with CDAS and begin the EEMS Application, and the policies say the biospecimens resource is available to the entire scientific community. The application asks for the contact information of a Principal Investigator. The separate instructions for accessing PLCO data require that Data Access Requestor to be a permanent employee of the submitting institution at professor level or senior-researcher level, and to be the person who registers and submits.

I do not hold a current institutional appointment: I am not employed by any institution, and the work is self-funded. Before I go further I would like to know how that bears on the biospecimen route.

1. May an applicant who holds no current institutional appointment submit an EEMS preliminary application, provided the funding is their own?

2. If the Principal Investigator named on an EEMS application must be a permanent employee at professor level of some institution, must that institution also be the one that holds the transfer agreement for the specimens, or may the applicant be a member of an investigative team based elsewhere?

3. What does the preliminary application require from an applicant in that position — an institutional e-mail address, a CV, an NIH biosketch, an ethics determination, and if so, from which body?

4. Is there a route by which a researcher without an institutional appointment can take part in a PLCO biospecimen study, whether as the applicant or as a member of the investigative team?

I would rather ask than have an application returned on a formality.

Thank you for your help.

Royce Lam
roycelam@umich.edu
<!-- END MESSAGE D -->

### Message E — who may sign the transfer agreement — drafted, not sent

Subject: **PLCO** · Topic: **Biospecimen Transfer Agreements** · Message:

<!-- BEGIN MESSAGE E -->
Dear CDAS team,

I am preparing an EEMS application for PLCO and have a question about the transfer agreement that goes with it.

The instructions say that recipients of PLCO samples must sign and abide by an NCI Material Transfer Agreement, that extramural investigators are contacted by a member of the NCI Technology Transfer Center to start that process, and that no agreement is needed for projects conducted by NIH employees. My situation is that I would be the applicant for the preliminary application while holding no current institutional appointment, so there is no institution that employs me and could be the counterparty.

1. Can the Material Transfer Agreement for the shipment of specimens be executed with an institution other than the applicant's employer — for example the laboratory that will run the assays, or a host institution that agrees to carry the project?

2. Must the institution that executes the Material Transfer Agreement be the same one that hosts the Principal Investigator named on the application?

3. Whose institutional e-mail address must be used for the CDAS account and for the approved-user list in that arrangement, and must each approved user hold an appointment at the institution that executes the agreement?

Any light you can shed on this before I put an application in would be much appreciated.

Thank you for your help.

Royce Lam
roycelam@umich.edu
<!-- END MESSAGE E -->

### What the answers decide

| Answer | What it settles |
|---|---|
| D1 — an applicant with no institutional appointment may apply | The EEMS route is open to the requester, and E becomes the question about who signs |
| D1 — no, an institutional PI is required | The EEMS route needs a host PI before anything else, and the requester can be a team member only |
| E1 — the MTA counterparty need not be the applicant's employer | A laboratory or host institution can carry the specimens, which is what makes a self-funded application workable |
| E1 — the MTA counterparty must be the applicant's employer | The specimen route cannot be run by the requester alone, and the host has to be the employer |
| E3 — approved users must hold appointments at the MTA institution | The requester needs an institutional email at that institution, which is a condition the application would have to satisfy |

## 8. Before you send E

- **E is plain text.** The field is a plain textarea; markdown will not
  render, and asterisks around a word look like noise.
- **The limit is 10,000 characters.** E is 1,402.
- **The fields are filled.** The name, the e-mail address and the form's own
  e-mail field carry `Royce Lam` and `roycelam@umich.edu`.
- **The two unlabelled boxes stay empty.** They are anti-spam traps; a
  submission carrying a value in one of them can be discarded without a
  reply.
- **Send E only if D's first answer opens the route.** If an applicant with
  no institutional appointment may not apply, there is no transfer
  agreement for them to be the counterparty of, and the route needs a host
  Principal Investigator instead.
- **E is not a request for access.** It asks about eligibility. No proposal
  is attached, nothing is committed, and no signature is asked for.


---

## 9. The reply — what came back

**Three of the four inquiries were answered, on 2026-11-12.** The answers
arrived by e-mail at `roycelam@umich.edu` and are quoted in full below, so
that what CDAS said and what this repository does about it can be checked
against each other.

| Inquiry | Topic | Ticket | Answered by | Answered (US Eastern) |
|---|---|---|---|---|
| B — the archived material | Biospecimen Availability | #1563 | Shannon Merkle | Nov. 12, 2026, 7:41 a.m. |
| C — the data route's eligibility | Data Access/Availability | not in the pasted record | Dayanna Sorto | Nov. 12, 2026, 7:11 a.m. |
| D — the biospecimen route | Biospecimen Application Process | #1565 | Shannon Merkle | Nov. 12, 2026, 7:48 a.m. |

**Message A has not been answered.** It was submitted first, at 23:27 US
Eastern on 2026-11-10, and it is the one that asks for the clinical-data
counts — the lung-cancer participants with serial plasma and the matched
comparators. That is still outstanding.

### 9.1 The reply to C — the data route's eligibility

<!-- BEGIN REPLY C -->
Dear Royce,

Unfortunately, you will need to find a professor to submit this data request and you must be part of the institution to be able to have access to CDAS data.
<!-- END REPLY C -->

### 9.2 The reply to B — the archived material

<!-- BEGIN REPLY B -->
Dear Royce,

We can get you exact numbers once you put in an application but you can find information about tissue in these tables here: https://cdas.cancer.gov/files/download/kx3yxvf4m8/silver_CDAS_chapter2.aug21.d050322.pdf

These are from primary lung tumors. To date, nothing has been done with the lung tissue so no markers exist.

We do have genotyping data available for most of PLCO and it can be obtained here: https://www.ncbi.nlm.nih.gov/projects/gap/cgi-bin/study.cgi?study_id=phs001286.v5.p2

We will be happy to hone your numbers further if you put in an application, the current round that is open the preliminary application is due by 2/18/27 and the full application is due 4/1/27
<!-- END REPLY B -->

### 9.3 The reply to D — the biospecimen route

<!-- BEGIN REPLY D -->
Dear Royce,

May an applicant who holds no current institutional appointment submit an EEMS preliminary application, provided the funding is their own? An MTA is required so we would need to be employed by a private company, a academic or research institution capable of executing that MTA.

2. If the Principal Investigator named on an EEMS application must be a permanent employee at professor level of some institution, must that institution also be the one that holds the transfer agreement for the specimens, or may the applicant be a member of an investigative team based elsewhere? The institution for the MTA is always that of the lead PI, others may be named on that MTA at different institutions, or they can get a DTUA to access the data, but the DTUA will be between their institution and NCI.

3. What does the preliminary application require from an applicant in that position — an institutional e-mail address, a CV, an NIH biosketch, an ethics determination, and if so, from which body?
institutional email, and NIH biosketch is required. and ethics determination is not needed.

4. Is there a route by which a researcher without an institutional appointment can take part in a PLCO biospecimen study, whether as the applicant or as a member of the investigative team? They can be listed as a collaborator, but they may not access the data without being at the institution with the MTA to have their own DTUA.
<!-- END REPLY D -->

### 9.4 What each answer settles

| Question | The answer | What it changes |
|---|---|---|
| C1 — must the Data Access Requestor be a current permanent employee at professor level | **Yes.** "You will need to find a professor to submit this data request" | The data-only route is closed to the requester as an applicant |
| C2 — may a professor register and submit while someone else fills in the fields | **Yes**, by implication of the same sentence | The delegation the package already assumes is permitted |
| C3 — must an approved user hold a current appointment at the PI's institution | **Yes.** "You must be part of the institution to be able to have access to CDAS data" | An address at an institution where the person no longer holds an appointment is **not** acceptable |
| C4 — any route for a researcher without an appointment | **Not for data access.** The reply is a flat no | The host has to give the requester a standing at their institution, not just carry the proposal |
| B1 — how many lung-cancer participants have plasma from more than one visit | **Not answered.** "We can get you exact numbers once you put in an application" | Still outstanding; message A is the inquiry for it |
| B2 — is the archived lung tissue primary tumour rather than recurrence | **Yes.** "These are from primary lung tumors" | The tissue is usable for the tumour-expression gate |
| B3 — what profiling exists on the lung tissue | **None.** "To date, nothing has been done with the lung tissue so no markers exist" | There is tumour material and tumour DNA, and no somatic profile; the application has to ask for the profiling |
| B4 — is a germline sample or genotype set available | **Yes, for most of PLCO, but through dbGaP**, at phs001286.v5.p2 — not through CDAS | The germline half of the per-molecule attribution is a second, separate application |
| B5 — is the material requested through the EEMS preliminary application, and what are the deadlines | **Yes**, and: "the preliminary application is due by 2/18/27 and the full application is due 4/1/27" | The full application for the current round is due **2027-04-01**, not on the February date |
| D1 — may an applicant with no institutional appointment submit an EEMS preliminary application | **No.** "An MTA is required so we would need to be employed by a private company, a academic or research institution capable of executing that MTA" | The biospecimen route is closed to the requester as an applicant |
| D2 — must the PI's institution hold the MTA | **Yes.** "The institution for the MTA is always that of the lead PI"; collaborators at other institutions may be named on that MTA, or "get a DTUA to access the data" between their institution and NCI | One institution has to carry the whole route |
| D3 — what the preliminary application requires | "Institutional email, and NIH biosketch is required. and ethics determination is not needed" | Two documents come off the checklist: the institutional e-mail address is required, and the **ethics determination is not** |
| D4 — any route for a researcher without an appointment | "They can be listed as a collaborator, but they may not access the data without being at the institution with the MTA to have their own DTUA" | The requester can be named on the application; the data come through the lead PI's institution |

### 9.5 Two consequences that are not answers to anything

**Message E must not be sent.** It asked who may sign the transfer agreement,
and D1 and D2 answer it: an MTA is required, the applicant must be employed
by an institution capable of executing one, and the MTA institution is always
that of the lead PI. There is no longer a question, so the message that
would have asked it has nothing to ask. The draft stays in §7 as a record of
what was considered, and §8's condition — "Send E only if D's first answer
opens the route" — is now met in the negative: the answer closed the route.

**The requester's own standing is now the whole of the PLCO problem.** Every
PLCO route that CDAS administers requires an institution: the data route
requires a professor to submit *and* the requester to be part of that
institution; the biospecimen route requires an employer capable of
executing an MTA; the PAR-25-248 grant route requires an organisation. A
researcher with no affiliation can be named as a collaborator on somebody
else's application, and cannot reach the data at all. That is the shape of the
remaining problem, and the letters have to be written to it.

### 9.6 What the reply did not answer

Message A — the clinical data — is unanswered, and it is the one that asks
for the numbers the programme's design needs: how many lung-cancer
participants have plasma archived from more than one screening visit, and how
many matched participants without cancer are available as comparators. The
tissue tables Shannon Merkle linked do answer the tissue half of the
question, and their numbers are recorded in
[`../DATA-ACCESS-APPLICATIONS.md`](../DATA-ACCESS-APPLICATIONS.md) §2.4. The
plasma half is still open.

---

## 10. Message F — the PAR route's mechanics — drafted, not sent

**Status: drafted, not sent.** It is a question about how two forms work, and
it commits nothing: no application is filed, no specimen is requested, and no
principal investigator is named. It waits for the go because a message sent to
CDAS is his to send.

**Subject:** PLCO
**Topic:** Biospecimen Application Process
**Characters:** 2,534
**Why it exists.** The PAR-25-248 route was found on 2026-11-12, and four
mechanical questions about it cannot be answered from the published
instructions. Two of them decide whether the route is available at all on the
programme's own timeline, and one of them decides whether the route and the
EEMS route can be run at the same time.

<!-- BEGIN MESSAGE F -->
Dear CDAS team,

I am scoping two applications for PLCO — the EEMS preliminary application for biospecimens, and the Request Form for Specimen Verification for PAR-25-248 — and there are four mechanical questions about the PAR route that I cannot answer from the published instructions. I am not filing either application yet; these are questions about how the forms work.

1. The Request Form for Specimen Verification asks for project and PI information, and you state that "Prior to submitting a grant application, applicants must first submit a Request Form for Specimen Verification through the CDAS". Does that request form itself require the Principal Investigator to be a permanent employee of an academic or research institution, or may it name any investigator with a contact address, including an investigator at a company? And must the person filing the form be employed by the same institution as the Principal Investigator?

2. You state that "Investigators are prohibited from submitting an application to both PAR-25-248 and PLCO EEMS at the same time". If an investigator files a Request Form for Specimen Verification but does not submit a grant application, has that investigator submitted "an application to PAR-25-248" for the purposes of that rule?

3. The PAR Request Form instructions state that the form "must be submitted within 3 months of, but no later than 30 days before, the grant due date, and is only valid for that grant cycle", while the CDAS PLCO page states that new PAR Request Forms may be submitted from December 8, 2026 until January 8, 2027. The PAR-25-248 FOA lists an application deadline of October 8, 2027. Which grant cycle does the December 8, 2026 to January 8, 2027 window belong to, and would a Confirmatory Letter issued in that window still be valid for an application due on October 8, 2027?

4. For the EEMS preliminary application, does the named Principal Investigator have to be a permanent employee at professor level of the institution that will hold the Material Transfer Agreement, or may the Principal Investigator be another employee of that institution?

Context, in case it helps: the work is a plasma assay for an electrical marker of a drug-tolerant tumour state, with the per-molecule attribution pre-specified. I am asking these four questions before choosing between the two routes, because the choice depends on the answers and I would rather not take up a reviewer's time with a form that cannot be filed.

Thank you for your help.

Royce Lam
roycelam@umich.edu
<!-- END MESSAGE F -->

**Before it goes.** It is plain text, the field limit is 10,000 characters
and this is 2,534; the name and the address fields carry `Royce Lam` and
`roycelam@umich.edu`; the two unlabelled boxes stay empty, because they are
anti-spam traps and a submission carrying a value in one of them can be
discarded without a reply; and the topic is Biospecimen Application Process,
which is the desk that answered the biospecimen route.
