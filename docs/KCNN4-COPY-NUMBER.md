# Is KCNN4's elevation in the state a copy-number effect?

**Audit ID:** `kcnn4-copy-number-audit-2026-11`
**Date of run:** 2026-11-11
**Reproduce:** `python scripts/kcnn4_copy_number_audit.py --permutations 200`
**Artefact:** `results/kcnn4_copy_number/kcnn4_copy_number.json`
**Needs:** the local GEO cache under `data/`, which is gitignored. CI cannot run
it, so the check in CI is the verifier's reading of the committed artefact.
**Companion:** [`KCNN4-DRIVER-OR-PASSENGER.md`](KCNN4-DRIVER-OR-PASSENGER.md)

---

## 1. The question, and why it is the boring objection

The driver-versus-passenger audit found that KCNN4's expression co-allocates
with the state's transcriptional programme inside state cells, and left the
direction of causation open. One of the two ways that could go is
copy-number. If the state carries an amplification that includes KCNN4, the
channel's elevation is a consequence of the genome rather than of the
programme, and no amount of transcriptional reasoning would separate them.

It is the objection worth killing first, because it is the one that would
make the programme's framing wrong for a reason that has nothing to do with
biology.

## 2. Why the obvious statistic cannot be used

A gene that is transcriptionally upregulated has its own expression raised
relative to its positional neighbours, **exactly as an amplified gene
does**. "KCNN4 is high relative to its neighbours" therefore cannot tell
amplification from regulation, and this audit does not claim it can.

What can be told apart is a *locus-specific* copy-number event: a region of
the genome that is denser in the state cells than the genome as a whole.
That is the statistic here, and it is the one a copy-number caller uses —
the local density at a locus, as a log-ratio against the cell's
genome-wide baseline.

The comparison is made per library, between three quantities: the gene's own
expression, the mean expression of the fifty positional neighbours on either
side of it, and the genome-wide baseline taken as the median over three
hundred control loci spread across the genome. All three are ratios of means
in linear space, the convention the repository's published folds use.

**Validation.** The per-library folds this pipeline computes reproduce the
published `KCNN4_linear_fold` exactly — ×16.33, ×32.16, ×3.31, ×6.16,
×3.50 and the rest, to four decimals, against
`results/per_library_folds/per_library_folds.tsv`. The code path is the
repository's, not a re-implementation of it.

## 3. The result

GSE353299, EGFR-mutant NSCLC, sixteen libraries, all sixteen comparable.

| Quantity | Fold in the state cells | |
|---|---:|---|
| **KCNN4 itself** | **×3.53** (median over libraries) | the published fold is 3.698 |
| **Its ±50-gene neighbourhood** | **×1.05** (maximum ×1.45) | the region the gene sits in |
| **Genome-wide baseline** | ×1.04 | 300 control loci |
| Locus log-ratio change, percentile among control loci | 0.579 (null 0.498 ± 0.077) | **p = 0.139** |

In **fifteen of the sixteen** libraries the gene rises while its own
neighbourhood does not; the neighbourhood rises more than the gene in one.

GSE299684, relapsed SCLC, nine libraries: the gene does not mark the state
here (median own fold ×0.58, which is the published finding that the mark
fails in SCLC), the neighbourhood is flat at ×0.96, and the locus's
log-ratio change is *below* the median of the control loci (percentile 0.395,
p = 0.83).

## 4. What this rules out, and what it does not

**Ruled out.**

- A **regional** copy-number gain covering the KCNN4 locus. The region rises
  ×1.05 — at most ×1.45 in one library — while the gene rises ×3.53. A fourfold
  copy gain in the region would show as a fourfold rise in the neighbourhood.
  It is not there.
- A **genome-wide** change in the state cells. The baseline is ×1.04.
- A **locus-specific regional copy-number event** at KCNN4. The locus's
  log-ratio change sits at the 58th percentile of three hundred control
  loci, p = 0.139, and in SCLC below the median.

**Not ruled out.** An event that affects **the gene itself** rather than its
region — a focal amplification of KCNN4 — would raise the gene without
raising the neighbourhood, and would therefore look exactly like what is
observed. And the positional proxy this repository computes cannot see such
an event at all, because smoothing replaces a gene's value with its
neighbours' mean by construction. The repository's own note on the proxy
says it "does not reproduce the paper's copy-number-diversity comparison
between YAP1(+) and YAP1(-) cells, which is a finer metric than this proxy
computes".

**And here the limit is not just technical.** Transcript counts cannot
distinguish a focal amplification of a gene from transcriptional
upregulation of that gene: both raise the gene's counts above its
neighbours'. Separating them needs DNA.

## 5. So where does the copy-number route stand?

Narrowed, not closed. The broad and regional explanations are gone. What
remains is the single-gene form, and it is not answerable from RNA at all.

**Which means it is answerable from the cohort.** The scoping inquiry's
second message already asks, of the matched tumour material: *"What
profiling exists for that tissue: whole-exome sequencing, whole-genome
sequencing, or targeted sequencing?"* — and a copy-number profile at the
KCNN4 locus in the matched primary tumours would settle it directly, in the
same tissue, by the same route the data-access application is already
asking for. If the answer is that no such profiling exists, the question
closes on the evidence rather than on the argument: there is no DNA, so no
DNA-level amplification can be claimed or excluded, and the perturbation
experiment becomes the only remaining route.

## 6. What this changes

- **The programme's framing survives the boring objection.** A region-wide or
  genome-wide copy-number artefact does not explain the elevation, so
  "electrically marked" is not a copy-number artefact in disguise.
- **The perturbation experiment becomes more important, not less.** The
  remaining passenger route is the one the public data cannot reach, so the
  laboratory question in
  [`PERTURBATION-QUESTION.md`](PERTURBATION-QUESTION.md) now stands as the
  only route that closes it — and it is the route a collaborator can actually
  run.
- **The scoping inquiry gains a reason.** Its question about the tumour's
  profiling is now attached to a specific measurement that would settle a
  specific doubt, which is what makes an answer worth having.

## 7. What would change this document

- A copy-number profile at the KCNN4 locus from DNA, in the matched primary
  tumours, if the cohort has WES or WGS (the scoping inquiry's second
  message asks).
- A focal-amplification caller that works on the raw read matrix rather than
  on the smoothed expression, which would have to be built rather than
  reused.
- More libraries: the per-library comparison is robust as it stands, but the
  pooled ratio of means moves with the library set, because the gene's
  expression in tumour cells is near zero in many libraries and the ratio is
  then dominated by a few of them.
