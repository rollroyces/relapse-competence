# Data access applications: the prepared packages, and the approval tracker

**Last reviewed:** 2026-11-10
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
EEMS Biospecimens Application" (preliminary application). **Verified
2026-11-10.**

**Why it is a separate application.** The Data-Only route delivers the
phenotype data. The plasma itself is a biospecimen, and aliquots are
released through the NCI's Etiologic and Early Marker Studies programme, whose
first step is a preliminary application. **Expected time to a review outcome:
4–6 months from the preliminary application deadline.** Preliminary-application
deadlines are announced on the CDAS home page; data-only projects are not
listed among the dated deadlines, so they appear to be open continuously, but
that should be confirmed with the coordinating centre rather than assumed.

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

**What to ask for.** Serial plasma aliquots for the lung-cancer stratum in the
pre-diagnosis window, with the clinical data needed to align each draw to
the outcome, and with the methylation measurements if the collaborators are
willing -- so that the two readouts can be compared in the same participants.

**What must be disclosed.** The PanSeer assay was funded by Singlera
Genomics, and Kun Zhang is a co-founder, equity holder and paid consultant of
it. A request to that group has to carry that disclosure, and the request
should also state plainly that the proposed readout is a different measurement
from theirs, not a competing implementation of PanSeer.

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
| PLCO-DATA | Create the CDAS account and log in with RAS | PI | not started | — |
| PLCO-DATA | Fill the data-only project proposal from §2.1 | PI or delegate | prepared | — |
| PLCO-DATA | **PI reviews and submits the proposal** | PI | blocked | proposal text |
| PLCO-DATA | Signing Official signs the proposal | Signing Official | blocked | PI submission |
| PLCO-DATA | Supply PI CV, institutional letter and ethics determination | PI | blocked | — |
| PLCO-DATA | Accept the CDAS data use agreement | PI | blocked | — |
| PLCO-DATA | List project staff | PI | blocked | — |
| PLCO-DATA | Confirm the scope: lung cases with serial plasma and matched tumour | PI | not started | — |
| PLCO-EEMS | Confirm the EEMS preliminary application deadline | PI | not started | — |
| PLCO-EEMS | Prepare the EEMS preliminary application | PI | not started | PLCO-DATA scoping |
| PLCO-EEMS | **Submit the EEMS preliminary application before the deadline** | PI | blocked | deadline, application text |
| TZL-EGA | Re-check the EGA catalogue for a Taizhou or PanSeer deposit | PI | done — no deposit found | — |
| TZL-EGA | Create and validate an EGA user account on an institutional address | PI | not started | — |
| TZL-EGA | Identify the dataset, its EGAD accession and its DAC | PI | blocked | a deposit existing |
| TZL-EGA | Request access, naming the files wanted | PI | blocked | the above |
| TZL-EGA | **Email the DAC directly** | PI | blocked | the above |
| TZL-EGA | Accept the Data Access Agreement | PI | blocked | — |
| TZL-DIRECT | Identify the current contact for collaboration at the Taizhou Institute | PI | not started | — |
| TZL-DIRECT | Prepare the collaboration request from §2.3, with the conflict disclosure | PI | prepared | — |
| TZL-DIRECT | **Send the request** | PI | blocked | contact identified |
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
| 1 | Institutional email address for the PI | PI | available as `roycelam@umich.edu` in the repository's git configuration; confirm it is the current official address | all |
| 2 | PI curriculum vitae | PI | not started | all |
| 3 | Institutional letter of support on headed paper | Signing Official | not started | PLCO-DATA, PLCO-EEMS |
| 4 | Ethics determination for secondary use of human plasma | PI | not started | all |
| 5 | Data use agreement, signed | PI | not started | all |
| 6 | List of research-group members who will hold accounts | PI | not started | TZL-EGA, TZL-DIRECT |
| 7 | Statement of where the data will be stored and who will access it | PI | not started | TZL-EGA, TZL-DIRECT |
| 8 | Pre-specified analysis plan | programme | prepared; §2.1 aims 1–3 | all |
| 9 | Confirmation that the panel and operating point will not be re-tuned after the data are opened | programme | prepared | all |

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
