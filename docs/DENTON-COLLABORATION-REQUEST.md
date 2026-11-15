# Collaboration request to Professor Brian Denton — a composite plasma assay and ten tubes

**Status: draft, not sent.** Nothing has been sent to Professor Denton, to
the University of Michigan, or to anyone else. This is a draft for review.

**What this document is.** The University of Michigan has two approved PLCO
investigators, and this letter goes to the one whose subject is the programme's
question: Brian T. Denton, PhD, Professor of Industrial and Operations
Engineering, on PLCO-2057, "Adaptive Diagnostic Testing Algorithms for Design
of Cost-sensitive Composite Biomarker Tests". The letter asks for three things
— the Principal Investigator role on the CDAS proposal, a sponsorship under
SPG 601.42, and ten plasma tubes — and attaches the one-page partner summary
that separates what is measured from what is projected and simulated.

**Where the request sits.** This is not part of the PLCO submission package.
The package under `plco-cdas-submission-package/` is what CDAS receives; this
is outbound correspondence to a person at the institution that would submit it,
so it is not printed into the package PDF and the package checker does not
treat it as a submission document. Its gate is in
`scripts/verify_report_consistency.py`.

**What it rests on.** The evidence, split three ways, is in
[`PARTNER-SUMMARY.md`](PARTNER-SUMMARY.md); the programme's own numbers are in
[`GATE-REVIEW.md`](GATE-REVIEW.md),
[`LOCALISATION-AUDIT.md`](LOCALISATION-AUDIT.md),
[`PER-PATIENT-AUDIT.md`](PER-PATIENT-AUDIT.md) and
[`GSE353299-STATE-EXPRESSION.md`](GSE353299-STATE-EXPRESSION.md); the assay
is in [`PLASMA-ASSAY-SPECIFICATION.md`](PLASMA-ASSAY-SPECIFICATION.md); the
institutional mechanism is in
[`UM-AFFILIATION-MECHANISM.md`](UM-AFFILIATION-MECHANISM.md); the data-access
position is in [`DATA-ACCESS-APPLICATIONS.md`](DATA-ACCESS-APPLICATIONS.md)
§2.1.

---

## 1. Before you send — seven things to set

1. **Who it goes to.** Brian T. Denton, PhD, Stephen M. Pollock Collegiate
   Professor of Industrial and Operations Engineering, University of Michigan;
   also Professor of Electrical Engineering and Computer Science, Professor of
   Urology by courtesy at Michigan Medicine, and a member of the Institute for
   Healthcare Policy and Innovation and of the Cancer Center. E-mail
   `btdenton@umich.edu`, published on his CDAS project page and on his own
   department page. Office: 1847 IOE Building. Department phone: (734)
   763-2060. **Decided: the CDAS project address**, which is the address CDAS
   itself holds against an approved project.

2. **Why him and not Bryant.** Both are approved PLCO investigators at
   Michigan, and the letter to Bryant is drafted and not sent
   ([`HOST-INVITATION.md`](HOST-INVITATION.md)). Denton is the better
   subject match: his PLCO project is about combining biomarkers into
   composite tests and balancing diagnostic benefit against the cost of
   testing, which is the programme's question. Bryant's project is prostate
   screening microsimulation, which is not. **The reasoning, the fallback
   order and the contact address for both are in
   [`HOST-SHORTLIST.md`](HOST-SHORTLIST.md).** If you would rather start with
   Bryant, say so and this letter is not the one to send.

3. **The sponsorship mechanism, stated in the letter.** SPG 601.42 Covered
   Visitors covers people who "do not hold a U-M appointment", excludes U-M
   employees so that it is not employment, and lists "a U-M alum" among the
   eligible categories; a sponsoring unit or a faculty sponsor puts it in
   place. It applies to the Ann Arbor campus. The letter asks the question;
   it does not assert that CDAS accepts it.

4. **The two things that are not settled, and must stay in the letter.**
   Whether CDAS accepts a sponsored affiliation as "part of the
   institution" — asked, answer outstanding — and the germline half of the
   attribution, which runs through dbGaP, whose application requires the
   institution to verify that the investigators are full-time employees, which
   a covered-visitor sponsorship by definition is not. **If you would rather
   not raise the second with him in a first letter, cut the paragraph — but
   then do not expect him not to meet it.**

5. **What is attached.** [`PARTNER-SUMMARY.md`](PARTNER-SUMMARY.md), one page.
   It carries the disclosure, so the letter points to it rather than
   repeating it in full; the letter adds the Singlera fact in one sentence
   because a first letter should not require an attachment to be read for a
   conflict.

6. **The specimen route, if he says yes.** PLCO's own policies note that an
   EEMS application is required for all pilot studies, including the limited
   pilots it offers to assess specimen and assay suitability. So ten tubes is
   not a favour to be slipped into an existing request: it is a preliminary
   EEMS application with a lead PI whose institution holds the Material
   Transfer Agreement. The fields are written in
   [`plco-cdas-submission-package/`](plco-cdas-submission-package/README.md).
   For the round now open the preliminary application is due 2027-02-18 and
   the full application 2027-04-01.

7. **The cost to his department.** Sponsorship is not free for the
   sponsoring unit: it is the onboarding, the agreements, the restricted-party
   screening and possibly a background screening under SPG 201.95. The letter
   says the request is not free of his time and does not disguise it.

---

## 2. The letter

Plain text, ready to paste into an e-mail. The subject line is given
separately because it is the subject line.

**Subject:** A composite plasma assay, ten tubes, and the question your PLCO
project is about

<!-- BEGIN DENTON LETTER -->
Dear Professor Denton,

I am writing about your PLCO project, "Adaptive Diagnostic Testing Algorithms for Design of Cost-sensitive Composite Biomarker Tests" (PLCO-2057), because it asks a question I have a concrete instance of: how to combine several measurements into one test, in what order to make them, and how to spend a fixed read budget so that the benefit is not paid for with false positives, false negatives, specimen volume and money. I have an instance of that question with the answer space already fixed, and I need ten tubes of plasma to start it.

The measurement. A composite test on plasma, in three parts: a mutation panel that gives the participant's own tumour cfDNA fraction and the MRD flag, which is the denominator; a leukocyte reference set, which is the background; and fifty of the two hundred loci on the electrical channel, which is the signal. Two ion channels, KCa3.1 and Piezo1. The part that is not standard is that attribution is per molecule: a channel-transcript read counts only if it carries the tumour's own shift of a germline position, so a leukocyte-derived molecule cannot be counted, and the compartment is removed by construction rather than by subtraction. The panel is two hundred loci at two hundred thousand times, with a quarter of the read budget on the channel, and there are six stop rules with thresholds fixed in advance.

What is settled and what is not is in the attached one page, and I would rather you read it before anything else. In short: the marking of the state by the channel is measured in tumour tissue from public deposits, two point nine seven times in EGFR-mutant lung adenocarcinoma against a state defined independently of the channel, carried within an individual patient's tumour in twenty of twenty-three libraries and in every one of seven residual-disease libraries, and absent in relapsed small-cell lung cancer. Nothing has been measured in blood. The published plasma statistic does not survive a realistic leukocyte background and inverts, and my own audit says so. The attributed statistic above was then simulated, and it clears my own bar and collapses to chance when the state is matched away, so it is measuring the state rather than the tumour burden. Three of my five kill conditions have fired. That is the position, and it is why the next step is ten tubes and not a cohort.

Why I am asking you rather than a laboratory. Two reasons, and the second is the larger one. The first is that the question I need answered is yours: the programme's problem before it is a wet-laboratory problem is a measurement-design problem, and the naive version of the answer, subtracting a background, has already been tried and fails. The second is institutional. CDAS requires the Principal Investigator of a data-access proposal to be a permanent employee of the submitting institution at professor level, and the requester has to be part of that institution to reach the data at all. I hold no current appointment, I am employed by nobody, and no funding is attached to this work, so I cannot take either role.

What I am asking you for, in three parts. First, to be the Principal Investigator on the CDAS proposal: the form fields, the project description, the aims, the data requested and the reason each element is necessary are already written, and the analysis is pre-specified, so this is not a draft you have to write. Second, to sponsor a standing for me at your institution. The University has a mechanism for exactly this and I have the policy to hand: Standard Practice Guide 601.42, Covered Visitors, which covers people who engage with the University's non-public resources and who do not hold a U-M appointment, excludes University employees so that it is not employment, and names a former student of the institution among the categories that qualify. A sponsoring unit or a faculty sponsor puts it in place. Third, to carry or co-sponsor the specimen request for the ten tubes. And one thing I would ask for explicitly, because it is the record that matters to me: that the application name me, with the role that is actually mine. CDAS publishes the collaborators named on an approved project, with their institutions, so a name on the application is a public and permanent record of who did what, and it is made at the moment when authorship cannot honestly be discussed.

The ten tubes. Five incident lung-cancer cases and five matched cancer-free controls, chosen to span the storage conditions the repository actually holds plasma under. PLCO banks plasma at T0, T3, T4 and T5 and not at T1 or T2, so a plasma allocation has to span T0 and T3 at minus seventy against T4 and T5 at minus one hundred and fifty-seven; serum is available for every screening year, which is why I am asking for plasma and not serum. Ten tubes answer three questions: whether cell-free RNA is recoverable and sequenceable from these archives at all, whether what is recoverable decays with the age of the specimen and the temperature it was held at, and whether the two channel transcripts are detectable in cell-free RNA at all and at what abundance against a leukocyte reference set. Ten tubes do not need germline material or matched tumour, because they only ask whether the material is there; that is why ten is a sensible first request rather than a smaller one dressed up. Ten is not enough to estimate a recovery rate and I am not asking for one.

Two things I have not settled, said plainly rather than left for you to find. Whether CDAS treats a sponsored affiliation as "part of the institution" for the approved-users list, I have asked them and the answer is outstanding; if it is not, the standing question has to be solved some other way and I would rather tell you that now than have it appear after you have agreed to carry something. And the germline half of the attribution runs through dbGaP, whose application requires the institution to verify that the investigators are full-time employees, and a covered-visitor sponsorship is by definition not employment. If the pilot proceeds, that half needs someone employed at your institution, and I would rather agree that with you than discover it later.

A disclosure, since it is owed. The programme's reference early-detection assay is PanSeer, whose DNA methylation work was funded by Singlera Genomics; thirteen of its authors are Singlera employees, two are board members, three are inventors on a Singlera patent, and one is a co-founder, equity holder and paid consultant. Its analysis code is public. The full statement, and my own position, are in the attached page. My measurement is a channel transcript in cell-free RNA rather than methylation in cell-free DNA, and the two are orthogonal.

What I am not asking for. Not a commitment, not funding, not exclusivity, not intellectual property, not authorship, and not your department's time for nothing: a sponsorship is real work for the sponsoring unit, and I would rather say so than let you discover it. What I am asking is twenty minutes to talk about whether this is worth doing, and whether you would carry the PI role if it is.

The full protocol, the analysis plan and the stop rules are written down in advance and will be sent before anything is requested or ordered.

With thanks for reading this far.

Royce Lam
roycelam@umich.edu
<!-- END DENTON LETTER -->

---

## 3. What this letter deliberately does not do

- It does not present the programme's plasma numbers as measurements. Every
  plasma figure in the letter is a projection or a simulation, and the letter
  says so in the same paragraph, including that the published statistic
  inverts and that three kill conditions have fired.
- It does not claim the sponsorship route is settled. The letter says CDAS's
  answer is outstanding, and it says the germline half has a requirement the
  sponsorship cannot meet.
- It does not claim ten tubes will show the readout works. It says they ask
  whether the material is there, and it says so before the ask rather than
  after.
- It does not ask for a partnership, an exclusive arrangement, intellectual
  property, authorship, funding or a commitment. It does ask to be named on
  the application, which is a different request: an application names the
  investigators and is published, while a paper's author list is settled by the
  paper's own conventions, and asking for a place on a paper that does not
  exist yet is what makes a PI say no. It asks for a conversation
  and, conditionally, for the PI role.
- It does not disguise what the sponsorship costs his department: onboarding,
  agreements, screening and possibly a background check.
- It does not describe the requester as a member of the University of
  Michigan. The letter says the opposite, in the plainest terms available,
  because a PI who cannot say who the researcher is will be asked the same
  question again by CDAS.
- It does not quote the performance figures of the programme's own assay,
  because they do not exist yet, and it does not quote the numbers of the
  reference assay as if they were the programme's.
