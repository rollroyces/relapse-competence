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

The field names below are CDAS's own, taken from the section headings of a
published PLCO project: *About this CDAS Project* carries Study, Project ID,
Title, Summary, Aims and Collaborators.

| Field | Value |
|---|---|
| Title | Validating an electrical-channel readout of the relapse-competent state in serial plasma |
| Summary | the text in section 4 below |
| Project ID | assigned by CDAS on submission (`PLCO-` followed by a number) |
| Collaborators | none at the time of writing; anyone added later needs a separate proposal if they are at another institution |
| Initial CDAS Request Approval | filled by CDAS; the date the Data Access Committee approved the project |

## 4. Summary

CDAS's instructions describe this as "a brief description of your project
(500 words or less)", and the published projects show it as the **Summary**
field. The text between the markers below is what to paste there, and
`scripts/check_plco_cdas_package.py` counts its words so that the cap cannot
be discovered by rejection.

<!-- BEGIN PROJECT DESCRIPTION -->
The relapse-competent state is a drug-tolerant subpopulation of tumour cells associated with relapse. Its definition is transcriptional rather than electrical: the paper defining the population never mentions an ion channel, and the state-bearing cells are a minority of the tumour — a median 39% of malignant cells at the residual-disease timepoint.

We have measured, in three public single-cell deposits, that the state is nevertheless electrically marked, and disease-specifically. In EGFR-mutant lung adenocarcinoma it over-expresses the potassium channel KCa3.1 at a 2.97x detection ratio. A per-tumour audit shows the KCa3.1 marking is carried within an individual patient's tumour in 20 of 23 libraries and in 7 of 7 residual-disease libraries, while it does not hold in relapsed small-cell lung cancer, where most tumours carry too little state to read.

None of this has been measured in blood. Every plasma number this programme has produced is a simulation built on tissue measurements, and the programme's own kill conditions, applied to that evidence, leave the readout surviving in EGFR-mutant lung adenocarcinoma and failing in most relapsed-SCLC tumours. The decisive unknown is therefore neither the channel nor the read depth, but the state fraction's distribution across patients.

A second audit changed the assay design. In bulk plasma most cfDNA is leukocyte-derived, and KCa3.1 is expressed in immune cells, so a channel transcript read without localisation is dominated by leukocyte material: at a realistic tumour DNA fraction the state contributes about two per cent of the measurement, and the burden-normalised statistic inverts rather than degrades. The assay must therefore localise the channel transcript to the tumour, counting only reads carrying a tumour-specific somatic variant on the same molecule; estimate each participant's tumour cfDNA fraction from the somatic variants already read; and include leukocyte reference loci so each library's background is measured, not assumed. Correcting the background afterwards is not enough: we re-allocated the panel to carry a reference set, re-derived the operating point, and it stays at chance. The reference set is a check, not a fix. Our projection assumes localisation works, and is therefore an upper bound.

This project asks for the serial plasma and outcome data needed to test that projection. The plasma is drawn at screening visits, before diagnosis: the question is whether the readout separates participants diagnosed with lung cancer from matched participants who are not. The analysis is pre-specified: the panel, operating point, thresholds and per-patient applicability rule are fixed before any data are opened, and the code behind every published figure is public.

We request serial plasma at every visit for participants diagnosed with lung cancer, with their matched primary tumour; serial plasma from matched participants not diagnosed with lung cancer during follow-up, at the same visits; and the clinical data to align them: date and site of diagnosis, treatment, mortality, smoking history, and the visit dates of the blood draws. We do not request sequencing data; assays are run locally on the aliquots. Diagnosis dates are essential, and we request them in the Limited Data Set.
<!-- END PROJECT DESCRIPTION --><!-- END PROJECT DESCRIPTION --><!-- END PROJECT DESCRIPTION -->

## 5. Aims

CDAS collects aims separately from the description, and the review asks
whether the project addresses a scientific question and whether the data are
appropriate for it. The three aims are the ones the description refers to;
`02-proposal-narrative.md` states them in full. What is measured, in which
analyte, and how the signal is attributed to the tumour are specified in
[`PLASMA-ASSAY-SPECIFICATION.md`](../PLASMA-ASSAY-SPECIFICATION.md).

1. **Measure the *localised* ion-channel enrichment of the state-bearing
   clone** (KCNN4 and PIEZO1) in serial plasma of participants who were
   diagnosed with lung cancer, against serial plasma of matched participants
   who were not, counting only the channel-locus reads that carry a
   tumour-specific somatic variant on the same molecule, and testing the
   pre-specified thresholds on the tumour-attributable enrichment AUC (0.60 for
   the readout, 0.65 at the operating point). The raw, unlocalised enrichment
   is reported as a secondary analysis, because our own audit shows it
   inverts when the plasma pool carries leukocyte DNA.
2. **Estimate the per-participant tumour cfDNA fraction and the
   per-participant state fraction** — the two quantities the simulation has
   had to assume — from the somatic variants read in the same library, so the
   projection can be re-run against measured inputs.
3. **Determine the per-participant applicability of the readout**: what
   fraction of participants carry the state at a frequency plasma can read,
   and what fraction of their tumours express the channel, so that the panel
   design carries a tumour-expression gate rather than a single-channel
   assumption.

## 6. Data requested

CDAS staff assess whether the data requested are available and necessary, so
this is stated element by element. The justification for each is in
`02-proposal-narrative.md` §3.

| Element | Why it is needed | Limited Data Set? |
|---|---|---|
| Serial plasma, participants who were diagnosed with lung cancer | the measured case side of the discrimination | — |
| Serial plasma, matched participants who were not diagnosed with lung cancer during follow-up | the comparator the enrichment AUC is computed against | — |
| Matched primary tumour tissue, or the participant's somatic variant profile | **required, not optional**: the somatic variant set is what localises the channel transcript to the tumour, which is the precondition for the primary endpoint in aim 1; it is also what the tumour-expression gate in aim 3 is measured against | — |
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
