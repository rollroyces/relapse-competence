# Localisation audit: can per-molecule attribution rescue the plasma readout?

**Audit ID:** `localisation-audit-2026-11`
**Date of run:** 2026-11-12
**Datasets:** the measured fold and state fraction from the committed artefacts
**Reproduce:** `python scripts/localisation_audit.py --patients 800`
**Artefacts:** `results/localisation_audit/localisation_audit.json`,
`results/localisation_audit/localisation_audit.tsv`

---

## 1. What this audit asks

The leukocyte audit searched the space of *background-subtraction* statistics
and found that none of them clears K3. Subtracting the leukocyte reads and
then dividing by the participant's own tumour cfDNA share amplifies the noise
by the inverse of that share, and the two arms of an MRD-positive cohort sit
two orders of magnitude apart in it. The gate review's verdict of record is
that K3 fired.

The assay specification
([`PLASMA-ASSAY-SPECIFICATION.md`](PLASMA-ASSAY-SPECIFICATION.md) §4) says
the background must not be subtracted at all. The tumour-derived molecules
must be *counted* directly, using a per-molecule signature: a heterozygous
germline SNP that the participant's own tumour shifts. A leukocyte's channel
transcript carries the germline allele, not the tumour's shift of it, so a
leukocyte-derived molecule is never counted. The background is removed **by
construction** rather than inferred.

That mechanism had never been simulated. The leukocyte audit said so itself:

> The model does not simulate per-read tumour assignment, so the projection
> under localisation is an argument from the structure of the statistic
> rather than a simulated measurement.

This audit simulates it. The attribution model is **default-off**: with it off,
the simulator's output is byte-identical to the committed golden fixture, and
the published AUCs are reproduced exactly. The control is in
`results/localisation_audit/localisation_audit.json` under `control`.

---

## 2. The mechanism as modelled

Three quantities are added to the simulator, all default-off.

| Parameter | Meaning |
|---|---|
| `attribution_rate` | The probability that a tumour-derived channel-transcript molecule carries an informative tumour signature. The specification leaves this to the pilot, so it is swept. |
| `informative_position_rate` | The probability that a participant has at least one informative position at all. The specification's first stop rule is about this number. |
| `informative_positions_mean` | How many informative positions a participant has, given one or more. One is the single-transcript case; more is the multi-gene fallback. |

The attributable reads are drawn by **thinning** the channel reads, not by an
independent Poisson: the thinning rate is the tumour's share of the channel
signal times the participant's attribution rate. The attributable molecules are
therefore a genuine subset of the channel molecules, and a leukocyte-derived
molecule can never be among them.

Two statistics are computed, and the difference between them is the second
finding of this audit:

- **`auc_localised`** — attributed reads over the mutation channel's raw
  per-locus VAF. This is the literal formula in §5 of the specification.
- **`auc_localised_corrected`** — the same numerator over the participant's
  *estimated tumour cfDNA fraction*, which is the raw VAF with the
  sequencing-error floor removed.

The floor sits in the denominator of both statistics but only in the numerator
of the published one. So the published statistic has the floor in both places
and the floor partly cancels, while the localised one has it in the
denominator only. That asymmetry has to be handled, and §4.1 of the
specification already asks for the estimated fraction as the denominator, so
the corrected form is the specification's own requirement rather than a
departure from it.

---

## 3. The control: the statistic measures the state, not the burden

This is the finding that makes the rest readable. The audit runs a cohort
whose two arms carry the **same** state fraction, so any discrimination left
over is burden rather than state.

| Configuration | Statistic | Realistic state | Matched state |
|---|---|---:|---:|
| NSCLC / KCNN4 | raw | 0.0057 | 0.0068 |
| NSCLC / KCNN4 | localised | 0.9964 | 0.9693 |
| NSCLC / KCNN4 | **localised, floor-corrected** | **0.9091** | **0.5170** |
| SCLC / KCNN4 | localised, floor-corrected | 0.5373 | 0.5329 |
| SCLC / PIEZO1 | localised, floor-corrected | 0.5404 | 0.5383 |

Read the third row. The floor-corrected statistic separates relapsers from
non-relapsers at **0.9091** when the state differs, and collapses to
**0.5170** — chance — when the state is matched away. It is measuring the
state.

Read the second row and the two SCLC rows, and the picture changes. The
raw-VAF version of the localised statistic scores 0.9693 even with the state
matched away: it is picking up burden, not state, and it does so because the
floor is in its denominator but not its numerator. The floor-corrected version
has no such residual. **The raw-VAF form of the localised statistic would
have passed K3 for the wrong reason.**

The two SCLC configurations score 0.53–0.54 in the realistic case, which is
chance. They clear their thresholds in the published model on burden, not on
state: the per-patient audit already found that the SCLC readout does not
survive per tumour. The attributed statistic does not rescue them, and it does
not pretend to.

---

## 4. The result: per-molecule attribution clears K3 for the NSCLC readout

At the published operating point (200,000×, 200 loci, 25% of the read budget
on the electrical channel), in the bulk-plasma regime (leukocyte fraction
0.99), with every participant carrying an informative position:

| Configuration | raw AUC | localised AUC | localised, floor-corrected | K1 (>0.60) | K3 (>0.65) |
|---|---:|---:|---:|:--:|:--:|
| NSCLC / KCNN4 | 0.0057 | 0.9964 | **0.9091** | pass | **pass** |
| SCLC / KCNN4 | 0.0057 | 0.9888 | 0.5373 | fire | fire |
| SCLC / PIEZO1 | 0.0057 | 0.9776 | 0.5404 | fire | fire |

The raw statistic inverts, exactly as the leukocyte audit found. The
attributed statistic does not invert, and for the one configuration the
programme has a readout for, it clears both thresholds with margin.

**The attributed statistic is also insensitive to the leukocyte compartment**,
which is the structural claim the mechanism makes. Across the bulk-plasma
regimes (leukocyte fractions 0.5, 0.9 and 0.99), the NSCLC corrected AUC
moves only between 0.9043 and 0.9091, while the raw AUC sits at 0.0053
throughout. The compartment cannot reach the numerator, so it cannot invert
the statistic.

The compartment-free regime is reported separately, because it is not
comparable. With no compartment there is no leukocyte signal, so the
sequencing-error floor sits in the numerator as well as the denominator, and
the two statistics are not the same quantity. There the raw statistic is
0.9929 and the floor-corrected one 0.9352. The comparison that matters is
within the bulk-plasma regime, and there the raw statistic inverts while the
attributed one does not.

---

## 5. What it costs

**The attribution rate.** The floor-corrected AUC at the operating point, as
the attribution rate rises (NSCLC/KCNN4, bulk plasma, every participant
informative):

| Attribution rate | floor-corrected AUC | K3 |
|---:|---:|:--:|
| 0 (attribution off) | undefined | — |
| 0.01 | 0.7848 | pass |
| 0.05 | 0.8303 | pass |
| 0.10 | 0.8308 | pass |
| 0.25 | 0.8772 | pass |
| 0.50 | 0.9028 | pass |
| 1.00 | 0.9091 | pass |

Even a one-per-cent attribution rate clears K3 at the published depth. The
mechanism is not fragile at the statistic level; it is fragile at the
participant level, which is the next row.

**The informative positions.** The fraction of MRD-positive participants with
at least one informative position is the applicability rate. It does not
change the AUC among the participants the readout applies to (0.9098 at 50%
applicability, 0.8900 at 70%, 0.9105 at 90% for NSCLC/KCNN4), because the
statistic is computed over that subset. What it changes is how much of the
cohort the assay can speak about at all. The specification's first stop rule
requires at least 70% of participants with a measurable tumour cfDNA fraction
to have one.

**Depth.** Depth buys accuracy but not feasibility: at a 1% attribution rate,
the corrected AUC is 0.7848 at 200,000×, 0.8841 at 2,000,000× and 0.9047 at
20,000,000×. Since the attribution rate cannot be bought with depth, and
since a hundredfold depth increase does not change the verdict, the published
operating point is sufficient if the attribution works at all.

---

## 6. What this changes, and what it does not

**It changes.** The gate review's K3 verdict stands for the *bulk* statistic:
the readout as modelled does not survive the leukocyte compartment, and that
is not in dispute. But the specification's own prescribed correction had never
been simulated, and it turns out to work. For the one configuration the
programme has a readout for — KCa3.1 in EGFR-mutant NSCLC — per-molecule
attribution clears K1 and K3 at the published operating point, with the
attributed statistic insensitive to the leukocyte compartment by construction.

**It does not change.**

- **Nothing here is a measurement.** Every number here is a projection from
  the simulator, and the same kind of projection the leukocyte audit was
  criticised for. The specification's §10 already says the published AUCs are
  an upper bound for a localised assay; this audit quantifies that upper
  bound and identifies what has to be true for it to be approached.
- **The attribution rate is not measured.** It is swept, and the pilot has to
  measure it (§9, step 3). The finding is that the statistic clears K3 across
  the whole plausible range, so the pilot's job is to establish whether the
  mechanism is *available*, not whether the arithmetic works.
- **The informative positions are not measured.** The applicability rate is
  swept, and the specification's first stop rule is the operative constraint.
- **The SCLC candidates do not come back.** They were never a readout for
  this programme — the per-patient audit had already excluded them — and the
  attributed statistic does not change that.
- **The matched-state control is a control, not a finding about the
  literature.** It shows this statistic measures state in this model. It does
  not show the state fraction in a real MRD-positive cohort separates the way
  the simulator assumes.

---

## 7. Limitations

- The leucocyte compartment is a single parameter: the share of the
  electrical locus's signal that is leukocyte-derived. It does not model the
  cfRNA transcript pool's composition, so it is a bounding device rather than
  a measurement.
- The attribution model treats the informative signature as a property of the
  participant and the panel, not of the cfRNA fragmentation. The
  specification's §10 already records that the requirement that the
  informative SNP and the channel position fall in the same fragment is
  assumed, not modelled. The `attribution_rate` parameter stands in for that
  and for the tumour's shift being per-molecule identifiable, which the
  specification notes is true of a somatic variant but not of loss of
  heterozygosity on its own.
- The informative positions are drawn independently of the state fraction and
  of the arm. If the presence of an informative position correlates with the
  tumour's burden or with the state, the applicability rate and the AUC
  among the applicable would both move.
- The measured fold and state fraction come from the committed artefacts, and
  the numbers here inherit whatever those carry.
- Nothing in this audit uses a real plasma sample.

---

## 8. Reproducing

```bash
python scripts/localisation_audit.py --patients 800              # the full sweep
python scripts/localisation_audit.py --patients 800 --control-only  # what CI runs
```

The control reproduces the three published operating-point AUCs exactly, and
the state control reproduces the matched-state figures in section 3. Both are
checked by `scripts/verify_report_consistency.py`, and the golden fixture is
checked to be unchanged with the attribution model off.
