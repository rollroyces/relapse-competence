# Data access applications: the prepared packages, and the approval tracker

**Last reviewed:** 2026-11-11
**Machine-readable state:** `results/application_tracker/application_tracker.json`
**Regenerate it from this document:** `python scripts/application_tracker.py`
**Check it in CI:** `python scripts/application_tracker.py --check`

---

## 1. What this document is, and what it is not

Two data-access applications stand between this programme and its first real
plasma measurement. Both are prepared here: the route, the fields the forms ask
for, the data we would ask for, and the steps only a person can take.

**Neither application has been submitted, and this document does not submit
them.** A data-access request is an institutional act. CDAS requires the
proposal to be submitted by the Principal Investigator with a Signing
Official's signature; the EGA requires a validated account under an
institutional email address and a signed Data Access Agreement. Filing either
of them on someone's behalf, or on their institution's behalf, would put a
false attestation and a legal commitment in their name, and could get the
account flagged. The remaining steps are listed as steps, not performed.

What this document does instead is remove everything that does not need the
PI's identity or signature, so that what remains is a short list of human
actions with nothing else to prepare.

**Four things have been sent: the scoping inquiry.** It went through CDAS's
public contact form as four messages — the clinical-data scope question, the
biospecimen scope question, a question about who is allowed to submit a
proposal at all, and, the next morning, a question about whether such an
applicant may submit an EEMS application. They are questions, not
applications: they ask what exists and what the rules are before anything is
requested, and they commit the PI to nothing. The proposals and the EEMS
application are untouched and still require the PI's own submission and the
Signing Official's signature. The sending record is in
[`plco-cdas-submission-package/07-scoping-inquiry.md`](plco-cdas-submission-package/07-scoping-inquiry.md)
§0, and the CDAS form issues no inquiry number, so there is no reference to
quote until the reply arrives.

**The PI role cannot be filled by a personal contributor.** CDAS's own
instructions, read on 2026-11-11, say the Principal Investigator — the Data
Access Requestor — "must be a permanent employee of your institution at a
level equivalent to... an academic professor... or senior researcher", cannot
be "a post-doc, trainee, or lab technician", and "will register and be
responsible for the project, its submission, renewals and close-out". The
Signing Official is likewise "permanently employed at the institution". A
researcher without such an appointment therefore cannot submit either
PLCO application, and cannot be an approved user at an institution they do
not belong to.

That is the route's real dependency, and it is not a form to fill: it is an
institutional home with a professor-level PI who agrees to carry the
proposal, and a Signing Official who can sign for the institution. The
package's PI cover sheet cannot be completed until that person exists, which
is why its fields are still markers.

The letter that asks such a person is drafted and waiting for review:
[`HOST-INVITATION.md`](HOST-INVITATION.md). It has not been sent to anyone.
It states what the PI would actually be taking on — registering, reviewing
and submitting, the renewal and the close-out, and the institution's DTUA —
because a request that hides those is a request that ends in a no, and the
approved-user question it raises is the one most likely to end the
correspondence anyway.

### 1.1 What changed in the route

One finding from this review is worth stating before the tables, because it
changes what is worth applying for.

`docs/DATASETS.md` listed the Taizhou Longitudinal Study (PanSeer) as
accessible through an "EGA Data Access Committee". **The EGA catalogue does not
contain it.** On 2026-11-10 the EGA's own public metadata API was queried in
full: 10,814 studies and 21,922 datasets, and no record matches Taizhou,
PanSeer, or Chen Xingdong. The application package below therefore treats the
EGA route as unverified and puts a direct request to the study's investigators
first.

The second finding is about what these cohorts are. **Neither PLCO nor TZL is a
post-treatment cohort.** PLCO enrolled screening participants between 1993
and 2001 and reports diagnoses through 2009; TZL enrolled 123,115 healthy
adults and followed them for cancer occurrence. The requirement in
`docs/DATASETS.md` §1 is serial plasma drawn *after treatment*. Neither
cohort provides it.

That is not a reason to drop either application, but it does change what to
ask for. Both cohorts test the same discrimination the simulator models --
whether a marker separates participants who will progress to cancer from
participants who will not -- one before diagnosis rather than after treatment.
And both can deliver the one quantity the programme has never measured and
keeps having to assume: **the per-participant state fraction, and its
distribution across a real cohort.** The per-patient audit
([`PER-PATIENT-AUDIT.md`](PER-PATIENT-AUDIT.md)) showed that this distribution
is what decides the verdicts: the pooled projection survives for EGFR-mutant
NSCLC because every residual-disease library clears the threshold, while the
relapsed-SCLC candidates fail in most tumours because the state is too rare
to read. A cohort with hundreds of progressors measures that distribution
directly.

## 2. The applications

### 2.1 PLCO — Data-Only Project (CDAS)

**Route:** [cdas.cancer.gov/plco](https://cdas.cancer.gov/plco/) → "Begin a
Data-Only Project". **Verified 2026-11-10.**

**The signed-and-submitted package is in
[`plco-cdas-submission-package/`](plco-cdas-submission-package/README.md)**:
the CDAS form fields pre-filled, the proposal narrative, the PI cover sheet
with its attestations, the Signing Official's letter, and the documents
checklist. What is drafted there is what the CDAS form asks for; what is
missing there is marked `[PI]` or `[SO]` and is listed in the checklist.

**What CDAS says this needs:** an institution, a Principal Investigator, a
Signing Official and project staff; the proposal must be submitted by the PI;
expected time for a new project to have data delivered is 1–4 weeks.

**Pre-drafted form fields:**

- **Title.** Validating an electrical-channel readout of the relapse-competent
  state in serial plasma: a pre-specified analysis in the PLCO cohort.
- **Summary.** The programme has measured, in public single-cell deposits,
  that the relapse-competent state in small-cell lung cancer is marked by the
  ion channel Piezo1 and that in EGFR-mutant lung adenocarcinoma the state is
  marked by the potassium channel KCa3.1 (KCNN4). A per-tumour audit shows
  the marker is carried within a patient's tumour in 20 of 23 EGFR-mutant
  NSCLC libraries and in every residual-disease library measured, while the
  same within-tumour contrast does not hold in relapsed small-cell lung
  cancer. The programme has not yet measured the electrical signal in blood:
  every plasma number published so far is a simulation built on tissue
  measurements, and the gate review that applied the programme's own kill
  conditions found that the readout survives in NSCLC but not in SCLC, and
  that the decisive uncertainty is the distribution of the state fraction
  across individual patients. This project requests the serial plasma and
  outcome data needed to test that projection against reality. The analysis
  is pre-specified: the panel, the operating point (200,000x, 200 loci, 25%
  allocation to the electrical channel), the enrichment-AUC thresholds and the
  per-patient applicability rule are fixed before the data are opened.
- **Aims.**
  1. Measure the bulk ion-channel enrichment of the state-bearing clone
     (KCNN4 and PIEZO1) in serial plasma of participants who progressed to
     lung cancer, against serial plasma of matched participants who did not,
     and test the pre-specified burden-normalised enrichment-AUC thresholds
     (0.60 for the readout, 0.65 at the operating point).
  2. Estimate the per-participant state fraction and its between-participant
     distribution -- the quantity the simulation has had to assume -- so the
     projection can be re-run against measured inputs.
  3. Determine the per-participant applicability of the readout: what
     fraction of participants carry the state at a frequency plasma can read,
     and what fraction of tumours express the channel, so the panel design
     carries a tumour-expression gate rather than a single-channel assumption.
- **Data requested.** Serial plasma for participants with a lung cancer
  diagnosis at every available visit, with matched primary tumour tissue where
  archived, plus serial plasma from matched cancer-free participants at the
  same visits; and the phenotype data to align them -- cancer diagnosis site
  and date, treatment, mortality, smoking history, and the visit dates of the
  blood draws. Whole-genome sequencing data is not requested; the programme
  generates its own reads locally.

### 2.2 PLCO — EEMS biospecimen application (CDAS)

**Route:** [cdas.cancer.gov/plco](https://cdas.cancer.gov/plco/) → "Begin an
EEMS Biospecimens Application". The governing documents are the *PLCO EEMS
Application Process* (updated June 30, 2025) and the *PLCO EEMS Policies &
Procedures* (updated June 16, 2025). **Verified 2026-11-11.**

**This is the route that does not require an institutional PI.** The
professor-level requirement is in the *data* instructions — "Instructions for
Accessing Data Through the CDAS Website" — and not in the EEMS instructions.
The EEMS process says: "If you have your own source of funding and wish to
obtain PLCO biospecimens, then you should register with CDAS and begin the
EEMS Application for Biospecimens." The policies say the resource "is
available to the entire scientific community" and that access "is based on a
peer review process". What the EEMS application asks for is "contact
information for your Principal Investigator" — it does not restate the
employment or rank requirement that the data route does.

**Two deadlines, not one.** Preliminary applications are "accepted on a
rolling basis" and are reviewed for feasibility by NCI PLCO EEMS staff; on
acceptance of the preliminary application, a final application may be
submitted. Final proposals are "accepted on a twice yearly basis
(June/July and January/February)". The Feb 18 date on the CDAS PLCO page is
therefore the **final application** deadline for the January/February round,
not a preliminary deadline. The tracker previously said otherwise, and that
was wrong: the preliminary application can go in at any time, but the
research plan and an NIH biosketch for every member of the investigative team
have to be in by Feb 18, which means the preliminary application has to be
accepted first.

**Why this programme fits the EEMS programme's own priorities.** The
policies say PLCO resources "are most suitable for Phase III studies", which
are "retrospective longitudinal repository studies to determine if a biomarker
can detect cancer before clinical diagnosis", and they name the questions:
how well a biomarker distinguishes people who later developed cancer from
those who did not, and how early, before clinical diagnosis, it can detect
cancer — the lead time. That is the design in
[`PLASMA-ASSAY-SPECIFICATION.md`](PLASMA-ASSAY-SPECIFICATION.md).

**What the specimens allow.** Plasma is banked at T0, T3, T4 and T5; at T1
and T2 the plasma, red-cell and buffy-coat fractions were not. Nearly all
tissue samples have corresponding prediagnostic blood samples or buccal cells
from the same patient, which is what the per-molecule attribution needs. The
lung tumour collection is 435 PLCO cases in 3,773 cores, plus 446 NLST-LSS
cases in 3,951 cores, with additional tissue cores for DNA, RNA and protein.

**Three requirements to plan around.**
- *Serial samples face a higher bar.* Applications "requesting the use of
  serial samples will be subjected to additional scrutiny during scientific
  review and a higher bar for approval", and the policies hold that
  time-related evaluations "should occur only after PLCO studies demonstrate
  that the analysis from the disease-proximate samples shows adequate
  performance results". A disease-proximate-first design, with serial
  sampling as a later step, is the shape the policies point at.
- *A new assay needs a pilot first.* "Pilot studies will be required for new
  assays to establish assay reproducibility", and pilot data "must be
  evaluated and approved by NCI before full analytic samples can be
  released".
- *The phenotype data comes after the assay.* "Investigators are expected to
  submit laboratory analysis results before they are provided with phenotype
  data for their population", and the linking of laboratory data to
  individual data "shall only be performed by the NCI PLCO team". The
  analysis is therefore blinded, which is exactly why the panel, the
  operating point and the thresholds are fixed in advance.

**The one institutional thing an individual cannot sign.** Specimen shipment
requires a Material Transfer Agreement with NCI, and the Technology Transfer
Center contacts "extramural investigators" to execute one. An MTA is a legal
instrument for an institution, so this needs a counterparty — but it does not
have to be the institution that employs the applicant, and it does not have
to be the PI's institution.

**Whether the route is open to an applicant with no institutional appointment
at all is the first question, and it has been asked.** The two questions —
whether such an applicant may submit a preliminary application, and who may
sign the transfer agreement — are in
[`plco-cdas-submission-package/07-scoping-inquiry.md`](plco-cdas-submission-package/07-scoping-inquiry.md)
§7, as messages D and E. The answer to D1 decides whether the rest of this
section is worth doing, which is why it goes before the deadline rather than
with the application.

**Expected time to a review outcome:** 4–6 months from the final application
deadline.

**Where the pool of people who can be that PI comes from.** CDAS publishes
every approved PLCO project with its Principal Investigator and institution,
and the list can be filtered to biospecimen studies:
`https://cdas.cancer.gov/approved-projects/plco/?data&data_types=plco_data_images&bio_types=plco_bio_eems&bio_types=plco_bio_par`.
Those investigators have already been through EEMS, hold the biosketches,
and know what the review asks. Two of the recent entries are instructive. A
project approved on 2026-09-15 is titled "Analytical Suitability and
Storage-Stability Pilot for a Serum NMR-Based Multi-Omics Multi-Cancer Early
Detection Assay Using Pre-Diagnostic PLCO Specimens" — a new multi-omics
early-detection assay on pre-diagnostic PLCO specimens, brought to NCI as a
pilot, which is exactly the shape the policies describe for an assay that
has not been validated. And one prostate project appears twice, once as an
original and once as a continuation credited to a different Principal
Investigator, which shows the role can change hands inside a project's life
rather than being fixed for its duration.

**A collaborator does not have to be the PI.** The EEMS application has an
"Investigative Team": every member is listed and supplies an NIH biosketch,
and the EEMS review panel's own members are allowed to submit an
application or to be a co-investigator on one, provided they recuse
themselves from the applications they are not on. So a mechanistic
collaborator can be named on the application, with their institution behind
the Material Transfer Agreement, without being the person who registers,
submits, renews and closes out. That distinction is what makes a
collaboration a smaller ask than a host PI, and it is the form to aim for
when the collaboration is scientific rather than administrative.

**The number of lung-cancer participants with usable serial plasma and a
matched tumour is the scoping question that has to be answered first.** It
determines whether this application is worth the 4–6 months, and it can be
asked of the coordinating centre without an application.

### 2.3 Taizhou Longitudinal Study — route unverified, direct request first

**Route:** the EGA Data Access Committee, **as recorded in
`docs/DATASETS.md`, is not supported by the EGA catalogue.** On 2026-11-10 the
EGA's public metadata API was queried in full — 10,814 studies and 21,922
datasets — and no record matches Taizhou, PanSeer or Chen Xingdong. The EGA's
own guidance is that access requests are made to the data controller, not to
the EGA, and a dataset that is not in the catalogue has no DAC to apply to.

**Primary route, therefore, is a direct request** to the Fudan Taizhou
Institute of Health Sciences and the Human Phenome Institute, and to the
corresponding authors of Chen X, et al. *Non-invasive early detection of
cancer four years before conventional diagnosis using a blood test*, Nature
Communications 2020, doi:10.1038/s41467-020-17316-z.

**Why the collaboration is worth asking for.** TZL is the only published
cohort in which a blood test was shown to detect cancer in asymptomatic
participants one to four years before diagnosis, at 95% sensitivity
(95% CI 89–98) against a specificity of 96% (95% CI 93–98). That result is
methylation-based, and the measurement proposed here is orthogonal to it: a
bulk transcript measurement of two ion channels. The two are complementary
rather than competing, and TZL has the sample collection and the outcome
follow-up that the programme cannot obtain any other way.

**What to ask for, and in what order.** The order matters, because the first
question is about consent rather than samples, and everything else is
conditional on its answer.

1. **Is there germline consent, or a way to obtain it, for participants in
   the lung-cancer stratum?** The per-molecule attribution reads a heterozygous
   germline SNP that the participant's own tumour shifts, so a participant
   without germline genotype is not measurable by this assay at all. The
   programme's own pilot measures the fraction of participants with an
   informative position, and this is where that fraction comes from.
2. **Is the matched tumour tissue available for those participants?** It is
   what establishes which germline positions this tumour shifts, and it is
   the tumour-expression gate.
3. **Serial plasma aliquots for the lung-cancer stratum** in the
   pre-diagnosis window, with the clinical data needed to align each draw to
   the outcome.
4. **The methylation measurements**, if the collaborators are willing, so the
   two readouts can be compared in the same participants.

**Why the consent question comes first.** The data availability statement
carries a constraint that bears directly on this programme's assay design:

> Full genetic sequencing data was not included in the informed consent, hence
> only the methylation status at each genomic position has been released.

**No participant germline genotype was consented for.** That is decisive for
the per-molecule attribution the assay specification depends on, which reads a
heterozygous germline SNP that the participant's own tumour shifts. TZL cannot
supply that per participant for the participants already in the study. It is a
question to put to the collaborators -- whether a *new* cohort with germline
consent exists, or whether the archived material was banked under consents
that would permit it -- and it has to be asked before the request is sent,
because if the answer is no, the collaboration cannot deliver the attribution
the readout rests on.

**What must be disclosed.** The funding is narrower than it first looks, and
the request should say so precisely rather than over-disclose. The paper's
acknowledgements read: *"The TZL study was supported by the National Key
Research and Development Program of China, the National Natural Science
Foundation of China, the Key Basic Research grants from the Science and
Technology Commission of Shanghai Municipality, the International S&T
Cooperation Program of China, the Shanghai Municipal Science and Technology
Major Project program, and the 111 Project. **Funding for the DNA methylation
assays was provided by Singlera Genomics.**"

The qualifier is **the DNA methylation assays**, not the cohort: the Taizhou
Longitudinal Study itself was funded by the Chinese national and municipal
programmes, while Singlera funded the assay. So the assay carries the
Singlera funding; the cohort does not.

The competing-interest statement is fuller, and it is the part that has to be
disclosed: thirteen authors are employees of Singlera Genomics, Yuan Gao and
Rui Liu are board members of it, and Jeffrey Gole, Athurva Gore and Rui Liu
are inventors on patent US62/657,544, which is held by Singlera Genomics and
covers basic aspects of the library preparation method the paper uses. Kun
Zhang is a co-founder, equity holder and paid consultant, and the terms are
managed by UC San Diego under its conflict-of-interest policies.

**What must be acknowledged.** The PanSeer Python code is public, deposited
in `https://github.com/ncomms-20-10056-t/ncomms-20-10056-t`. Two things
follow. The programme can use it, and it can check its own implementation
against the published one. And the request has to state plainly that the
proposed readout is a different measurement from PanSeer, not a competing
implementation of it -- a distinction that is easier to make credibly when the
request acknowledges the released code rather than appearing unaware of it.

**If an EGA deposit appears.** The route is short and is worth doing in
parallel: register as an EGA user with an institutional email address and
validate the account; find the dataset in the catalogue and note its EGAD
accession and DAC; click "Request access", write the comment naming the files
wanted and send it; **email the DAC directly as well**, which the EGA's own
instructions require; accept the Data Access Agreement; and on approval
download through the EGA Secure Download Client or PyEGA3. The DAC's own
published practice is to answer an initial request within two weeks.

### 2.4 The external facts this rests on, and when they were checked

| Fact | Value | Source | Verified on |
|---|---|---|---|
| EGA studies in the catalogue | 10,814 | EGA public metadata API | 2026-11-10 |
| EGA datasets in the catalogue | 21,922 | EGA public metadata API | 2026-11-10 |
| EGA records matching Taizhou, PanSeer or Chen Xingdong | 0 | EGA public metadata API | 2026-11-10 |
| PLCO participants enrolled 1993–2001 | 155,000 | CDAS PLCO trial summary | 2026-11-10 |
| PLCO data-only delivery time | 1–4 weeks | CDAS PLCO instructions | 2026-11-10 |
| PLCO EEMS review outcome | 4–6 months from the preliminary application deadline | CDAS PLCO instructions | 2026-11-10 |
| PLCO diagnoses and mortality follow-up | diagnoses through 2009, mortality through 2022 | CDAS PLCO trial summary | 2026-11-10 |
| TZL participants providing plasma for long-term storage | 123,115 | Chen X et al. 2020 | 2026-11-10 |
| PanSeer sensitivity in asymptomatic participants diagnosed within 4 years | 95% (95% CI 89–98) | Chen X et al. 2020 | 2026-11-10 |
| PanSeer specificity | 96% (95% CI 93–98) | Chen X et al. 2020 | 2026-11-10 |
| PanSeer assay funding | Funding for the DNA methylation assays was provided by Singlera Genomics; the cohort was funded by the Chinese national and municipal programmes (National Key R&D Program, NSFC, Shanghai Key Basic Research, International S&T Cooperation, Shanghai Major Project, 111 Project) | Chen X et al. 2020, acknowledgements | 2026-11-12 |
| TZL genetic sequencing consent | Full genetic sequencing data was not included in the informed consent, hence only the methylation status at each genomic position has been released | Chen X et al. 2020, data availability statement | 2026-11-12 |
| PanSeer Python code | Public, at https://github.com/ncomms-20-10056-t/ncomms-20-10056-t | Chen X et al. 2020, data availability statement; repository reachable, HTTP 200 | 2026-11-12 |
| PanSeer competing interests | 13 authors are Singlera Genomics employees; Yuan Gao and Rui Liu are board members; Jeffrey Gole, Athurva Gore and Rui Liu are inventors on patent US62/657,544; Kun Zhang is a co-founder, equity holder and paid consultant, managed by UC San Diego under its conflict-of-interest policies | Chen X et al. 2020, competing interests statement | 2026-11-12 |
| PanSeer correspondence | Weimin Ye (weimin.ye@ki.se), Yuan Gao (gary.gao@singleragenomics.com), Kun Zhang (kzhang@bioeng.ucsd.edu), Rui Liu (rliu@singleragenomics.com), Li Jin (lijin@fudan.edu.cn) | Chen X et al. 2020, author notes | 2026-11-12 |
| CDAS contact form: message length limit | 10,000 characters | CDAS contact form | 2026-11-10 |
| CDAS contact form: subject for PLCO | PLCO | CDAS contact form | 2026-11-10 |
| CDAS contact form: topics | Data Access/Availability, Biospecimen Availability | CDAS contact form | 2026-11-10 |
| CDAS contact form: unlabelled anti-spam fields | 2 | CDAS contact form | 2026-11-10 |
| CDAS PI eligibility | permanent employee of the institution at professor level or senior researcher; cannot be a post-doc, trainee or lab technician; the PI registers, submits, renews and closes out | CDAS instructions for accessing data (PDF) | 2026-11-11 |
| CDAS Signing Official eligibility | permanently employed at the institution and authorised to sign legally binding documents | CDAS instructions for accessing data (PDF) | 2026-11-11 |
| CDAS approved users | names and institutional e-mail addresses, at the PI's institution; a collaborator from another institution needs a separate proposal | CDAS instructions for accessing data (PDF) | 2026-11-11 |
| PLCO EEMS biospecimen application deadline | Feb 18, 11:59 PM EST — the final-application round; preliminary applications are rolling | CDAS PLCO page, and the EEMS policies | 2026-11-11 |
| CDAS: PLCO approved-project list | public, with the Principal Investigator and institution for every project, and filterable by biospecimen type | CDAS approved projects | 2026-11-11 |
| PLCO EEMS investigative team | every member is listed and supplies an NIH biosketch; EEMS panel members may be co-investigators, with recusal | PLCO EEMS Application Process and Policies & Procedures | 2026-11-11 |
| PLCO EEMS eligibility | a self-funded applicant may register and apply: "If you have your own source of funding and wish to obtain PLCO biospecimens"; the resource is "available to the entire scientific community" | PLCO EEMS Application Process and Policies & Procedures | 2026-11-11 |
| PLCO biospecimens in the repository | about 2.9 million specimens; plasma banked at T0, T3, T4, T5 but not T1 or T2 | PLCO EEMS Policies & Procedures | 2026-11-11 |
| PLCO lung tumour collection | 435 PLCO cases in 3,773 cores, plus 446 NLST-LSS cases in 3,951 cores | PLCO EEMS Policies & Procedures | 2026-11-11 |
| PLCO tissue with matched prediagnostic blood | nearly all tissue samples have prediagnostic blood samples or buccal cells from the same patient | PLCO EEMS Policies & Procedures | 2026-11-11 |
| PLCO serial-sample approval | a higher bar than non-serial applications, and time-related evaluations are expected only after the disease-proximate analysis performs adequately | PLCO EEMS Policies & Procedures | 2026-11-11 |
| PLCO new-assay pilot | a pilot is required for assay reproducibility and its data must be approved by NCI before full analytic samples are released | PLCO EEMS Policies & Procedures | 2026-11-11 |
| PLCO phenotype-data sequencing | laboratory results are submitted before the investigator is given phenotype data; only the PLCO team links them | PLCO EEMS Policies & Procedures | 2026-11-11 |
| CDAS contact form: message field limit, enforced by the field | 10,000 characters | CDAS contact form | 2026-11-11 |
| CDAS contact form: inquiry reference number issued | none — the form returns only a confirmation banner | CDAS contact form | 2026-11-11 |
| CDAS contact form: topic list appears only after a subject is chosen | yes | CDAS contact form | 2026-11-11 |
| CDAS contact form: hidden decoy submit buttons | 10, plus the visible one | CDAS contact form | 2026-11-11 |
| CDAS contact form: anti-spam traps, both left empty at submission | `id_name` in `antispam1`; `id_phone` in `antispam2` | CDAS contact form | 2026-11-11 |
| Scoping inquiries sent to CDAS | 4 — Data Access/Availability twice, Biospecimen Availability, and Biospecimen Application Process | this repository's sending record | 2026-11-12 |
| KCa3.1 within-tumour fold above 1 in EGFR-mutant NSCLC libraries | 20 of 23 | this repository's per-library folds | 2026-11-09 |
| Residual-disease libraries clearing the programme's K3 threshold | 7 of 7 | this repository's per-patient audit | 2026-11-09 |

The last two rows are not external: they are this repository's own
measurements, and they are why the applications are worth making. The
readout is carried within a patient's tumour in 20 of 23 EGFR-mutant NSCLC
libraries and in every residual-disease library measured, and the per-patient
audit is what shows the state fraction's distribution is the decisive
uncertainty. The plasma cohorts would measure that distribution directly.


## 3. The approval tracker

| Application | Step | Owner | Status | Depends on |
|---|---|---|---|---|
| PLCO-DATA | Assemble the submission package | programme | done — `docs/plco-cdas-submission-package/` | — |
| PLCO-DATA | Check the package: 500-word cap, fields, numbers, signature blocks | programme | done — `scripts/check_plco_cdas_package.py` | the package |
| PLCO-DATA | Write the submission runbook and the scoping inquiry | programme | done — `06-submission-runbook.md`, `07-scoping-inquiry.md` | the package |
| PLCO-DATA | Re-derive the operating point with the leukocyte reference loci, and re-run the audit at it | programme | done — nothing in the search space clears K3; the reference set is a check, not a correction | the leukocyte audit |
| PLCO-DATA | Send the scoping inquiry to CDAS (subject: PLCO) | PI | done — four messages sent, three on 2026-11-11 and the eligibility question on 2026-11-12; the form issues no inquiry number | the scoping inquiry |
| PLCO-DATA | Secure an institutional PI to be the Data Access Requestor, and a Signing Official | PI | not started — the PI must be a permanent employee at professor level and is the person who submits | an institutional relationship |
| PLCO-DATA | Approach a host PI with the invitation letter | PI | draft prepared, not sent — `docs/HOST-INVITATION.md` | the eligibility answer |
| PLCO-DATA | Create the CDAS account and log in with RAS | PI | not started | — |
| PLCO-DATA | Fill the data-only project proposal from the package | PI or delegate | prepared | — |
| PLCO-DATA | **PI reviews and submits the proposal** | PI | blocked | proposal text |
| PLCO-DATA | Signing Official signs the institutional letter | Signing Official | blocked | PI submission |
| PLCO-DATA | Supply PI CV, institutional letter and ethics determination | PI | blocked | — |
| PLCO-DATA | Accept the CDAS data use agreement | PI | blocked | — |
| PLCO-DATA | List project staff | PI | blocked | — |
| PLCO-DATA | Confirm the scope: lung cases with serial plasma and matched tumour | PI | not started | — |
| PLCO-EEMS | Confirm the EEMS preliminary application deadline | PI | done — preliminary applications are rolling; Feb 18 is the final-application deadline for the January/February round | the EEMS policies, read 2026-11-11 |
| PLCO-EEMS | Prepare the EEMS preliminary application | PI | not started — it is rolling, so it does not have to wait for Feb 18 | PLCO-DATA scoping |
| PLCO-EEMS | Send the biospecimen eligibility questions to CDAS (messages D and E) | PI | D sent 2026-11-12; E drafted and held until the first answer to D | the answer to D1 |
| PLCO-EEMS | Submit the EEMS preliminary application | PI | blocked | the scoping answers, the application text |
| PLCO-EEMS | **Submit the EEMS final application by Feb 18, 11:59 PM EST** | PI | blocked | preliminary acceptance, the research plan, an NIH biosketch for every investigative-team member |
| TZL-EGA | Re-check the EGA catalogue for a Taizhou or PanSeer deposit | PI | done — no deposit found | — |
| TZL-EGA | Create and validate an EGA user account on an institutional address | PI | not started | — |
| TZL-EGA | Identify the dataset, its EGAD accession and its DAC | PI | blocked | a deposit existing |
| TZL-EGA | Request access, naming the files wanted | PI | blocked | the above |
| TZL-EGA | **Email the DAC directly** | PI | blocked | the above |
| TZL-EGA | Accept the Data Access Agreement | PI | blocked | — |
| TZL-DIRECT | Identify the current contact for collaboration at the Taizhou Institute | PI | not started | — |
| TZL-DIRECT | **Establish whether germline consent exists for the lung-cancer stratum** | PI | not started — the published consent excluded full genetic sequencing, so the attribution the readout rests on has no source | the answer |
| TZL-DIRECT | Prepare the collaboration request from §2.3, with the conflict disclosure | PI | prepared — `docs/TAIZHOU-COLLABORATION-REQUEST.md` | — |
| TZL-DIRECT | **Send the request** | PI | blocked | contact identified, germline consent established |
| TZL-DIRECT | Register the EGA account in parallel | PI | not started | — |

**Application-level status:**

| Application | Dataset | Access route | Route verified | Expected turnaround | Status |
|---|---|---|---|---|---|
| PLCO-DATA | PLCO | CDAS Data-Only Project | yes, 2026-11-10 | 1–4 weeks to data delivery | blocked on PI submission |
| PLCO-EEMS | PLCO | CDAS EEMS biospecimen preliminary application | yes, 2026-11-10 | 4–6 months from the deadline | blocked on PI submission |
| TZL-EGA | Taizhou Longitudinal Study | EGA Data Access Committee | **no**, 2026-11-10 | no published turnaround; DAC practice is a reply within 2 weeks | blocked on the route |
| TZL-DIRECT | Taizhou Longitudinal Study | direct request to the study investigators | n/a | unknown | not started |

## 4. Prerequisites, shared by both applications

| # | Prerequisite | Owner | Status | Applies to |
|---|---|---|---|---|
| 1 | Institutional email address for the PI | PI | confirmed — `roycelam@umich.edu` carried both scoping inquiries on 2026-11-11 | all |
| 2 | PI curriculum vitae | PI | not started | all |
| 3 | Institutional letter of support on headed paper | Signing Official | not started | PLCO-DATA, PLCO-EEMS |
| 4 | Ethics determination for secondary use of human plasma | PI | not started | all |
| 5 | Data use agreement, signed | PI | not started | all |
| 6 | List of research-group members who will hold accounts | PI | not started | TZL-EGA, TZL-DIRECT |
| 7 | Statement of where the data will be stored and who will access it | PI | not started | TZL-EGA, TZL-DIRECT |
| 8 | Pre-specified analysis plan | programme | prepared; §2.1 aims 1–3 | all |
| 9 | Confirmation that the panel and operating point will not be re-tuned after the data are opened | programme | prepared | all |
| 10 | An institutional PI: a permanent employee at professor level, to be the Data Access Requestor and to submit the proposal | PI | not started | PLCO-DATA |
| 11 | An institution willing to execute the NCI Material Transfer Agreement for the specimens | PI | not started | PLCO-EEMS |
| 12 | A laboratory to run the transcript assay on the aliquots, blinded, with pilot QC | PI | not started | PLCO-EEMS |

## 5. What these applications cannot deliver, and what would

- **No post-treatment serial plasma from either cohort.** The programme's
  post-treatment MRD claim cannot be settled by PLCO or TZL. What they can
  settle is the per-participant state-fraction distribution and the
  discrimination question, in lung cancer, in a pre-diagnosis window.
- **PLCO's lung cases are from a screening cohort enrolled 1993–2001**, with
  diagnoses through 2009 and mortality through 2022. The number of lung
  cases with serial plasma *and* a matched tumour is unknown and is the
  scoping question in the tracker.
- **The artefact both applications would test is a transcript measurement**, and
  neither cohort has been sequenced for it. The assays would have to be run on
  the aliquots, which is a cost and a time line the tracker does not yet
  contain. That line should be added once the sample counts are confirmed.
- **A route to genuinely post-treatment serial plasma with matched tumour is
  still missing.** That is a clinical-cohort collaboration rather than a
  registry application, and it is the single largest gap in the programme's
  evidence chain.

## 6. How this state is maintained

`docs/DATA-ACCESS-APPLICATIONS.md` is the source of truth. The tables above
are parsed into `results/application_tracker/application_tracker.json`, and CI
runs `python scripts/application_tracker.py --check`, which fails if the
committed JSON does not match this document. When an application moves, edit
this document and run `python scripts/application_tracker.py` to regenerate the
JSON.
