# Partnership enquiry to Wholomics GmbH — a ten-tube feasibility question

**Status: draft, not sent.** Nothing has been sent to Wholomics, to Patrick
Strasser, or to anyone else. This is a draft for review.

**What this document is.** Wholomics GmbH holds an approved PLCO project
(2026-0185) whose Principal Investigator is its own chief executive, and that
project is the requester's own experiment run with a different analyte: an
analytical-suitability pilot on archived pre-diagnostic specimens, with
matched controls, split by storage temperature, whose stated purpose is to
establish whether the archive can yield the material at all before any
irreplaceable specimens are requested for a full validation study. The
question in this letter is the same question asked of cell-free RNA. The
routes by which the requester could satisfy CDAS's "part of the institution"
requirement are worked out in [`HOSTING-ROUTES.md`](HOSTING-ROUTES.md).

**Where the request sits.** This is not part of the PLCO submission package.
The package under `plco-cdas-submission-package/` is what CDAS receives; this
is outbound correspondence to a company in a different country, so it is not
printed into the package PDF and the package checker does not treat it as a
submission document. Its gate is in `scripts/verify_report_consistency.py`.

**What it rests on.** The route finding and the four alternatives are in
[`HOSTING-ROUTES.md`](HOSTING-ROUTES.md) §4; the programme's own measurements
are in [`GATE-REVIEW.md`](GATE-REVIEW.md),
[`LOCALISATION-AUDIT.md`](LOCALISATION-AUDIT.md) and
[`PER-PATIENT-AUDIT.md`](PER-PATIENT-AUDIT.md); the assay that would be run is
in [`PLASMA-ASSAY-SPECIFICATION.md`](PLASMA-ASSAY-SPECIFICATION.md); the
disclosure about the programme's reference assay is in
[`DATA-ACCESS-APPLICATIONS.md`](DATA-ACCESS-APPLICATIONS.md) §2.4.

---

## 1. Before you send — seven things to set

1. **Who it goes to.** Patrick Strasser, MSc, Co-Founder and CEO, Wholomics
   GmbH, Boston and Ried im Innkreis. The company's own pages give
   `info@wholomics.com` and +1 617 222 0055, and a "Become a Partner" form
   on <https://www.wholomics.com/our-partners>. **Decided: an e-mail to the
   company address, not the form.** The form asks for a partnership in one
   field; this letter asks two questions and discloses a conflict, and both
   would be lost in a form. If the answer is to send it to Strasser
   personally, his address is not on the company's site.

2. **The ask: ten tubes, and why not a stratum.** The letter proposes a
   ten-tube feasibility pilot — five incident cases and five matched
   cancer-free controls, spanning the storage strata PLCO actually holds for
   plasma — and explicitly does not ask for the stratum. Ten is enough to
   answer "is cell-free RNA recoverable and sequenceable from this archive,
   and does what is recoverable decay with age and storage temperature", and
   it is not enough for a recovery rate. The letter says so, because
   Wholomics's own project is 100 specimens and the letter must not read as
   asking them to halve their pilot.

3. **The plasma-versus-serum difference, which is the one technical
   objection the recipient will have.** PLCO's plasma is banked at T0, T3,
   T4 and T5 and not at T1 or T2; serum is available for every screening
   year. Wholomics's design splits T0–T2 against T4/T5, which a plasma
   pilot cannot reproduce as a single block. The letter says this plainly
   rather than leaving them to find it.

4. **Your standing — check all three and amend what is not true.** You have
   no employer, no funding attached to this work and no competing interest in
   the result. The letter states all three, because the letter also asks
   whether the collaboration could be a paid one, and a letter that asks for
   money while implying an institutional standing would be dishonest.

5. **The disclosure, which is owed.** The programme's reference assay is
   PanSeer, whose DNA methylation work was funded by Singlera Genomics;
   thirteen of its authors are Singlera employees, two are board members,
   three are inventors on a Singlera patent, and one is a co-founder, equity
   holder and paid consultant. The analysis code is public. The letter says
   this because the measurement is a different one — channel transcripts in
   cell-free RNA, not methylation in cell-free DNA — and because a reader
   should be able to judge that against the published record.

6. **The commercial question.** The letter asks plainly whether this could be
   a paid collaboration and whether the company could act as the institution
   for a data-access proposal. It does not hide that this is one of the
   reasons for writing, and it says it will not be an unfunded interest. If
   that is wrong for the programme to say — for instance if the point of the
   enquiry is purely scientific — this paragraph is the one to cut.

7. **What to attach.** The assay specification and the public repository.
   The letter promises to send the full protocol before anything is requested
   or ordered; attaching both now is better than promising them.

---

## 2. The letter

Plain text, ready to paste into an e-mail. The subject line is given
separately because it is the subject line.

**Subject:** A ten-tube feasibility question about PLCO plasma, and why I am
writing to you

<!-- BEGIN WHOLOMICS LETTER -->
Dear Mr Strasser,

I am writing because your PLCO project, "Analytical Suituality and Storage-Stability Pilot for a Serum NMR-Based Multi-Omics Multi-Cancer Early Detection Assay Using Pre-Diagnostic PLCO Specimens" (2026-0185), asks the same question of an archive that I want to measure something else in, and because whether the answer is yes decides whether the work I am proposing is worth doing at all.

The measurement I want to make is a bulk cell-free transcript measurement of two ion channels, KCa3.1 (KCNN4) and Piezo1, as a marker of a drug-tolerant tumour-cell state. It is orthogonal to a methylation signature and, as far as I can tell, complementary to a serum NMR multi-omics signature rather than competitive with it: I am not proposing an early-detection classifier and I am not proposing to replace your assay. What I am proposing is a second question about the same specimens.

The question is whether cell-free RNA can be recovered and sequenced from these archives at all. That is a feasibility question and not an efficacy one, and it is the question your project is asking for the NMR assay: before any irreplaceable specimens are requested for a full validation study, the suitability of long-term archived pre-diagnostic PLCO serum for that assay has to be established. The same argument applies to a transcript assay, and it applies with more force, because RNA is scarcer and less stable in plasma than DNA is. Your stated motivation names three limits of current approaches, early-stage sensitivity, specimen volume requirements and cost, and the first of the three is moot if the analyte cannot be recovered from the archive at all.

What I am asking for is a ten-tube pilot and not a stratum. Ten tubes is enough to establish whether cell-free RNA is recoverable and sequenceable from these specimens, and whether what is recoverable decays with the age of the specimen and with the storage temperature it was held at. It is not enough to estimate a recovery rate, and I am not asking for one. It is enough to tell whether the measurement is possible here, which is the only question I can usefully ask before anything larger.

Ten also keeps the ask in the shape PLCO's own policies describe. Your pilot is a hundred specimens, fifty incident solid-tumour cases and fifty matched cancer-free controls, split equally between specimens stored at minus seventy (T0 to T2) and minus one hundred and fifty-seven (T4 and T5). The reason for a balanced allocation per storage stratum is that the storage condition is the variable that decides whether an archive is usable at all, and that is the reason I would want the strata separated at ten tubes rather than pooled.

One difference in the material, which is why the pilot is not a request for serum. PLCO's plasma is banked at T0, T3, T4 and T5 and not at T1 or T2, whereas serum is available for every screening year. A plasma pilot therefore cannot use the T0 to T2 stratum as a single block: it would have to span T0 and T3 at minus seventy against T4 and T5 at minus one hundred and fifty-seven. If the archive is workable for a transcript assay then that is a workable design, and I would want the allocation to reflect the strata PLCO actually holds rather than the strata that are convenient.

Two things I would be grateful for. First, whether you would be willing to consider including ten plasma tubes for a transcript feasibility pilot in your PLCO request, and to have the aliquoting done so that RNA is preserved at that point rather than after two decades of storage, with the storage-stratum metadata and the handling protocol shared with me afterwards. Second, whether you would point me to the sequencing route you use, if you use one.

What I am bringing is a public programme. The analysis behind every number I have published is in a public repository under an open licence; the panel, the operating point and the thresholds are fixed before any data are opened; and the assay specification, which states what would be counted, what would stop it and what the pilot would measure, is written down in advance. I would send you the full protocol before anything is requested or ordered.

There is one thing I should say plainly rather than let you discover later. I hold no current institutional appointment, I am employed by nobody, and no funding is attached to this work. That is why I am writing to a company and not to a department: NIH's Cancer Data Access System requires the person requesting a PLCO data-access proposal to be part of the institution that submits it, and I cannot satisfy that on my own. If a collaboration with your company were the way that standing arose, I would want it to be a real collaboration with real terms rather than an arrangement, and I would rather say so at the start than have it emerge later. I would also want to be clear that I am not asking you to sponsor an unfunded interest. If this is worth doing, it should be worth doing commercially or not at all, and I would rather hear that from you than work it out.

A disclosure, because it is owed. The programme's reference early-detection assay is PanSeer, and the DNA methylation assays in that work were funded by Singlera Genomics; thirteen of its authors are Singlera employees, two are board members, three are inventors on a Singlera patent covering the library preparation, and one is a co-founder, equity holder and paid consultant. The analysis code from that paper is public. I mention it because my measurement is a different one, channel transcripts in cell-free RNA rather than methylation in cell-free DNA, and because a reader should be able to judge that claim against the published record rather than take it from me. My own position is the one above: no employer, no funding, no competing interest in any result.

Where the programme stands, so that you can judge the scale of what I am asking for. The programme has measured, in public single-cell deposits, that the drug-tolerant state is electrically marked: the potassium channel is elevated in EGFR-mutant lung adenocarcinoma at a 2.97-fold detection ratio, the marking is carried within an individual patient's tumour in twenty of twenty-three libraries and in every one of seven residual-disease libraries measured, and it does not hold in relapsed small-cell lung cancer. What the programme has not measured is the electrical signal in blood. Every plasma number published so far is a projection built on tissue measurements, and the audit that applied the programme's own kill conditions found that the published statistic does not survive a realistic leukocyte background in bulk plasma: it inverts, from 0.9929 to 0.0053. A different statistic, one that attributes each channel-transcript molecule to the tumour rather than subtracting a background, was then simulated and clears the programme's own bar at 0.9091 against a threshold of 0.65, and collapses to chance, 0.5170, when the state is matched away, so that it is measuring the state and not the tumour burden. That is a simulation and not a measurement, and I do not want to be read as claiming otherwise. Ten tubes would not settle it. They would settle whether the archive can yield the material at all, and nothing in this programme can be settled without that.

I am not asking you to carry the work, to commit the company, or to tell your funder anything. A no to any part of this is a complete answer and I will not follow up. If it is a yes, or a maybe, I would welcome twenty minutes.

With thanks for reading this far.

Royce Lam
roycelam@umich.edu
<!-- END WHOLOMICS LETTER -->

---

## 3. What this letter deliberately does not do

- It does not ask for the stratum, the lung-cancer cases, or any number of
  specimens above ten. The letter says in terms that ten cannot estimate a
  recovery rate, so that the ask cannot later be read as a larger one.
- It does not claim that the programme's readout works in plasma. Every
  plasma number the letter quotes is a projection or a simulation, and the
  letter says so in the same paragraph, including the fact that the
  published bulk statistic inverts. A reader who took only the good numbers
  would be misled, and the letter is written so that they cannot.
- It does not present the attributed statistic as the programme's own. The
  letter says that the published projection fails and that a different
  statistic was then simulated, and it says the simulation is a simulation.
- It does not hide the commercial motive. The programme needs an institution
  to exist for CDAS's purposes, the letter says so, and it says it will not
  be an unfunded interest.
- It does not promise an exclusive arrangement, an IP position, a first
  refusal, or authorship. Those are the programme's to give or withhold
  after there is something to give, and offering them in a first letter
  would trade the only thing this letter has, which is that its ask is
  small and its interest is real.
- It does not describe the requester as a member of Wholomics, or as having
  any standing at all. The letter says the opposite, in the plainest terms
  available, because a PI or a chief executive who cannot say who the
  researcher is will be asked the same question again by CDAS.
- It does not cite the Singlera disclosure as though it were a material
  obstacle. It is a disclosure, and it is made so that the recipient can
  judge the claim against the published record.
