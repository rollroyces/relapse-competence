# D0 — target therapeutic-window audit

**Audit ID:** `d0-target-window-2026-11`
**Date of run:** 2026-11-06
**Protocol:** a decision rule fixed in the script, applied identically to every target
**Reproduce:** `python scripts/d0_window_audit.py --outdir results/d0_window_audit`
**Machine-readable artefacts:** `results/d0_window_audit/d0_window_audit.json`,
`results/d0_window_audit/d0_window_audit.tsv`

---

## 1. What D0 was supposed to decide

Stage D0 of [`RESEARCH-PLAN.md`](RESEARCH-PLAN.md) is the cheapest kill in the
programme: before any sample is spent, decide whether the candidate channels
have a therapeutic window in lung at all.

The plan sets D0's exit criterion as *a written window verdict for every
candidate target* — **selective**, **conditionally selective** (the plan's own
example: "only in the inflamed niche"), or **not viable** — and defines the
kill condition K4 as: *no target is conditionally selective → the pharmacological
arm is dropped and the programme becomes purely a biomarker programme*.

D0's method, as specified, is: pull GTEx lung and immune expression for the
channel gene and its known regulators; score the specificity verdict; pull
ClinVar and AlphaGenome regulatory-variant scores for the same loci.

This audit executes that method and reports what it does and does not decide.

---

## 2. The rule as implemented

The rule lives in `scripts/d0_window_audit.py`, not in a dependency that could
change underneath it:

| Input | Rule |
|---|---|
| Detection | lung median TPM ≥ 1 (the GTEx/HPA "detected" floor) |
| `selective` | lung TPM ≥ 10 × the highest non-lung tissue |
| `conditionally_selective` | lung TPM ≥ 3 × the highest non-lung tissue |
| `no_bulk_window` | lung is expressed, but neither margin is met |
| `not_a_lung_target` | lung median TPM < 1 |

"Window fold" is lung median TPM divided by the highest median TPM among the
other 53 GTEx tissues. The immune fold and epithelial fold use the maximum
within the immune group (lymphocytes, spleen, whole blood) and the epithelial
group (skin, mucosa, colon, salivary gland, and the genitourinary and
gynaecological epithelia) respectively; the full tissue grouping is written out
in the script so a reader can argue with it.

**Disclosure.** The aggregate lung and tissue values were already visible when
the margins were fixed, because the data pull and the rule design were
interleaved. The margins are therefore reported with a sweep rather than as a
single number, and the sweep is in the artefact:

| Margin | Classification counts (7 targets) |
|---|---|
| 2× | 5 × `no_bulk_window`, 2 × `not_a_lung_target` |
| 3× | 5 × `no_bulk_window`, 2 × `not_a_lung_target` |
| 5× | 5 × `no_bulk_window`, 2 × `not_a_lung_target` |
| 10× | 5 × `no_bulk_window`, 2 × `not_a_lung_target` |
| 20× | 5 × `no_bulk_window`, 2 × `not_a_lung_target` |

**No target changes class anywhere between 2× and 20×.** The conclusion is not
an artefact of the threshold.

---

## 3. Data, and how to re-derive it

| Source | Used for | Endpoint |
|---|---|---|
| GTEx Portal v2 (`gtex_v8`) | median expression per tissue, 54 tissues | `/expression/medianGeneExpression` |
| Open Targets GraphQL | tractability, gnomAD constraint, safety liabilities, drug candidates | `target(ensemblId:)` |
| NCBI ClinVar | aggregate germline classification and asserted traits | `esearch` + `esummary`, `db=clinvar` |
| AlphaGenome Atlas | regulatory-variant scores | **not executed** — the official `alphagenome` package is not installed here, and the window verdict does not depend on it |

The audit is self-contained: no sibling repository is imported, the tissue
grouping and the decision rule are both in the script, and every number in this
report is in the JSON artefact. Re-running takes about three minutes, most of
it ClinVar rate-limiting. Exactly as the gap-audit script is not part of CI,
this script is not part of CI either; the *consistency* of this report with
its artefact is checked in CI instead.

ClinVar was truncated for two genes — PIEZO1 (2,000 of 3,123 records fetched)
and CACNA1E (2,000 of 2,659) — because the fetch is capped. The artefact
records `n_records_on_file` and a `truncated` flag, so the pathogenicity
counts for those two genes are lower bounds.

---

## 4. The verdicts

| Target | Tier | Lung TPM | Highest non-lung tissue | Window fold | Immune fold | Epithelial fold | Germline P/LP | Verdict |
|---|---|---|---|---|---|---|---|---|
| `KCNN4` | 1 | 9.511 | Minor_Salivary_Gland (115.7) | 0.0822 | 0.1766 | 0.0822 | 10 | **no_bulk_window** |
| `PIEZO1` | 1 | 101.5 | Colon_Sigmoid (119.2) | 0.8513 | 1.472 | 0.8513 | 115 | **no_bulk_window** |
| `CACNA1E` | 1 | 0.1259 | Brain_Nucleus_accumbens_basal_ganglia (20.32) | 0.006199 | 0.03045 | 0.5402 | 29 | **not_a_lung_target** |
| `KCNA3` | 2 | 4.238 | Cells_EBV-transformed_lymphocytes (7.973) | 0.5315 | 0.5315 | 1.957 | 34 | **no_bulk_window** |
| `STOML3` | regulator | 0.6649 | Fallopian_Tube (1.268) | 0.5245 | — | 0.5245 | 49 | **not_a_lung_target** |
| `TMEM150C` | regulator | 7.65 | Adrenal_Gland (48.67) | 0.1572 | 0.8239 | 0.3695 | 39 | **no_bulk_window** |
| `PIEZO2` | offtarget | 7.949 | Brain_Spinal_cord_cervical_c-1 (7.62) | 1.043 | 2.631 | 1.598 | 255 | **no_bulk_window** |

`STOML3` has no immune-group value: none of the three immune tissues expresses
it above the detection floor.

---

## 5. Per-target findings

### 5.1 KCNN4 — the highest-priority target has no systemic window

Lung median expression is 9.5 TPM. The highest non-lung tissue is minor
salivary gland at 115.7 TPM — **12× the lung** — and the highest immune tissue
is EBV-transformed lymphocytes at 53.8 TPM. The window fold is 0.082: for
every unit of expression in lung there are twelve in salivary gland.

This is not only an expression fact:

- **Genetic constraint.** gnomAD LoF observed/expected is 31/45.2 with
  LOEUF 0.515 — the gene is loss-of-function intolerant, so systemic
  knockdown is expected to have toxicity.
- **On-target safety liabilities.** Open Targets records, from Lynch et al.
  (2017), the following liabilities for KCNN4: ataxia, convulsions, decreased
  locomotor activity, increased atrial refractory period, neurotoxicity. These
  are pharmacological on-target effects, not idiosyncratic ones.
- **Pharmacology exists.** Open Targets lists senicapoc at Phase 3 and
  chlorzoxazone as approved.
- **Germline.** 10 pathogenic/likely-pathogenic records. The traits asserted
  are dominated by *dehydrated hereditary stomatocytosis 2* (3) and the
  pseudohyperkalaemia/perinatal-oedema variant (1). Whether a blocker helps or
  harms those patients depends on the direction of the effect, which this
  audit did not establish.

**Verdict: `no_bulk_window`.** The therapeutic index for a systemic KCa3.1
blocker in an adjuvant lung setting is not supported by bulk tissue. A minority
state-bearing fraction cannot out-express 115 TPM of salivary gland, so the
route to viability is not "more selectivity" — it is **delivery**: a
tumour-directed or local modality, or the senicapoc-BODIPY probe as a
companion imaging readout rather than the drug itself.

### 5.2 PIEZO1 — well expressed in lung, and not separable from PIEZO2

Lung is 101.5 TPM, one of the highest values of any target here, and the
tissue is genuinely lung-relevant (colon sigmoid 119.2, spleen 69.0). Two
things qualify it:

- **PIEZO2 is the problem.** PIEZO2's window fold is 1.043 — lung is *less*
  expressed than the highest non-lung tissue, which for PIEZO2 is spinal cord
  (7.62 TPM against lung's 7.95). There is no bulk-tissue separation between
  a Piezo1 drug and its homologue. PIEZO2's germline record is large:
  255 pathogenic/likely-pathogenic variants, dominated by *arthrogryposis,
  distal, with impaired proprioception and touch* (60) and PIEZO2-related
  disorders (23).
- **Germline is a liability, not an opportunity, for a blocker.** PIEZO1's
  pathogenic records assert *lymphatic malformation 6* (35) and PIEZO1-related
  disorder (21); 115 pathogenic/likely-pathogenic records in the fetched set.
  PIEZO1's gnomAD LoF observed/expected is 296/297.2 — tolerant of LoF, which
  is the better of the constraint profiles here.

**Verdict: `no_bulk_window`** for a systemic agent, with an additional and
separate constraint: a Piezo1 drug must be isoform-selective, not merely
tissue-selective. Open Targets lists no clinical-stage drug candidate and no
tractability flag for PIEZO1 at all, which is consistent with the plan's own
observation that only 13 PubMed records combine a Piezo1 inhibitor with cancer.

### 5.3 CACNA1E — ruled out as a lung target

Lung median expression is 0.126 TPM, two orders of magnitude below the
detection floor. The highest tissue is brain (20.3 TPM), gnomAD LoF
observed/expected is 40/259.2 with LOEUF 0.120 — severely constrained — and
ClinVar asserts *developmental and epileptic encephalopathy, 69* (10 records).
Open Targets lists 10 drug candidates, all calcium-channel blockers approved
for other indications (bepridil, pregabalin, gabapentin, terodiline).

**Verdict: `not_a_lung_target`.** This is the one unambiguous kill in the
audit: the channel is not expressed in lung, and the off-target tissue is the
one where the germline disease lives.

### 5.4 KCNA3 — the immune arm, measured against the wrong axis

Lung 4.24 TPM; the highest tissue is EBV-transformed lymphocytes at 7.97 TPM,
so the immune fold (0.53) and the window fold are the same number. gnomAD LoF
LOEUF is 0.363 — constrained. ClinVar asserts *KCNA3-associated developmental
and epileptic encephalopathy* (13 records). Open Targets lists six candidates,
all Kv1.3 blockers used for neurological indications (amifampridine,
dalfampridine, tedisamil, guanidine).

**Verdict: `no_bulk_window`** as a lung-directed agent, which is the correct
reading: KCNA3's role in the plan is the *immune* arm, where blocking
effector-memory T-cell Kv1.3 is the intent rather than the hazard. That makes
it a **state-modulating** target, not a tumour-selective one, and it moves to
the immunotherapy arm of the plan rather than the drug-window table.

### 5.5 STOML3 — lung biology, no drug surface

Lung expression is 0.665 TPM, below the detection floor, though it is the
tissue where STOML3 is most enriched relative to the others (11× the mean of
all tissues). ClinVar asserts *primary ciliary dyskinesia* (48 pathogenic
records) — ciliary lung biology, not a channel to modulate. Open Targets lists
no target class, no tractability and no drug candidate.

**Verdict: `not_a_lung_target`** as a drug target; it survives only as a
mechanistic annotation of the ciliary–niche axis.

### 5.6 TMEM150C — no window, no pharmacology

Lung 7.65 TPM against adrenal gland at 48.7 (fold 0.157); gnomAD LoF LOEUF
0.206; no tractability, no drug candidate; and its 39 pathogenic ClinVar
records are dominated by *chromosome 4q21 deletion syndrome* (2) and
unspecified large-deletion records rather than a monogenic disease.

**Verdict: `no_bulk_window`.** As a Piezo1 regulator it does not widen the
window.

### 5.7 PIEZO2 — the off-target that decides the Piezo1 arm

Included as the dominant on-target off-target of any Piezo1 drug: window fold
1.043, neural fold 1.043 (spinal cord), and a large germline burden centred
on *arthrogryposis, distal, with impaired proprioception and touch*.

---

## 6. The gate: K4 does not fire as written

**The literal reading.** No target reaches `conditionally_selective` on bulk
normal tissue, so a literal application of K4 would drop the pharmacological
arm and reduce the programme to a biomarker programme.

**Why that reading is wrong.** K4 presumes the verdict *can* be established.
It cannot, from this data, for the reason the plan itself supplies:
"conditionally selective (e.g. only in the inflamed niche)" is a statement
about a **state**, and bulk GTEx tissue is by construction a state-free
sample. The plan's own D0 method therefore cannot decide its own kill
condition for the cases that matter. A screen that cannot distinguish
"conditionally selective" from "no window" has not failed the target; it has
failed to be a decision.

**What the screen does decide.** Two things, and both are real:

1. **Two targets are out.** CACNA1E and STOML3 are not lung targets at all,
   and this is not a margin-sensitive judgement.
2. **The systemic-window hypothesis is dead for KCNN4.** A window fold of
   0.082 against salivary gland, with loss-of-function intolerance and
   recorded neurological and cardiac liabilities, does not become viable
   because the state is enriched 3× or 10×. The KCa3.1 arm now requires
   **delivery** (tumour-directed or local), not selectivity.

**What the screen cannot decide.** Whether the relapse-competent state
expresses these channels more than the surrounding lung. That is a
cell-type-resolved question, and it is now the first experiment the programme
should run — see §8.

**Amended gate.** K4 is re-labelled **D0b** and deferred: it is decidable only
with state-resolved expression, and the bulk screen stands as a negative prior
plus two kills.

---

## 7. What this changes in the plan

| Plan element | Before D0 | After D0 |
|---|---|---|
| KCa3.1 / KCNN4 | "Highest priority", window risk high | **Conditional.** No systemic window (fold 0.082). Requires tumour-directed or local delivery, or a companion-probe role. |
| Piezo1 | "Second priority, most original" | **Still the most original, now with a quantified constraint**: no separation from PIEZO2 (fold 1.043), no clinical-stage asset. Isoform selectivity is a prerequisite. |
| Cav2.3 / CACNA1E | "Third, conceptually central" | **Ruled out** as a lung target: 0.126 TPM, LOEUF 0.120, DEE69. |
| Kv1.3 / KCNA3 | Tier 2 immune arm | Reclassified as a **state-modulating immune** target, not a tumour-selective drug target. |
| STOML3, TMEM150C | Piezo1 regulators | No drug surface; mechanistic annotation only. |
| D2 design | burden-normalised methylation enrichment ratio in sorted fractions | **Add an electrical endpoint**: channel expression per cell type within the same tumour — state-bearing vs non-state vs immune — and the state-to-immune ratio, as the gate that decides whether the drug arm survives. |
| K4 | kill the pharmacological arm if no target is conditionally selective | **D0b**, deferred to state-resolved data. Two targets already killed outright. |

---

## 8. Limitations

- **Bulk normal tissue is not tumour tissue.** Every number in §4 is from
  GTEx. Tumour tissue and the state-bearing fraction are not represented.
  This is the limitation the whole audit turns on.
- **Median TPM hides the cell-type mixture.** A lung median of 9.5 TPM for
  KCNN4 is an average over alveolar, bronchial, endothelial, immune and
  stromal cells; the state-bearing cells could sit anywhere within it.
- **The margin is a convention**, and although the verdict is insensitive to
  it between 2× and 20×, it is not a fitted quantity.
- **ClinVar truncation** for PIEZO1 and CACNA1E makes their pathogenicity
  counts lower bounds.
- **AlphaGenome was not executed**, so no regulatory-variant score at the
  candidate loci is reported. This affects panel design, not the window
  verdict.
- **Germline direction was not resolved.** The audit reports what ClinVar
  asserts, not whether blocking a gene helps or harms the people who carry
  the pathogenic variants. For KCNN4 (a red-cell disease) and PIEZO1 (a
  red-cell and lymphatic disease) this is the difference between an
  opportunity and a contraindication, and it is resolvable from the
  literature — it simply was not resolved here.
- **No clinical claim.** This is a target-triage audit on public expression
  and variant data.

---

## 9. The next input is already public

While assembling this audit, the anchor dataset of the programme was located
in public data: **GSE299684**, "Single-cell RNAseq analysis of relapsed SCLC
patient specimens", is the GEO deposit of PMID 42019833 (Stewart et al.,
*YAP1 Defines an Emergent, Plastic Population of Relapsed SCLC*, J Thorac Oncol
2026) — the very paper the research plan treats as its anchor. It holds 15
relapsed-SCLC single-cell libraries from liver, lymph node, head and neck,
adrenal, lung, brain and retroperitoneum, deposited as standard 10x
`barcodes/features/matrix` triplets (~700 MB), public since 2026-05-15.

That matters because it is the dataset that can decide what §6 says cannot be
decided: in relapsed SCLC single cells, the state-bearing population can be
identified and its ion-channel expression compared with the surrounding
malignant cells and with the tumour-infiltrating immune cells. It converts D0b
from "wait for the D2 tissue study" into "run it on public data first".

It also sharpens the gap audit rather than contradicting it: the *literature*
intersection is still a single narrative review, and the reason a
state-resolved electrical measurement has not been reported is still that
nobody has run it on this dataset.

**Update (2026-11-07).** The gate deferred here was then executed on exactly
this dataset: see [`GSE299684-STATE-EXPRESSION.md`](GSE299684-STATE-EXPRESSION.md).
The state *is* electrically marked — PIEZO1 in 39% of state cells against 6%
of neighbouring tumour cells, at every site tested — but KCa3.1 does not mark
the state in lung, which closes the KCa3.1 arm for the lung indication that
this audit had already called conditional.

---

**Bottom line.** D0 killed two targets outright (CACNA1E, STOML3), removed the
systemic-window hypothesis for KCa3.1, and quantified the Piezo1 isoform
problem. It did not fire the plan's own kill condition, because bulk tissue
cannot decide a state-dependent question — and the data that can decide it
turned out to be public.
