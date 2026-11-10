# Proposal narrative

Attached to the CDAS data-only project proposal for PLCO. Written to be
published on the CDAS website once access is granted.

---

## 1. Background and rationale

The relapse-competent state is a drug-tolerant subpopulation of tumour cells
associated with relapse. It was defined transcriptionally: the paper that
describes it in relapsed small-cell lung cancer
([PMID 42019833](https://pubmed.ncbi.nlm.nih.gov/42019833/), deposited as
[GSE299684](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE299684))
names no ion channel. The cells that carry it abandon the neuroendocrine
programme of their tumour and adopt an epithelial-like, LCNEC-like state, and
in that paper they are a minority of the malignant compartment.

We have measured, in three public single-cell deposits, that this state is
nevertheless electrically marked, and that the marking is disease-specific.

- In relapsed small-cell lung cancer the state over-expresses Piezo1.
- In EGFR-mutant lung adenocarcinoma it over-expresses the potassium channel
  KCa3.1 (KCNN4) at a 2.97x detection ratio
  ([PMID 41741906](https://pubmed.ncbi.nlm.nih.gov/41741906/),
  [GSE353299](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE353299)),
  a target that has been nominated as a novel NSCLC therapeutic target
  elsewhere, and which has a clinical-stage antagonist
  ([PMID 40688096](https://pubmed.ncbi.nlm.nih.gov/40688096/)).
- A per-tumour audit of the same data shows that the KCa3.1 marking is
  carried within an individual patient's tumour in **20 of 23** EGFR-mutant
  NSCLC libraries, and in **7 of 7** residual-disease libraries measured, while
  the same within-tumour contrast does not hold in relapsed small-cell lung
  cancer, where most tumours carry too little state to read.

That last sentence is the reason for this application. The audit also showed
that the pooled statistics the field would have quoted — a state fraction of
0.104 and a per-cell fold of 2.55 for relapsed SCLC — are cell-count
weighted, that three libraries hold 86.4% of the state cells, and that the
channel's baseline expression differs by metastatic site by up to 65-fold. A
pooled number can be stable and still describe no individual patient. The
honest quantity is the distribution of the state across individual tumours,
and the state fraction of the tumour is what a plasma assay would read.

**None of this has been measured in blood.** Every plasma number this
programme has produced is a simulation whose inputs are tissue measurements.
When the programme's own pre-specified kill conditions were applied to that
evidence, the readout survived in EGFR-mutant NSCLC and failed in most
relapsed-SCLC tumours, and the surviving margin was thin. The decisive
uncertainty is not the channel and not the read depth; it is the
between-participant distribution of the state fraction, and the state fraction
of the MRD-positive patients who do not relapse, which no deposit we have
used measures.

## 2. Aims

**Aim 1 — measure the readout, localised.** Measure the *localised*
ion-channel enrichment of the state-bearing clone (KCNN4 and PIEZO1) in serial
plasma of participants who were diagnosed with lung cancer, against serial
plasma of matched participants who were not, counting only the channel-locus
reads that carry a tumour-specific somatic variant on the same molecule, and
test the pre-specified thresholds on the tumour-attributable enrichment AUC:
0.60 for the readout, and 0.65 at the operating point. The raw, unlocalised
enrichment is a pre-specified secondary analysis, reported with its own AUC,
because section 4 shows it inverts when the plasma pool carries leukocyte
DNA.

**Aim 2 — measure the quantities the simulation assumes.** Estimate the
per-participant tumour cfDNA fraction and the per-participant state fraction
and its between-participant distribution, from the somatic variants read in
the same library, so that the projection can be re-run against measured inputs
rather than assumed ones. The per-tumour audit shows the state fraction's
distribution to be decisive, and the leukocyte audit shows the tumour fraction
to be the denominator that has never been measured.

**Aim 3 — determine per-participant applicability.** Establish what fraction
of participants carry the state at a frequency a plasma assay can read, and
what fraction of their tumours express the channel, so that the panel design
carries a tumour-expression gate rather than a single-channel assumption. A
third public relapsed-SCLC deposit expressed neither channel at all, so a
single-channel assumption is not safe.

## 3. Data requested, and why each element is necessary

CDAS staff assess whether the requested data are available and necessary to
answer the research questions. Each element is listed with the aim it serves.

| Element | Aim | Why it is necessary | Available from PLCO |
|---|---|---|---|
| Serial plasma, participants who were diagnosed with lung cancer | 1, 2 | the case side of the discrimination, and the material the assay reads | yes, at screening visits |
| Serial plasma, matched participants who were not diagnosed with lung cancer | 1, 2 | the comparator against which the enrichment AUC is computed; without it there is no discrimination to measure | yes |
| Matched primary tumour tissue, or the participant's somatic variant profile | 1, 2, 3 | **required, not optional**: the somatic variant set is what localises the channel transcript to the tumour, which is the precondition for aim 1; it is also what the tumour-expression gate in aim 3 is measured against | yes, where archived |
| Date and site of diagnosis (Limited Data Set) | 1, 2 | the interval between the blood draw and diagnosis is the measurement the project turns on; the standard de-identified dataset removes the dates | yes, in a Limited Data Set |
| Treatment history | 2 | separates a treatment-emergent state from a pre-existing one | yes |
| Mortality and follow-up time | 1 | defines the outcome window for the non-progressing comparator | yes |
| Smoking history | 1, 2 | the dominant confounder of lung cancer risk and of baseline plasma features | yes |
| Visit dates of the blood draws | 1, 2 | aligns each plasma sample to the clinical timeline | yes |
| Sequencing data | — | not requested; the assays are run locally on the aliquots | — |

## 4. The assay design: the channel transcript has to be localised

This is the part of the design that a second audit of our own model changed,
and it is worth stating plainly, because it is what the requested material
has to support.

Our plasma model originally had no leukocyte compartment: the cfDNA pool was
tumour-shed material plus a sequencing-error floor, so the channel's signal
was the tumour's contribution alone. In bulk plasma that is not the case. Most
cfDNA is leukocyte cfDNA, and KCa3.1 is expressed in immune cells -- the
tumour's state-bearing cells express it at 2.40 times the level of the
neighbouring immune cells, but in relapsed SCLC the tumour's *average* Piezo1
level is below the immune cells' level. Reading the channel transcript
without localisation therefore measures leukocyte material.

At the tumour DNA fractions a real MRD cohort sits at, the state's share of a
bulk channel measurement is about two per cent in EGFR-mutant NSCLC and half
a per cent in relapsed SCLC. Adding a leukocyte compartment to the model took
the published enrichment AUC from 0.9929 to 0.0053: not degraded but
*inverted*, because the leukocyte term divided by the tumour's own cfDNA
share is inversely related to tumour burden, and relapsing patients carry more
tumour. Subtracting a leukocyte baseline before the division left 0.5111,
which is chance: the tumour's contribution was about 1,700 reads out of ten
million, against a counting noise of about 3,200 on the difference of two
Poisson counts of five million each.

Three design elements follow, and they are what the data request is for:

1. **Localise the channel transcript to the tumour.** Only reads at the
   channel locus that also carry a tumour-specific somatic variant on the
   same molecule are counted. This removes the leukocyte contribution *before*
   the measurement instead of correcting it afterwards, and the audit found
   only this version workable. It requires the participant's own somatic
   variant set, which is what the matched primary tumour provides.
2. **Estimate each participant's tumour cfDNA fraction** from the somatic
   variants the mutation panel already reads. This is the denominator the
   enrichment statistic divides by, and it is a quantity the programme has
   never had a measurement of.
3. **Include leukocyte reference loci** -- positions in transcripts the immune
   cells express and the tumour does not -- so that each library's leukocyte
   contribution and its tumour fraction are measured in the same sample rather
   than assumed, and a library whose background is inconsistent with its
   tumour fraction can be caught.

The third element is a check, not a fix, and we tested it rather than
assuming it. Re-allocating the panel to carry a leukocyte reference set and
re-deriving the operating point against it does not rescue the readout: no
configuration between 200,000x and 20,000,000x, with reference sets from 5 to
50 loci, brings the reference-corrected enrichment AUC above 0.58, against a
threshold of 0.65. The reason is structural rather than budgetary -- the
statistic divides by the patient's own tumour cfDNA share, so an error in the
background estimate is multiplied up, and the non-relapsing arm of an
MRD-positive cohort sits two orders of magnitude lower in tumour cfDNA than
the relapsing arm. Subtracting the background *perfectly*, with foreknowledge,
does not help either. Only localisation does, because it restores the
proportionality the statistic depends on.

Our published projection assumes that localisation works, and is therefore an
upper bound on what the assay can achieve. It also holds only for a localised
assay at the right effective depth: localisation keeps the reads that happen
to carry a variant, so the quantity that sets the readout's precision is the
depth multiplied by the localisation rate, and the localisation rate is set by
how many tumour-specific variants the mutation panel reads per participant.
The model does not yet simulate per-read tumour assignment, so the projection
cannot be tightened until the assay has been run on real plasma.

## 5. The analysis is pre-specified

The analysis is fixed before the data are opened, and the code is public.
The following are already fixed and will not be re-tuned after the data are
opened:

- **The panel and operating point.** 200,000x sequencing depth, 200 loci, with
  25% of the read budget allocated to the ion-channel panel. The sensitivity
  analysis across the full grid — 5,000x to 500,000x, 50 and 200 loci — is
  pre-specified as a sensitivity analysis, not as a search.
- **The thresholds.** Enrichment AUC of 0.60 for the readout, and 0.65 at the
  operating point. These are the programme's own pre-declared kill
  conditions, fixed before the PLCO data existed.
- **The estimand.** The enrichment AUC is computed within the pool of
  plasma-positive participants, separating those who progress from those who
  do not, which is the discrimination a relapse-prediction assay has to make.
- **The statistic.** The primary statistic is the **tumour-attributable**
  enrichment: only the channel-locus reads that carry a tumour-specific
  somatic variant on the same molecule are counted, and the result is divided
  by the mutation channel's per-locus VAF. The raw, unlocalised enrichment is
  a pre-specified **secondary** analysis, reported with its own AUC, because
  the audit in section 4 shows it inverts when the plasma pool carries
  leukocyte DNA.
- **The panel.** Loci are allocated to the mutation channel, the ion-channel
  channel and the leukocyte reference set, and the allocation is fixed before
  any data are opened. The published operating point was derived without the
  reference set, and the reference set has been added on the strength of the
  audit in section 4, which shows it is a check on each library rather than a
  correction to the readout.
- **The per-patient applicability rule.** A tumour is informative for the
  readout when its measured state fraction exceeds the fraction the assay can
  read at the operating point; the readout's sensitivity across participants
  is reported as a distribution rather than as a single cohort figure.
- **The analysis of the state fraction.** The per-participant state fraction
  is estimated from the plasma assay and its distribution is reported with
  its quantiles, not only its mean, because the per-tumour audit showed that
  the mean hides the heterogeneity that decides applicability.

What will **not** be done: no selection of participants, timepoints or
thresholds after the data are opened; no tuning of the panel to the cohort;
no post-hoc substitution of a different channel.

## 6. Data handling and security

- All data are downloaded into an access-controlled institutional storage
  location under the PI's control. Nothing is sent to a third-party service
  and no patient-level data leaves the institution.
- The data are not used to identify or contact any participant or physician,
  and no attempt will be made to re-identify any participant.
- The analysis code, the pre-specified parameters and the published figures
  are public. The participant-level data are not, and are not released.
- Access is requested for 12 months, matching CDAS's access term, and the
  project will be closed out rather than extended by default.

## 7. Limitations we would rather state than have the review find

- **PLCO is a screening cohort.** Its plasma is collected at screening visits
  before diagnosis, not after treatment. This project therefore measures the
  discrimination between participants who progress and those who do not in a
  pre-diagnosis window. It does not measure a post-treatment residual-disease
  readout, and it is not claimed to.
- **The state fraction is a tumour quantity.** The plasma assay measures the
  state-bearing clone's contribution to circulating tumour DNA, and estimating
  a per-participant state fraction from it is a modelling step. That step's
  assumptions are stated in the public code and tested against the tissue
  measurements already in hand.
- **The readout is not universal.** In a third public relapsed-SCLC deposit
  the tumour expressed neither channel. Aim 3 is designed to detect and
  quantify that, not to assume it away.
- **Lung cancer is a subset of the cohort.** PLCO is a multi-cancer
  screening trial; the request is restricted to the lung stratum.
- **A tumour-expression gate will be needed** for any eventual assay. This
  project measures what that gate should be based on; it does not validate an
  assay.
- **The projection assumes the localisation step works.** Section 4 shows
  that an unlocalised readout of a channel that immune cells also express
  measures leukocyte material, and that correcting for it afterwards is not
  enough -- the re-derived panel does not clear the threshold at any depth we
  searched. The published AUC is therefore an upper bound, and the model does
  not simulate per-read tumour assignment, so the number cannot be tightened
  before the assay has run on real plasma.
- **The localisation rate is not modelled.** It depends on how many
  tumour-specific variants the mutation panel reads per participant, and it
  divides the effective depth. The projection is for an assay that localises
  well; an assay that localises poorly pays for the mutation panel's depth
  twice.

## 8. Timeline

| Stage | Duration |
|---|---|
| CDAS staff assessment and any request for more information | weeks |
| NCI Data Access Committee review | weeks to a few months |
| Data Transfer and Use Agreement executed by the Signing Official | days |
| Data delivery | the CDAS instructions give 1–4 weeks from approval for a data-only project |
| Assays run on the delivered aliquots | to be scoped, once the number of usable samples is confirmed |
| Analysis, pre-specified, and submission of the manuscript | 3–6 months after delivery |

## 9. Publication plan and data availability

Results will be submitted for peer-reviewed publication whether or not they
support the hypothesis, including the per-participant distribution and its
relation to the pre-specified thresholds. The analysis code, the
pre-specified parameters and every figure behind the manuscript are public
from the outset, so that the published numbers can be recomputed. The
participant-level data will not be released.

## 10. Conflict of interest

None to declare for this project. The investigators have no financial interest
in the PLCO data, in the assay platform, or in any therapeutic product
directed at the channels measured. No commercial sponsor is involved in the
work proposed here. The analysis is registered as pre-specified analysis with
a public code base before the data are opened.

## 11. References

1. Stewart et al. Relapsed small-cell lung cancer with a YAP1-positive
   drug-tolerant state. [PMID 42019833](https://pubmed.ncbi.nlm.nih.gov/42019833/);
   [GSE299684](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE299684).
   Preprint version: [PMID 41279637](https://pubmed.ncbi.nlm.nih.gov/41279637/),
   doi:10.1101/2025.10.21.683746.
2. EGFR-mutant NSCLC single-cell cohort. [GSE353299](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE353299);
   KCa3.1 as a nominated NSCLC target, [PMID 41741906](https://pubmed.ncbi.nlm.nih.gov/41741906/).
3. Elexacaftor directly blocks KCa3.1. [PMID 40688096](https://pubmed.ncbi.nlm.nih.gov/40688096/).
4. The public analysis that produced the measurements above, including the
   per-tumour audit: `rollroyces/relapse-competence`,
   [`PER-PATIENT-AUDIT.md`](https://github.com/rollroyces/relapse-competence/blob/main/docs/PER-PATIENT-AUDIT.md).
