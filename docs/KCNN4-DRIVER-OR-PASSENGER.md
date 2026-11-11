# KCNN4: instructive, or a passenger of the transcriptional programme?

**Audit ID:** `driver-passenger-audit-2026-11`
**Date of run:** 2026-11-11
**Reproduce:** `python scripts/driver_passenger_audit.py --permutations 200`
**Artefact:** `results/driver_passenger_audit/driver_passenger_audit.json`
**Needs:** the local GEO cache under `data/`, which is gitignored. CI cannot run
it, so the check in CI is the verifier's reading of the committed artefact.

---

## 1. The question

The programme's readout rests on an ion channel marking the relapse-competent
state. Before a mechanistic collaborator is asked to test whether that mark is
*instructive* — whether the electrical state causes the transcriptional state
— one question has to be answered with what is already in this repository:

> **Is KCNN4's elevation in state cells part of the transcriptional programme
> that defines the state, or is it a separate axis that the programme does not
> explain?**

The two answers point at opposite collaborations. If the channel is a
programme output, the "electrical readout" is a shadow of a transcriptional
programme, and a collaborator in bioelectricity has nothing to add. If the
channel is a separate axis — or shares an upstream cause with the programme —
then it is the one quantity in this programme that a plasma assay could read
that a transcriptome panel could not.

## 2. Why it has to be settled first

An invitation to a mechanistic collaborator is a request to put their name on
a question. If this repository's own data already undercuts the premise of
that question, the invitation is not honest, and the answer would arrive
after the name was on it. The EEMS application period closes on 18 February,
so the question has to be settled before the application, not after it.

## 3. What was measured

Two measurements, both from the public deposits already cached here and from
nothing else.

**Within state cells.** Within a library's state cells, does a channel's
expression rise with the strength of the transcriptional programme, once cell
complexity is held constant? The test is a Mantel–Haenszel chi-square for the
channel's detection odds at high versus low programme score, stratified by
decile of detected genes, pooled across libraries with Stouffer's method, and
calibrated by permutation within each library. The stratification variable is
the number of detected genes, not total counts: the programme score is a mean
over six genes' detection, so a cell that detects more genes scores higher
whatever its programme is. Stratum count adapts to the library, because a fixed
ten strata left every library under three hundred state cells contributing
nothing.

**Across libraries.** Across libraries, does the channel's state-versus-tumour
fold track the programme's own state-versus-tumour fold? Both are ratios of
means over the same cells, so estimation noise attenuates both equally and
cannot manufacture an association between them.

Two controls travel with every test. A gene that is *in* the programme score
is a power control: if the machinery cannot find it, it cannot find anything.
A housekeeping gene is a specificity control: if it shows the same coupling
as the channel, the coupling is an artefact of depth. The permutation null is
narrow, because shuffling within a library leaves that library's contribution
intact, so the effect is also reported in units of that null's spread.

**The two cohorts.** GSE353299 (NSCLC, 25 libraries) defines the state by
KRT17 and its programme is the basaloid programme; KRT5 and KRT6A are left out
of the score because they are also in that dataset's malignant marker module,
which would make the score circular with the cell-type call. GSE299684 (SCLC,
15 libraries) defines the state by YAP1 and validates it against the
published surface-target signature, CD276, TACSTD2 and ERBB2 up, DLL3, SEZ6
and CEACAM5 down — an axis independent of the ion channels under test.

## 4. The result, in the cohort where the controls hold

GSE353299, nine libraries with enough state cells to contribute.

| Gene | Role | z | Effect | p |
|---|---|---:|---:|---:|
| **KRT14** | power control (in the score) | 15.70 | **29.3 sd** | 0.005 |
| KRT15 | in the score | 31.42 | 54.3 sd | 0.005 |
| **ACTB** | specificity control (housekeeping) | -0.10 | **-0.5 sd** | 0.82 |
| **KCNN4** | candidate channel | **5.15** | **6.8 sd** | **0.005** |
| PIEZO1 | candidate channel | 0.85 | -1.5 sd | 0.93 |
| CACNA1E | candidate channel | -0.24 | -0.6 sd | 0.60 |
| KCNA3 | candidate channel | 0.32 | 0.7 sd | 0.42 |
| TMEM150C | candidate channel | 1.00 | 0.2 sd | 0.39 |
| STOML3 | candidate channel | 0.92 | 1.8 sd | 0.045 |
| PIEZO2 | candidate channel | 0.85 | 1.5 sd | 0.075 |

The machinery finds the genes that are in the score, finds nothing in the
housekeeping gene, and finds KCNN4 at 6.8 times the null spread.

**In EGFR-mutant NSCLC state cells, KCNN4's expression co-allocates with the
basaloid programme beyond what cell complexity explains.** Across libraries
the channel's fold does not track the programme's strength (rho 0.333, p 0.37,
nine libraries, no power), which is expected: the library-level fold is
dominated by estimation noise — the same biology gives per-library folds from
0.0 to 64.2 — and is not what this question is about.

The other channels' nulls are worth stating carefully and are **not**
evidence that they are selectively uncoupled: a channel that is not elevated
in the state cannot co-vary with a programme it does not participate in. Only
KCNN4 is elevated in this cohort's state, so only KCNN4 can be tested this
way. The discriminating power is in the perturbation, not in this comparison.

## 5. The cohort where the controls do not hold

GSE299684, five libraries. The power control is found (CD276, z 11.13), and so
is KCNN4 (z 6.65, 10.0 sd) — but **the specificity control is found too**
(ACTB, z 3.15, 5.1 sd, p 0.005). A housekeeping gene that couples with the
programme score means the test is measuring depth, not coupling.

The cohort's numbers are therefore **not interpretable**, and none of them is
quoted as a finding. Reducing the programme score to its up genes alone, to
test whether the down-gene term was the cause, does not fix it: ACTB stays
coupled (z 2.54). The SCLC result is recorded as uninterpretable rather than
as weak support.

## 6. What the result does and does not settle

**Settled.** In the cells where the readout works, the channel's expression
co-allocates with the transcriptional programme that defines the state. The
mark is not an independent axis in these cells.

**Not settled.** Causation, and the reason matters. Co-expression is equally
compatible with two stories:

- *passenger.* KCNN4 is a transcriptional output of the basaloid programme, a
  downstream consequence of the state, and the electrical framing is
  decoration on a transcriptional marker.
- *shared upstream cause.* Both the channel and the programme are downstream of
  something else — a bioelectric state, say — and co-expression is exactly
  what that would look like. This is the reading a bioelectricity
  collaborator would bring, and the public data here cannot exclude it.

**What it changes.** The invitation to a mechanistic collaborator cannot be
the claim that the electrical mark is a separate axis; this repository's own
data does not support that claim for the one marker that works. What it can
be is a sharper question, with a clean falsifiable prediction — see the next
section.

## 7. The consequence for the plasma arm

If the passenger reading is right, a plasma panel that measures the channel
carries no information a panel measuring the programme would not carry
better: the programme's own transcripts are keratins — KRT17, KRT5, KRT6A,
KRT14, KRT15 — and they are far more abundant than the channel, so the
assay would be easier, not harder. The programme's claim would then be that
the channel reports the state *earlier* than the programme does, which is a
finer claim than "the channel is electrical", and one that no public data
here can settle either.

If the shared-upstream-cause reading is right, the channel could in principle
report an upstream state that the downstream programme has not yet shown, and
the assay makes sense as written.

**So the premise of the plasma arm is conditional on the answer to the
perturbation experiment.** That is a reason to run it before the EEMS
application rather than after, and it is not a reason to stop.

## 8. The proposition, stated so that it can be falsified

> **P1.** KCNN4's elevation in the relapse-competent state is a transcriptional
> output of the basaloid programme, not a separate electrical axis.
>
> **P2.** If P1 is false — if the channel and the programme share an upstream
> cause — then the channel's plasma readout can report the state earlier than
> the programme's own transcripts can, and the assay specification's premise
> holds.

**Public-data predictions.** If P1 is true, the channel's elevation should
track the programme's own strength at the library level as well as within
cells, and a channel that is not part of the programme should not track it.
The within-cell result above is consistent with P1; the library-level test
has no power at nine libraries and is not yet able to discriminate.

**The natural experiment still to run.** The state cells carry copy-number
divergence, and a gene amplified in the state would be elevated for a reason
that has nothing to do with the programme. The copy-number audit
([`KCNN4-COPY-NUMBER.md`](KCNN4-COPY-NUMBER.md)) has since run: a regional or
genome-wide gain is excluded — the KCNN4 region rises ×1.05 while the gene
rises ×3.53 — but a *focal* amplification of the gene itself cannot be
separated from transcriptional regulation in RNA, and would need DNA. That
is the same tumour profiling the scoping inquiry already asks about, so the
question is answerable in the cohort if the cohort has it.

**The experiment only a laboratory can run, and the falsifiable prediction.**
In tumour cell models that carry the state, perturb KCNN4 — knock it down,
or force it up — and ask whether the basaloid programme and the
drug-tolerant phenotype follow.

- If knocking KCNN4 down collapses the YAP1-positive programme and the
  drug-tolerant phenotype, the channel is **instructive**: P1 is false, P2
  holds, and the plasma arm's premise is sound.
- If the programme and the phenotype are unchanged, the channel is a
  **passenger**: P1 is true, and the plasma arm has to be re-stated as a
  transcriptional readout that happens to use a channel transcript.

Either answer is a result. Neither requires a new cohort, and both are
available before the EEMS deadline to a laboratory that already works with
ion channels.

## 9. What would change this document

- A local copy-number estimate at the KCNN4 locus (section 8).
- A perturbation result, from a laboratory (section 8).
- More libraries in the GSE299684 cohort, which would let the specificity
  control be diagnosed rather than the cohort being set aside.
- The across-library test, at enough libraries to have power.
