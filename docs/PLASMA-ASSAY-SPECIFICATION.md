# The plasma assay specification

**Document status:** pre-specified, 2026-11-11
**Applies to:** the plasma arm of the relapse-competent state programme
**Parents:** [`LEUKOCYTE-AUDIT.md`](LEUKOCYTE-AUDIT.md),
[`PER-PATIENT-AUDIT.md`](PER-PATIENT-AUDIT.md),
[`GATE-REVIEW.md`](GATE-REVIEW.md),
[`plco-cdas-submission-package/`](plco-cdas-submission-package/README.md)

---

## 1. Why this document exists

Every plasma number this programme has published is a projection. The audit in
[`LEUKOCYTE-AUDIT.md`](LEUKOCYTE-AUDIT.md) found what the projection was
assuming: the plasma cfDNA pool was modelled as tumour-shed material plus a
1e-6 sequencing-error floor, so the electrical channel's signal was the
tumour's contribution alone. The audit's conclusion was that the readout as
modelled is a *tumour-purified* measurement, and that plasma is not
tumour-purified.

An assay design can only be specified once the thing being measured is
written down. It never was. The simulator calls the channel "ion-channel loci
read as a bulk feature" and gives it a per-locus VAF, while the tissue
measurement it is calibrated against is a *transcript* abundance ratio. The
leap between the two was never justified, and the audit made it visible,
because once the plasma pool has two compartments the leap stops working.

This document specifies the assay: what is measured, in what analyte, how the
signal is attributed to the tumour, what statistic is computed, and what would
stop the programme. It is written before any plasma is opened, and it is the
document the data-access applications are for.

## 2. The analyte

**The channel is read in circulating RNA. The mutation panel is read in
circulating DNA.**

| | Analyte | What it measures | Why |
|---|---|---|---|
| Electrical channel | **cfRNA** | the channel transcript's abundance in the plasma cfRNA pool, and which of those molecules are tumour-derived | The channel is a transcript: the tissue measurement is transcript expression, and only a transcript assay reports it. cfDNA cannot report expression at all, so a DNA library cannot carry this readout. |
| Mutation panel | **cfDNA** | tumour cfDNA fraction per participant, and the MRD flag | Somatic variants are tumour-specific, so this channel localises to the tumour without help. It is also the denominator of the enrichment statistic. |
| Leukocyte reference | **cfRNA** | the leukocyte compartment's abundance of the reference transcripts, in the same library | The background, measured rather than assumed. |

Two consequences of the split are stated here because they make the readout
harder than the model implies.

- **The channel and the mutation panel are different analytes.** They are
  therefore not affected by the same processes, and the tumour's cfRNA share
  is not the tumour's cfDNA share. In plasma, tumour-derived cfRNA is a
  smaller fraction of the pool than tumour-derived cfDNA, because circulating
  RNA is dominated by platelet and leukocyte transcripts. The dilution the
  audit found is therefore, if anything, worse in a real library than the
  model's single pool suggests.
- **The simulator's per-locus VAF is a proxy, not a description.** The model's
  electrical channel is a fraction of a pool of reads; a cfRNA channel locus
  is a transcript abundance. The audit's conclusions are unaffected, because
  they are about the *mixture* and the *statistic*, both of which are
  properties of proportions and counts rather than of the library type. The
  projection is an upper bound in either case, for the reason in section 5.

## 3. What is counted

For each participant, from the plasma cfRNA library:

- **The channel's transcript abundance**, at a fixed panel of positions in the
  channel transcript, normalised to the library's total transcript pool and
  to a set of reference transcripts whose expression does not move with the
  state.
- **The allele at each informative position**, so that the tumour-derived
  fraction of the channel's molecules can be counted rather than inferred.
- **The leukocyte reference transcripts' abundance**, in the same library, as
  the background and as a negative control.

Everything is done locally on the aliquots; no sequencing data is requested
from the data-access applications, and none is sent anywhere.

## 4. Localisation: the attribution must be per molecule, not per participant

This is the design decision the leukocyte audit forces, and it is the one
place where the assay can fail.

### 4.1 Why subtracting the background cannot work

The audit measured the reason. The statistic this programme uses is the
channel's per-locus signal divided by the mutation channel's, and the
mutation channel is tumour-specific while the electrical channel is not. The
noise in that ratio is therefore amplified by the inverse of the
participant's own tumour cfDNA share.

At the published operating point the two arms of the MRD-positive population
sit two orders of magnitude apart in that share:

| | Median tumour cfDNA share | Noise in the enrichment statistic |
|---|---:|---:|
| Relapsing arm | 3.67e-04 | about 1.2 |
| Non-relapsing arm | 1.68e-06 | about 265 |

The group difference the statistic has to resolve is 0.79 — the difference
between a state fraction of 0.392 and the 0.100 the simulator assumes for
the persistent arm. A non-relapsing participant's statistic carries a noise
of about 260 against a signal of 0.79. No read depth fixes that, because the
amplification is 1/s and s is set by the biology, not by the panel: the
audit searched 200,000x to 20,000,000x with reference sets from 5 to 50 loci
and the best reference-corrected AUC found was 0.5815 against a threshold of
0.65, and even a perfect subtraction of the background topped out at 0.5796.

**So the background must not be subtracted. The tumour-derived molecules must
be counted directly.**

### 4.2 The mechanism

Per-molecule attribution: a channel-transcript molecule is counted as
tumour-derived if it carries an informative signature, and informative means
**a heterozygous germline SNP that the participant's own tumour shifts** — by
loss of heterozygosity, or by a somatic variant on the other allele.

- The participant's **matched primary tumour** is what makes this possible.
  It establishes which germline SNPs are shifted in *this* tumour, and it
  establishes the channel's expression in it, which is the tumour-expression
  gate. This is why the matched tumour is a required element of the data
  request rather than an optional one.
- The informative SNP must fall within the same cfRNA fragment as the channel
  position. cfRNA fragments are longer than cfDNA fragments, which helps, but
  the number of informative positions inside a transcript's footprint is
  small, and that is the assay's binding constraint.
- **A tumour-shifted heterozygous SNP is therefore a property of the
  participant, not of the panel.** The panel can be chosen to maximise the
  chance of informative positions, and the pilot must measure how many
  participants actually have one.

### 4.3 If the transcript footprint carries no informative position

The fallback is a **multi-gene channel signature**: several channel
transcripts are read together, and the union of the participants' informative
positions across them is what carries the attribution. This is the same
reason the third-dataset audit required a tumour-expression gate rather than a
single-channel assumption, applied to the plasma side.

The pilot must establish which of the two applies before the programme
commits to the larger panel. Section 8's first stop rule is about exactly
this.

## 5. The statistic

**Estimand.** Within the pool of plasma-positive participants, the ability of
the channel's tumour-derived signal to separate those who progress from those
who do not. This is the discrimination a relapse-prediction assay has to
make, and it is the quantity the gate review's AUCs were computed for.

**Estimator.** For each participant, pooling the post-baseline draws:

```
channel_attributed_p = (channel-transcript reads carrying an informative
                        tumour signature) / (total channel-transcript reads)
```

and the enrichment for that participant is

```
enrichment_p = channel_attributed_p / (mutation channel's per-locus VAF)
```

The AUC of `enrichment_p` over relapsers against non-relapsers, within the
plasma-positive population, is the statistic. It is the same statistic the
programme has always used, with one change: the numerator is *counted*
tumour-derived rather than *inferred* by subtraction, so the noise is
proportional to the square root of the tumour's own share rather than to the
whole pool, and the division by the mutation channel cancels it as it did in
the published model.

**Thresholds.** The programme's own, fixed before any plasma is opened:

| Threshold | Value | Meaning |
|---|---:|---|
| K1 | 0.60 | the readout carries no information beyond tumour burden |
| K3 | 0.65 | the state cannot be inferred from plasma at the operating point |

**What is reported, always.** The raw (unlocalised) enrichment AUC is
reported alongside the attributed one, with the leucocyte reference signal, so
that the attribution's own contribution is visible and not assumed.

**The operating point.** 200,000x depth, 200 loci, 25% of the read budget on
the electrical channel, unchanged from the published one, with the panel
composition in section 6.

## 6. The panel

| Set | Loci | Job |
|---|---:|---|
| Mutation panel | 150 | tumour cfDNA fraction per participant; MRD flagging; the denominator of the enrichment |
| Channel positions | 38 | the channel transcript's abundance, and the allele at each position, so that the informative ones can be used for attribution |
| Leukocyte reference | 12 | the background, measured in the same library; the negative control |
| **Total** | **200** | 50 electrical, 25% of the budget, as published |

The leucocyte reference set is a **control and a normalisation check, not the
correction**. The correction is the molecular filter in section 4. This is the
audit's finding, and the reason the reference set cannot rescue the readout
however large it is made.

## 7. The controls

| Control | What it would show if the attribution is not working |
|---|---|
| Leukocyte reference positions | the unattributed channel signal is dominated by leukocyte material, which is the finding the audit rests on |
| Mutation panel | the participant's own tumour cfDNA fraction, and the MRD flag at ≥ 98% specificity; if the mutation channel fails, the denominator of the statistic is unusable |
| Germline sample from the participant | the germline allele fractions at the informative positions, without which the tumour's shift cannot be read |
| Matched tumour | which germline SNPs *this* tumour shifts, and the channel's expression in it |
| Dilution series | that the attributed signal scales with the tumour's cfDNA fraction rather than being a constant offset |
| Participants whose tumour does not express the channel | reported separately, never pooled: they are the tumour-expression gate |

## 8. The stop rules

Each is a condition under which the programme stops, is re-specified, or
reports its result as exploratory. The shape follows the research plan's kill
conditions: a threshold, a detection method, and a consequence.

| # | Stop rule | How it is detected | Threshold | Consequence |
|---|---|---|---|---|
| **S1** | The attribution is not available per participant | informative positions per participant, from the matched tumour and the germline sample | fewer than 70% of pilot participants with a measurable tumour cfDNA fraction have at least one informative position | the panel is re-specified as a multi-gene signature, or the plasma arm stops |
| **S2** | The attributed readout does not clear the programme's own bar | the attributed enrichment AUC on the pilot, at the operating point | below 0.65 (K3) | the plasma arm stops |
| **S3** | The panel cannot be afforded | the panel at the operating point, with the attribution and reference positions included, and the mutation channel's specificity | above 200,000x or 200 loci, or the mutation channel below 98% specificity | the assay is re-specified, and the change is recorded before the next pilot |
| **S4** | The readout does not apply to the target population | the channel's expression in the matched tumour, per participant | fewer than 50% of participants have a within-tumour fold of at least 1 | the programme stops offering the readout and reports the applicability rate |
| **S5** | The attribution is not better than the background | the attributed channel signal against the leukocyte reference signal, per participant | the attributed signal does not exceed the leukocyte reference by at least threefold | the attribution is declared uninformative and the arm stops |
| **S6** | The analysis moved after the data were opened | the versioned analysis plan against the commit that opened the data | any change to the pre-specified parameters, the panel, or the thresholds | the result is reported as exploratory and the programme's claim is withdrawn |

Two of these thresholds are the programme's own (S2 is K3; S3's mutation
channel specificity is the 0.98 the simulator has always been calibrated
to). The other three are design choices, and they are stated here as choices
rather than as findings.

## 9. The pilot

Before any efficacy analysis, on the first cohort with serial plasma:

1. Measure the **per-participant tumour cfDNA fraction**, from the mutation
   panel. This is the denominator the programme has never measured.
2. Measure the **per-participant state fraction** and its distribution across
   participants, from the attributed channel signal. The per-tumour audit
   showed this distribution to be decisive.
3. Measure the **attribution rate**: the fraction of participants with an
   informative position, and the number of informative positions each has.
   This is what decides whether the assay is the single-gene channel or the
   multi-gene signature.
4. Measure the **attributed enrichment AUC** at the operating point, and the
   leucocyte reference signal beside it.

The pilot is what S1, S2, S4 and S5 are evaluated on. The programme has
published projections for years; the pilot is the first measurement of the
quantities those projections assume.

## 10. What this specification does not establish

- **It does not establish that the assay works.** It states what would have
  to be true, and what would make it stop. The published AUCs are an upper
  bound for a localised assay; the pilot is the first measurement.
- **It does not settle which channel.** KCa3.1 in EGFR-mutant NSCLC is the
  readout that survives the per-tumour audit, but the pilot's channel set is
  chosen from the per-tumour measurements, and the panel must carry more than
  one transcript if the informative positions are too few in one.
- **It does not model the cfRNA fragmentation.** The requirement that the
  informative SNP and the channel position fall in the same fragment is
  assumed; the fragment-length distribution of the cohort's cfRNA is
  measured in the pilot, not assumed here.
- **It does not make the readout clinical.** Every number remains a
  measurement on a public deposit or a projection informed by one.

## 11. What the data-access applications are for

The applications request the material this specification needs, and the
specification has already changed what they request:

- **The matched primary tumour is required**, because it establishes which
  germline SNPs this participant's tumour shifts, and because it is the
  tumour-expression gate.
- **A participant germline sample is needed**, for the germline allele
  fractions at the informative positions.
- **The panel's mutation loci matter to the channel**, because the mutation
  channel is both the denominator and the source of the attribution.

## 12. Reproducing and checking

Every number this document quotes is machine-checked against the artefacts
it came from, in CI:

```bash
python scripts/verify_report_consistency.py
```

The leucocyte audit that forced this specification is
[`LEUKOCYTE-AUDIT.md`](LEUKOCYTE-AUDIT.md), and its artefacts are
`results/leukocyte_audit/`.
