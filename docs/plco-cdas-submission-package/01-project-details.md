# CDAS project details, pre-filled

Every field the CDAS project form asks for, with the value to paste. Fields
that only the PI can supply are marked `[PI]` and must be completed before
submission; the checker refuses a package where one of them is still blank.

**Study:** PLCO
**Project type:** Data-Only Project (study data only — no images, no
biospecimens under this proposal; the plasma aliquots are a separate EEMS
application, recorded in the tracker as PLCO-EEMS)

---

## 1. Principal Investigator

CDAS calls this person the "Data Access Requestor". The person must be a
permanent employee of the institution at professor level or a senior
researcher; the instructions state that a post-doc, trainee or lab technician
cannot fill this role.

| Field | Value |
|---|---|
| Principal Investigator Name | `[PI]` — full name as it appears on the institutional record |
| Degrees | `[PI]` |
| Institution | `[PI]` |
| Position Title | `[PI]` — must show a permanent, professor-level or senior-researcher position |
| Institutional email | `roycelam@umich.edu` — taken from this repository's git configuration; **confirm** it is the current official address |
| Contact telephone | `[PI]` |

## 2. Institution

| Field | Value |
|---|---|
| Institution | `[PI]` |
| Institution location | `[PI]` — city and state |
| Signing Official | `[PI]` — name and title of the person authorised to sign legally binding documents for the institution, typically in Contracts, Licensing, Technology, or Research and/or Programs Administration |

## 3. Project details

| Field | Value |
|---|---|
| Project name | Validating an electrical-channel readout of the relapse-competent state in serial plasma |
| Project ID | assigned by CDAS on submission (`PLCO-` followed by a number) |
| Contact email (institutional) | `roycelam@umich.edu` — confirm |
| Collaborators | none at the time of writing; anyone added later needs a separate proposal if they are at another institution |

## 4. Project description

CDAS caps this at **500 words**. The text between the markers below is the
description to paste, and `scripts/check_plco_cdas_package.py` counts its
words so that the cap cannot be discovered by rejection.

<!-- BEGIN PROJECT DESCRIPTION -->
The relapse-competent state is a drug-tolerant subpopulation of tumour cells
associated with relapse. Its definition is transcriptional rather than
electrical: the paper that defines the population never mentions an ion
channel, and in EGFR-mutant lung adenocarcinoma the state-bearing cells are a
minority of the tumour, a median 39% of malignant cells at the residual-disease
timepoint.

We have measured, in three public single-cell deposits, that the state is
nevertheless electrically marked, and that the marking is disease-specific. In
relapsed small-cell lung cancer the state over-expresses Piezo1. In
EGFR-mutant lung adenocarcinoma it over-expresses the potassium channel KCa3.1
at a 2.97x detection ratio. A per-tumour audit shows the KCa3.1 marking is
carried within an individual patient's tumour in 20 of 23 libraries and in
every residual-disease library measured, while the same within-tumour contrast
does not hold in relapsed small-cell lung cancer, where most tumours carry too
little state to read at all.

None of this has been measured in blood. Every plasma number this programme
has produced is a simulation whose inputs are tissue measurements, and when
the programme's own kill conditions are applied to that evidence, the readout
survives in EGFR-mutant lung adenocarcinoma and fails in most relapsed-SCLC
tumours. The decisive unknown is therefore neither the channel nor the read
depth: it is how the state fraction is distributed across individual patients.
A projection from a pooled average hides that heterogeneity, and the
per-tumour audit is what exposed it.

This project asks for the serial plasma and outcome data needed to measure
that distribution and to test the projection against reality. The analysis is
pre-specified: the panel, the operating point (200,000x depth, 200 loci, 25%
of the read budget on the electrical channel), the enrichment-AUC thresholds
(0.60 for the readout, 0.65 at the operating point) and the per-patient
applicability rule are fixed before any data are opened, and the code behind
every published figure is public.

We request serial plasma at every available visit for participants who
progressed to lung cancer, with matched primary tumour tissue where archived;
serial plasma from matched participants who did not progress, at the same
visits; and the clinical data needed to align them: date and site of
diagnosis, treatment, mortality, smoking history, and the visit dates of the
blood draws. We do not request sequencing data; the assays are run locally on
the aliquots. Diagnosis dates are essential to this question, and we therefore
request them in the Limited Data Set.
<!-- END PROJECT DESCRIPTION -->

## 5. Aims

CDAS collects aims separately from the description, and the review asks
whether the project addresses a scientific question and whether the data are
appropriate for it. The three aims are the ones the description refers to;
`02-proposal-narrative.md` states them in full.

1. **Measure the bulk ion-channel enrichment of the state-bearing clone**
   (KCNN4 and PIEZO1) in serial plasma of participants who progressed to lung
   cancer, against serial plasma of matched participants who did not, and
   test the pre-specified burden-normalised enrichment-AUC thresholds (0.60
   for the readout, 0.65 at the operating point).
2. **Estimate the per-participant state fraction and its
   between-participant distribution** — the quantity the simulation has had to
   assume — so that the projection can be re-run against measured inputs.
3. **Determine the per-participant applicability of the readout**: what
   fraction of participants carry the state at a frequency plasma can read,
   and what fraction of tumours express the channel, so that the panel design
   carries a tumour-expression gate rather than a single-channel assumption.

## 6. Data requested

CDAS staff assess whether the data requested are available and necessary, so
this is stated element by element. The justification for each is in
`02-proposal-narrative.md` §3.

| Element | Why it is needed | Limited Data Set? |
|---|---|---|
| Serial plasma, participants who progressed to lung cancer | the measured case side of the discrimination | — |
| Serial plasma, matched participants who did not progress | the comparator the enrichment AUC is computed against | — |
| Matched primary tumour tissue, where archived | the tumour's own expression set; needed for the tumour-expression gate in aim 3 | — |
| Date and site of diagnosis | the lead time between draw and diagnosis is the measurement the project turns on | **yes** |
| Treatment history | distinguishes treatment-emergent from pre-existing state | — |
| Mortality and follow-up time | defines the outcome window for the non-progressing comparator | — |
| Smoking history | the dominant confounder of lung cancer risk and of baseline plasma methylation | — |
| Visit dates of the blood draws | aligns each plasma sample to the clinical timeline | — |
| Sequencing data | not requested | — |

## 7. Approved users

CDAS requires the names and institutional e-mail addresses of everyone the PI
approves to have access at the PI's institution. Users at other institutions
need a separate project proposal with the same project details, so they
cannot be added here.

| Name | Institutional email | Institution | Role |
|---|---|---|---|
| `[PI]` | `roycelam@umich.edu` | `[PI]` | Principal Investigator |
| `[PI]` | `[PI]` | `[PI]` | Co-investigator |
| `[PI]` | `[PI]` | `[PI]` | Analyst |

## 8. Data use policies

The PI agrees, by submitting, to the CDAS Data Use Policies: that the data
will not be used to identify or contact any participant or physician, and that
the research proposal will be published on the CDAS website once access is
granted. The narrative in `02-proposal-narrative.md` is written for that
publication, and it carries the conflict-of-interest disclosure that the
review will need to see.
