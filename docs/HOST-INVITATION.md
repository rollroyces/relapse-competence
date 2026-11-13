# Invitation to a host Principal Investigator

**Status: draft, not sent.** Nothing has been sent to anyone. The letter
below is waiting for the PI's review and for the decision on whether to
approach anyone at all.

**Why this document exists.** CDAS's own instructions for accessing data
(read 2026-11-11) require the Principal Investigator — the Data Access
Requestor — to be "a permanent employee of your institution at a level
equivalent to... an academic professor... or senior researcher", to
register, and to be responsible for "the project, its submission, renewals
and close-out". The requester holds no current institutional appointment,
so the role cannot be filled by the person doing the research. The route's
real dependency is therefore an institutional PI who agrees to carry the
proposal, and this is the letter that asks.

**Who it could go to.** CDAS publishes every approved PLCO project with its
Principal Investigator and institution, and the twenty most recently approved
are listed with their institutions in
[`HOST-SHORTLIST.md`](HOST-SHORTLIST.md). Five of those twenty are companies,
which CDAS permits as the counterparty of the transfer agreement, so this
letter is not restricted to academic departments.

**It is not part of the submission package.** The package under
`plco-cdas-submission-package/` is what CDAS receives; this is outbound
correspondence, so it is not printed into the package PDF and the package
checker does not treat it as a submission document. Its own gate is in
`scripts/verify_report_consistency.py`.

---

## 1. Before you send — seven things to set

1. **`[HOST]`** — the name and the salutation. **Decided: Dr Bryant**, Alex K
   Bryant, MD, MAS, Assistant Professor of Radiation Oncology at the
   University of Michigan and staff physician at the VA Ann Arbor
   Healthcare System (PLCO-2077). "Dr" rather than "Professor" because the
   title is Assistant Professor, and because CDAS's rule is about the rank
   and the letter should not appear to assert one. The reasoning, the
   fallback order and the contact address are in
   [`HOST-SHORTLIST.md`](HOST-SHORTLIST.md).

2. **How you know of them, or why you chose them.** One line. This is the
   line that makes the ask reasonable rather than cold: a shared lab, a
   paper, a seminar, a co-author, a field they work in. If there is no
   personal link, say so plainly — "I have been working on this from
   outside the field and wanted to approach someone whose work is close to
   it" is an acceptable sentence, and inventing a connection would not be.
   **Decided, and it is in the letter:** the requester studied at the
   University of Michigan, and the recipient is the PLCO investigator there.
   That is a true line and it does the work; no other connection is claimed.

3. **Your standing — check all three and amend what is not true.** You have
   no employer; no funding is attached to this work; you have no competing
   interest in the result. The package's own declarations say the work is
   not sponsored by any commercial party whose products it assesses, and
   that the data will not be used to identify or contact any participant.

4. **The letter now asks for more than it did, and CDAS's answer is why.**
   The eligibility question was answered on the morning of 2026-11-12: "you
   will need to find a professor to submit this data request and you must be
   part of the institution to be able to have access to CDAS data." That is
   two conditions. The first is the one this letter already assumed. The
   second is new, and it is the request the letter now has to make: carrying
   the proposal is not enough, because the requester has to be part of the
   submitting institution to reach the data at all. A professor who is only
   being asked to sign something would be asked the same question again by
   CDAS, so the letter offers the arrangement that makes the standing
   possible and says plainly that it is asking for one.

5. **Whether the laboratory question travels with this letter.** It does not
   have to be a second letter. The programme also wants to know whether a
   perturbation of the channel is worth running in a model that carries the
   state, and the only laboratory that can answer it is one with such a
   model — which is a laboratory inside the host's institution more often than
   not. [`LABORATORY-INVITATION.md`](LABORATORY-INVITATION.md) holds the
   question, its propositions and the decision table; it is held rather than
   sent, because a perturbation question with no route to the material is a
   question nobody can act on, and because one letter to one person is a
   smaller ask than two.

6. **Whether to raise the funded route in the same letter.** NCI's
   PAR-25-248 opportunity exists to use the PLCO biorepository for
   early-detection biomarker research, and its first step is a
   specimen-verification request answered in three weeks without any award.
   The letter below mentions it, because a professor asked to carry an
   unfunded favour and a professor asked to lead a funded proposal are not
   being asked the same thing. It promises nothing: the grant route needs an
   organisation and a full application, and the letter says so.

6. **If the letter is going to a laboratory rather than to a data-access
   office, it must carry the question, not the programme.** That is a
   different letter: [`LABORATORY-INVITATION.md`](LABORATORY-INVITATION.md)
   asks whether a perturbation is worth running, and carries the
   propositions, the measurement they rest on, and the decision table. A
   request that carries no prediction is a request for attention rather than
   for work.

## 2. The letter

Plain text, ready to paste into an e-mail. The subject line is given
separately because it is the subject line.

**Subject:** Would you be willing to be the Principal Investigator on a PLCO
plasma project?

<!-- BEGIN HOST LETTER -->
Dear Dr Bryant,

I am writing to ask whether you would be willing to be the Principal Investigator on a data-access proposal to the National Cancer Institute's Cancer Data Access System for the PLCO trial, the Prostate, Lung, Colorectal and Ovarian Cancer Screening Trial. I studied at Michigan, which is why I am writing to you rather than to a stranger. If you are not the right person, I would be grateful for a pointer to whoever is.

Why I am asking you rather than applying myself: CDAS's instructions require the Principal Investigator, the Data Access Requestor, to be a permanent employee of the submitting institution at professor level or senior-researcher level, to register on CDAS, and to be responsible for the proposal's submission, its renewals and its close-out. I hold no current institutional appointment, so I cannot take that role. I asked CDAS whether any route existed for a researcher in that position, and the answer this week was no: a professor has to submit the request, and the requester has to be part of the submitting institution to have access to the data at all. So what I am asking is that you carry the role, and that we settle between us what standing at your institution would let me reach the data myself rather than through someone else's hands.

The project. The relapse-competent state is a drug-tolerant subpopulation of tumour cells. Its definition is transcriptional rather than electrical, but we have measured, in three public deposits, that it is electrically marked and specifically so: it over-expresses the potassium channel KCa3.1 at a 2.97-fold detection ratio in EGFR-mutant lung adenocarcinoma, that marking is carried within an individual patient's tumour in 20 of 23 libraries and in 7 of 7 residual-disease libraries, and it does not hold in relapsed SCLC. We have also measured that the channel co-allocates with the state's transcriptional programme beyond what cell complexity explains, so the question is the direction of causation, not whether the two travel together. How the same measurement would be made in plasma is written down in the assay specification I will attach. Whether the state can be read in blood at all is the open question, and it has to be settled in a real cohort rather than in a simulation. PLCO can settle it: archived plasma drawn at screening visits, with the clinical data to align them, in a cohort of about 155,000 participants.

What I would ask you to do. Register on CDAS with RAS, and give CDAS your institution and its location. Review and submit the proposal: the fields are already written, the project description, the aims, the data requested and the reason each element is necessary, and the analysis is pre-specified, with the panel, the operating point, the thresholds and the per-patient applicability rule fixed before any data are opened, and the code behind every published figure public. Be the point of contact for CDAS staff's questions, for the renewal at twelve months, and for the close-out. And settle with me what standing at your institution would put me on the approved-users list with an institutional address, because CDAS will not grant data access to someone outside it. And let your institution's Signing Official execute the Data Transfer and Use Agreement through DocuSign, which is the institution's step and starts from your giving CDAS the contact details.

What I would do. The science, the analysis, the pre-specified plan and the code, and I would write it up whether or not it is favourable. One point I want to be straight about: CDAS have confirmed that the requester has to be part of the submitting institution, so this is not a contingency to be discovered after submission. If the standing we agree cannot be enough for me to be on the approved-users list, the analysis would have to be run by someone at your institution on the pre-specified plan and code. I would want to agree that with you before anything is submitted, not after.

What the proposal asks for. The clinical data that go with PLCO's archived plasma: date and site of diagnosis in a Limited Data Set, treatment, mortality with follow-up time, smoking history, and the visit dates of the blood draws, for participants diagnosed with lung cancer and for matched participants who were not. The archived plasma and the matched tumour material come through NCI's separate biospecimen programme rather than through this proposal. CDAS have told me what is on that side: the lung tissue is from primary lung tumours, 434 participants have tumour cores, 348 of them also in PLCO's genotyping study, and none of the tissue has been profiled, so the request has to include the whole-exome work. The germline genotypes come through dbGaP. Nothing in the proposal is confidential: CDAS publishes it once access is granted.

The timeline. Data-only projects have been delivered one to four weeks after approval. The biospecimen route runs through NCI's Etiologic and Early Marker Studies programme, and for the round now open the preliminary application is due 18 February 2027 and the full application 1 April 2027, so the answers to the scope questions have to be in before then. There is a funded version too: NCI's PAR-25-248 opportunity exists to use the PLCO biorepository for early-detection biomarker work, and its first step is a specimen-verification request answered in three weeks without any award. If you would rather lead a funded proposal than carry an unfavour one, I would rather raise it now than later. The assay cost on the delivered aliquots is not yet known and does not fall to your institution; I will confirm how it is covered before anything is ordered.

What I would ask of you. A yes or no would settle it. If the answer is not me, a short reply saying so is a complete answer and I will not follow up. If it is possibly, a twenty-minute conversation would be faster than a long exchange by e-mail.

With thanks for reading this far.

Royce Lam
roycelam@umich.edu
<!-- END HOST LETTER -->

## 3. What this letter deliberately does not do

- It does not promise funding, a position, authorship, or a place on a
  grant. Authorship should be offered if and when there is a paper, and the
  letter should not pre-commit to a credit it cannot guarantee.
- It does not describe the requester as a member of the recipient's
  institution. A PI who cannot say who the researcher is, and in what
  standing, is a PI who will be asked the same question by CDAS.
- It does not ask for the analysis to be run a particular way. The
  pre-specification is stated as a fact about the work, not as a favour.
- It does not hide the approved-user problem. The paragraph on what would
  happen if the data cannot be downloaded by the requester is the one most
  likely to end the correspondence, and leaving it out would be the worst
  possible way to spend a professor's attention.
