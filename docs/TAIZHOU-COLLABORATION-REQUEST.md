# Collaboration request: the Taizhou Longitudinal Study

**Status: draft, not sent.** Nothing has been sent to anyone at the Taizhou
Institute, the Human Phenome Institute, or to any of the paper's authors.

**What this document is.** The Taizhou Longitudinal Study is the only
published cohort in which a blood test was shown to detect cancer in
asymptomatic participants one to four years before diagnosis. The programme
wants to ask a different question of the same samples, and it needs two
things the published consent record does not establish: permission to analyse
RNA from the archived plasma, and germline material for the lung-cancer
stratum. The letter asks for those two answers first, because they decide
whether the material would be usable.

**Where the request sits.** This is not part of the PLCO submission package.
The package under `plco-cdas-submission-package/` is what CDAS receives; this
is outbound correspondence to a different institution, so it is not printed
into the package PDF and the package checker does not treat it as a
submission document. Its gate is in `scripts/verify_report_consistency.py`.

**What it rests on.** The route finding, the funding and competing interests,
the two consent constraints, the condition of the archived material and the
released code are all in
[`DATA-ACCESS-APPLICATIONS.md`](DATA-ACCESS-APPLICATIONS.md) §2.3, with
sources and verification dates in §2.4.

---

## 1. Before you send — six things to set

1. **Who it goes to.** The correspondence has five names: Weimin Ye
   (weimin.ye@ki.se) and Li Jin (lijin@fudan.edu.cn) at the Taizhou
   Institute of Health Sciences and the Human Phenome Institute; Yuan Gao
   (gary.gao@singleragenomics.com) and Rui Liu (rliu@singleragenomics.com)
   at Singlera Genomics; and Kun Zhang (kzhang@bioeng.ucsd.edu) at UC San
   Diego. The letter is addressed to the first two, and that is a
   deliberate choice: the cohort and its archive belong to the Institute,
   and the disclosure burden sits with the Singlera-affiliated authors
   rather than with the Institute. **Copying the Singlera authors is
   decided: do not copy them.** The cohort and its archive belong to the
   Institute, the ask is a question and a small pilot rather than a material
   transfer, and the disclosure paragraph of the letter already gives the
   Institute everything it needs to judge the conflict: the assay funder, the
   cohort's separate funders, the competing interests, the patent and the
   released code. The letter then asks the Institute whether the archive's
   sponsor has to be consulted, and offers to include them if it does. That
   puts the decision where it belongs -- with the body that holds the
   archive -- instead of pre-empting it, and it keeps a patent holder who is
   not a party to the archive from becoming a party to the request.

2. **Whether the two consent questions come before the sample request, and in
   what order.** In this draft they do, and the RNA-scope question comes
   first. Neither position is rhetorical. The measurement reads channel
   transcripts in cell-free RNA; PanSeer read methylation in cell-free DNA;
   and the published record cannot say whether the consent covers molecular
   analysis of RNA, because PanSeer never needed to ask. It also gates the
   germline question: if the consent does not permit molecular analysis of
   RNA, the aliquots cannot be used for this programme at all, so there is
   nothing for germline material to attach to. The germline question comes
   second because it is the one that decides whether the *attribution* works,
   and the published consent excluded full genetic sequencing — so the
   per-molecule attribution the readout depends on has no source in this
   cohort. A request that leads with plasma aliquots and mentions consent in
   the fourth paragraph would be asking for material that cannot be used as
   specified. If the programme can live without attribution — which is a
   different and weaker programme — the second question changes and so does
   the ask.

3. **Whether to name the PanSeer code.** The draft does, in the disclosure
   paragraph. The code is public at
   `github.com/ncomms-20-10056-t/ncomms-20-10056-t`, the request is
   orthogonal to it, and acknowledging it is the difference between a
   reader who believes the distinction and a reader who suspects it.

4. **What to attach.** The two documents below. They are the substance: a
   reader who wants to check the arithmetic can. The programme's public
   repository is linked in the letter, so the rest is one click away.

5. **Do not send it before the CDAS scoping answers arrive.** Not because
   the two routes depend on each other — they do not — but because the
   answer to "is there germline consent" is likely to be the same kind of
   answer, and a request that asks two institutions the same question at
   once looks like the programme is guessing. The germline half has been
   answered from the published consent: full genetic sequencing was not
   included in it. The RNA-scope half has not been answered at all, and only
   the collaborators can answer it.

6. **Whether to propose a pilot rather than the stratum, and how many
   aliquots.** The draft proposes a pilot rather than the stratum. PanSeer's
   own limitations section records that the archive was collected before
   modern plasma preservation, that only 1 mL of plasma was available per
   sample, and that there was a high sample failure rate; cfRNA is scarcer
   and less stable in plasma than cfDNA, and the aliquots are twelve to
   nineteen years old. Asking for the lung-cancer stratum before anyone has
   measured whether usable RNA is recoverable would be asking for the wrong
   thing first.
   **The size is decided: ten aliquots, spanning the archive's age range.**
   Ten is enough to answer the question the pilot exists to answer -- is
   cell-free RNA recoverable at all, and does what is recoverable decay with
   the age of the sample -- and it is small enough that the Institute can
   decide it is a reasonable thing to do. It is not enough to estimate a
   recovery rate, and the letter says so rather than implying otherwise. The
   number is a proposal for them to adjust, not a demand.

---

## 2. The letter

Plain text, ready to paste into an e-mail. The subject line is given
separately because it is the subject line.

**Subject:** Two questions about the Taizhou samples, and about their consent

<!-- BEGIN TAIZHOU LETTER -->
Dear Dr Ye and Professor Jin,

I am writing about the Taizhou Longitudinal Study, and about two questions the published consent makes difficult to answer before any samples are involved. If the answers turn out to be no, this message has cost you a few minutes and I will not follow up. The underlying question is a smaller one than it first looks: whether a cell-free RNA measurement is possible with this archive at all. I would rather ask that than build a proposal on material that cannot carry it.

Who I am and what this is. I am an independent researcher working on a problem that sits between tumour cell biology and blood measurement, outside the field of cancer screening. The programme is small and self-funded: I hold no institutional appointment, and no commercial party is involved in it.

The background. A drug-tolerant subpopulation of tumour cells — the relapse-competent state — is defined transcriptionally; the paper that defines it does not mention an ion channel. Across three public single-cell deposits, however, that state carries an unmistakable electrical signature: it over-expresses the potassium channel KCa3.1 (KCNN4) 3.7-fold in EGFR-mutant lung adenocarcinoma, the marking is carried inside an individual patient's tumour in 20 of 23 libraries and in all 7 residual-disease libraries, and it does not hold in relapsed small-cell lung cancer, where most tumours carry too little of the state to read. We would like to know whether the same state can be read in plasma rather than in tissue, because a screening cohort is the only setting where enough people are followed long enough for a lead time to mean anything.

Why Taizhou. Your study is the only published cohort in which a blood test detected cancer in asymptomatic participants one to four years before conventional diagnosis, in a population followed with a registry linkage, with 123,115 participants' samples stored for long-term use. The measurement we want to make is orthogonal to PanSeer: PanSeer reads circulating tumour DNA methylation, and we would read channel transcripts in cell-free RNA. The two are complementary rather than competing, and Taizhou has the sample collection and the outcome follow-up that this kind of question needs and that no other cohort offers in the same form.

The first question, and everything else waits on it. Your paper records that the study was approved by the Human Ethics Committee of Fudan University and that written informed consent was obtained from all study participants prior to inclusion in the TZL, so I am not asking you to re-open that. I am asking about the scope of that consent: does it permit molecular analysis of RNA from the archived plasma? The measurement I want to make reads RNA rather than DNA — channel transcripts in cell-free RNA — and your paper reads methylation in cell-free DNA. That difference is not cosmetic: it decides whether the archived aliquots can carry this programme at all. I cannot answer the question from the paper, because PanSeer never worked with RNA, so I would rather ask than infer it from an assay that worked.

The second question decides whether the programme is worth anything at all. PanSeer attributes a channel-transcript molecule to the tumour only when that molecule carries a signature the participant's own tumour has shifted — in practice, a heterozygous germline position that the tumour has lost heterozygosity at, or that carries a somatic variant on the other allele. It is the only way I know to attribute a plasma molecule to a tumour rather than to the white cells around it, and without it the measurement is dominated by leukocyte material rather than by the tumour. The data availability statement for your paper records that full genetic sequencing data was not included in the informed consent, and that only the methylation status at each genomic position was released. If that is right, the germline information this measurement needs was never collected for the participants already in the study, and I would rather establish that now than build a request around material that turns out to be unusable. So the question is narrow and answerable: does germline material exist, or could it be consented for going forward, for participants in the lung-cancer stratum? If it exists for the archived participants, I would also want to know whether matched primary tumour tissue is available for them, since that is what establishes which germline positions a given tumour has shifted. If it does not exist, please say so and I will treat Taizhou as unable to support this measurement and look elsewhere.

One thing I should say about the material now rather than discover later. Your paper records that these samples were collected before modern plasma preservation techniques, that the blood was held at 4 °C until the end of the business day before it was centrifuged, and that only 1 mL of plasma was available per sample, and it says plainly that better collection would have given the assay more and higher quality DNA molecules. I am asking about RNA, which is scarcer and less stable in plasma than DNA, and these aliquots are now twelve to nineteen years old. I do not know what is recoverable from them, and neither does the published record. I would therefore want to start with a pilot on ten aliquots spanning the age range of the archive, rather than with the lung-cancer stratum: enough to establish that cell-free RNA can be recovered and sequenced from this archive at all, and whether what is recoverable decays with the age of the sample. Ten aliquots is not enough to estimate a recovery rate, and I am not asking for one; it is enough to tell whether the measurement is possible here.

What I would ask for, if the answer is yes. Serial plasma aliquots for the lung-cancer stratum in the pre-diagnosis window, with the clinical data needed to align each draw to the outcome; matched primary tumour tissue where it is archived; and the methylation measurements, if you are willing, so that the two readouts can be compared in the same participants. The ask would start with the ten-aliquot pilot rather than with the stratum, and the protocol would follow it. All the assays would be run on the aliquots, and the analysis would be pre-specified — panel, operating point, thresholds and per-patient applicability rule fixed before any data are opened — with the code behind every figure public.

A disclosure, because it is owed. The PanSeer DNA methylation assays were funded by Singlera Genomics; the Taizhou study itself was funded by Chinese national and municipal programmes. The paper's competing-interests statement records thirteen authors as Singlera employees, Yuan Gao and Rui Liu as board members, and Jeffrey Gole, Athurva Gore and Rui Liu as inventors on patent US62/657,544, which covers the library preparation method the study uses; Kun Zhang is a co-founder, equity holder and paid consultant, with those arrangements managed by UC San Diego. The PanSeer analysis code is public at github.com/ncomms-20-10056-t/ncomms-20-10056-t. I am raising all of this because our measurement is a different one — channel transcripts in cell-free RNA, not methylation in cell-free DNA — and because a reader should be able to judge that claim against the published record rather than take it from me.

What I am asking for. Not a commitment, and not a data-transfer agreement at this stage. A short exchange about whether either of those two questions has an answer, and what a collaboration would look like if they do. If the archive's sponsor has to be consulted before even a pilot, tell me and I will include them; the disclosure above is complete enough for that conversation to start without me. If either answer is that Taizhou cannot support this measurement, that is a complete answer and I will not follow up. If it can, I will send the full protocol before anything is requested or ordered.

With thanks for reading this far.

Royce Lam
roycelam@umich.edu
<!-- END TAIZHOU LETTER -->

---

## 3. What to attach

| Document | What it gives the reader |
|---|---|
| [`PLASMA-ASSAY-SPECIFICATION.md`](PLASMA-ASSAY-SPECIFICATION.md) | What is measured, in which analyte, how the signal is attributed to the tumour, the statistic, the panel, the controls and the six numeric stop rules. It is where the germline requirement comes from, so it is the document that has to be checked |
| [`LOCALISATION-AUDIT.md`](LOCALISATION-AUDIT.md) | The measurement of whether the attribution works: the statistic clears the programme's own threshold for the lung readout where the bulk one inverts, and a matched-state control showing it measures the state rather than the burden |

Attach the first at minimum. The second is what makes the first's central
claim checkable rather than asserted.

The programme's public repository carries the rest: the per-tumour audit that
names the readout, the driver-versus-passenger audit that shows the channel
travels with the programme, and the gate review that records what has and has
not been established.

---

## 4. What this letter deliberately does not do

- **It does not ask for the samples first.** Two consent questions come
  before the aliquot request, because the answers decide whether the
  aliquots would be usable. A request that led with the material would
  have asked for something that may not support the measurement.
- **It does not assume the consent does not exist.** The letter records that
  written informed consent was obtained, because it was, and asks about the
  two specific things the published record does not establish: whether the
  consent covers molecular analysis of RNA, and whether germline material
  exists for the lung-cancer stratum.
- **It does not ask for the stratum before the material has been
  characterised.** The ask starts with a pilot, because the paper's own
  limitations section records that the archive was collected before modern
  plasma preservation, that only 1 mL of plasma was available per sample,
  and that there was a high sample failure rate — and because cfRNA is
  scarcer and less stable in plasma than cfDNA.
- **It does not overstate what the measurements show.** The audit is a
  simulation, and the letter says what the simulation found and what the
  pilot still has to establish.
- **It does not hide the funding.** The disclosure names the assay funder,
  the competing interests, the patent and the published code, and says
  which measurement is ours.
- **It does not imply an institutional backing that does not exist.** The
  letter states the requester's position plainly, so that a collaborator
  deciding whether to spend time on this is deciding with the same
  information the programme has.
- **It does not ask for a commitment.** It asks a narrow question that can
  be answered in a paragraph, and it says what happens if the answer is no.
