# Submission runbook

The operational sequence, for the person doing the submission. Everything
here is the same information as the CDAS instructions, turned into the order
the steps actually happen in and the exact text to paste.

**Where an automated agent stops, and why.** Three points in this procedure
cannot be crossed without a person, and they are marked **[GATE]** below:

- **[GATE] Login.** CDAS authenticates through RAS
  (`Shibboleth.sso/RAS-Production`), which is an institutional identity. An
  agent cannot register, and must not be given credentials.
- **[GATE] Data Use Policies.** Agreeing to them is an acceptance of terms
  about patient data, in the PI's name. The PI accepts them.
- **[GATE] Submit.** CDAS's instructions are that the Principal Investigator
  submits the proposal. The PI submits it, having read it.

Everything else — the text, the field values, the order — is prepared.

---

## 1. The entry points

| Application | URL |
|---|---|
| Data-Only Project (this one) | `https://cdas.cancer.gov/projects/create/plco/data/` |
| EEMS biospecimen preliminary application (the plasma aliquots) | `https://cdas.cancer.gov/projects/create/plco/bio/eems/` |
| Images project (not needed) | `https://cdas.cancer.gov/projects/create/plco/data/images/` |
| CDAS contact form, subject "PLCO" | `https://cdas.cancer.gov/contact/` |
| Published PLCO projects, for what a successful proposal looks like | `https://cdas.cancer.gov/approved-projects/plco/` |

Opening the data-only URL without being logged in redirects to
`/login/?next=/projects/create/plco/data/`.

## 2. The order of operations

| # | Step | Who | Gate |
|---|---|---|---|
| 1 | Ask the scoping question (§6) so the sample count is known before the EEMS application is drafted | PI | **done 2026-11-11** |
| 2 | Register a CDAS account through RAS | PI | **[GATE]** |
| 3 | Fill in the private profile: institution and its location | PI | — |
| 4 | Agree to the Data Use Policies | PI | **[GATE]** |
| 5 | Open the data-only project and fill in the fields (§3) | PI or delegate | — |
| 6 | Sign the PI cover sheet (`03-pi-cover-sheet.md`) | PI | — |
| 7 | Identify the Signing Official and give CDAS their contact details | PI | — |
| 8 | Submit the proposal | PI | **[GATE]** |
| 9 | Answer any questions from CDAS staff (§4) | PI | — |
| 10 | Sign the institutional letter (`04-signing-official-letter.md`) and send it | Signing Official | — |
| 11 | Execute the Data Transfer and Use Agreement when CDAS sends it through DocuSign | Signing Official | **[GATE]** |
| 12 | Confirm the Limited Data Set fields, specifically date and site of diagnosis | PI with CDAS staff | — |
| 13 | Download the data from *My CDAS* → the project → *Deliverables* | PI | — |

## 3. Field-by-field

The field names are CDAS's own, taken from the section headings of a
published PLCO project.

| CDAS field | Fill it from | The value |
|---|---|---|
| Principal Investigator → Name | `03-pi-cover-sheet.md` §1 | your name as on the institutional record |
| Principal Investigator → Degrees | `03` §1 | your degrees |
| Principal Investigator → Institution | `03` §1 | your institution |
| Principal Investigator → Position Title | `03` §1 | your title, showing a permanent professor-level or senior-researcher position |
| Principal Investigator → Email | `03` §1 | your institutional email |
| Project Details → contact information | `03` §1 | your institutional email and telephone |
| Institution and location | `03` §1 | your institution and its city and state |
| Signing Official | `04` §5 | the name and title of the person who signs for the institution |
| Approved users | `03` §2 | names and institutional e-mail addresses; anyone at another institution needs their own proposal |
| About this CDAS Project → Study | the form | PLCO |
| About this CDAS Project → Title | `01` §3 | Validating an electrical-channel readout of the relapse-competent state in serial plasma |
| About this CDAS Project → Summary | `01` §4, between the markers | the 498-word text, verbatim |
| About this CDAS Project → Aims | `01` §5 | the three aims |
| About this CDAS Project → Collaborators | `01` §3 | none, or the collaborators' names and institutions |
| Data requested | `01` §6 | the data-requested table, if the form asks for it |

`Project ID` and `Initial CDAS Request Approval` are filled by CDAS.

## 4. The questions CDAS will ask, and the answers

CDAS staff assess whether the data requested are **available** and
**necessary**, and may ask for more information. The answers are already
written down, so that they are not assembled under time pressure.

**"Are these data available?"** Serial plasma exists for participants at
screening visits. Treatment history, mortality, smoking history and the visit
dates are available as study data. Date and site of diagnosis is available in
a Limited Data Set. The one quantity not yet confirmed is **how many
lung-cancer participants have both usable serial plasma and archived primary
tumour** — that is what the scoping inquiry in §6 is for, and it should be
answered before the EEMS application is drafted.

**"Are they necessary?"** The mapping is in `02-proposal-narrative.md` §3:
every requested element is tied to a specific aim. Sequencing data is not
requested.

**"Is the analysis appropriate for the data?"** The analysis is pre-specified,
the estimand is the discrimination between participants diagnosed with lung
cancer and matched participants who are not, and the limitation that the
plasma is drawn before diagnosis is stated in the summary itself rather than
only in the narrative.

**"Is the request proportionate?"** The request is restricted to the lung
stratum of a multi-cancer screening cohort. The assay is run locally on the
aliquots; no sequencing data is requested.

## 5. After submission

- CDAS staff assess, then the NCI Data Access Committee reviews. The
  committee decides whether the project addresses a scientific question and
  whether the data are appropriate for it; it does not assess scientific
  merit, and it does not check whether someone else is doing similar work.
- **Access runs for 12 months.** The renewal or the close-out is the PI's
  and the Signing Official's job, and it has to be done rather than let
  lapse.
- **The proposal is published** on the CDAS website once access is granted.
- The proposal's own Discussion tab is where questions about a submitted
  project are asked, rather than the general contact form.

## 6. Do this first: the scoping inquiry — sent 2026-11-11

It needs no account, no signature and no proposal, and it is on the critical
path: the sample count determines whether the EEMS application (4–6 months)
and the assay budget are worth pursuing. **It has been sent** — two messages
through the CDAS contact form on 2026-11-11. The two messages as they went,
and the sending record with the date, the topic and the length of each, are
in [`07-scoping-inquiry.md`](07-scoping-inquiry.md).

The EEMS preliminary application period closes on **Feb 18 at 11:59 PM EST**
(read from the CDAS PLCO study page on 2026-11-11), so the answers, the
institutional PI and the draft all have to land before then.

It is **two** messages, not one. The contact form has a single Topic and
CDAS forward a message to the party best able to answer it, so the data
questions and the biospecimen questions go separately: message A with the
topic *Data Access/Availability*, message B with *Biospecimen Availability*.

CDAS's form issues **no inquiry number**. It returns a banner and nothing
else, so the reply is the only reference there will be; do not look for a
ticket number to quote.

Four details in the form are worth knowing, all read off the live form on
2026-11-11. The page also carries a newsletter form in the footer that posts
the e-mail address to `public.govdelivery.com`; it is not the contact form.
The contact form carries two boxes with no visible label, which are anti-spam
traps — `id_name` in a container whose class is `antispam1` and `id_phone` in
`antispam2` — and both are skipped when tabbing through the form, so a person
never reaches them. Filling one in makes the submission look automated, so
leave both empty and put the sender's details in the message. The topic list
does not appear until a subject has been chosen, so pick *PLCO* first and the
topics follow. And the form renders ten hidden decoy submit buttons besides
the visible one; press the visible one, because a submission carrying a
hidden button's name is the shape the server is checking for.

## 7. What gets a proposal delayed

- **A PI whose position title does not show a permanent, professor-level or
  senior-researcher role.** CDAS checks this.
- **A summary over 500 words.** The one here is 498, and the checker counts
  it.
- **An incomplete Data Use Policies agreement**, which blocks the form.
- **Data requested that are not available**, which is the most common cause
  of a "may we ask you some additional questions" letter. The scoping
  inquiry is what prevents that.
- **A proposal submitted by someone other than the PI**, which CDAS's
  instructions do not permit.
