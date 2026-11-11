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

**It is not part of the submission package.** The package under
`plco-cdas-submission-package/` is what CDAS receives; this is outbound
correspondence, so it is not printed into the package PDF and the package
checker does not treat it as a submission document. Its own gate is in
`scripts/verify_report_consistency.py`.

---

## 1. Before you send — four things to set

1. **`[HOST]`** — the professor's name and the salutation. Replace it.

2. **How you know of them, or why you chose them.** One line. This is the
   line that makes the ask reasonable rather than cold: a shared lab, a
   paper, a seminar, a co-author, a field they work in. If there is no
   personal link, say so plainly — "I have been working on this from
   outside the field and wanted to approach someone whose work is close to
   it" is an acceptable sentence, and inventing a connection would not be.

3. **Your standing — check all three and amend what is not true.** You have
   no employer; no funding is attached to this work; you have no competing
   interest in the result. The package's own declarations say the work is
   not sponsored by any commercial party whose products it assesses, and
   that the data will not be used to identify or contact any participant.

4. **Do not send it before CDAS answers the eligibility question.** The
   letter asks a professor to take on a role whose exact limits are still
   being confirmed. Two of the open questions bear directly on what this
   letter offers: whether the PI may register and submit while someone else
   fills in the fields, and whether an approved user may hold an address at
   an institution where they no longer hold an appointment. If either
   answer is no, the letter has to change before it goes.

5. **If the letter is going to a laboratory rather than to a data-access
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
Dear Professor [HOST],

I am writing to ask whether you would be willing to be the Principal Investigator on a data-access proposal to the National Cancer Institute's Cancer Data Access System for the PLCO trial, the Prostate, Lung, Colorectal and Ovarian Cancer Screening Trial. If you are not the right person, I would be grateful for a pointer to whoever is.

Why I am asking you rather than applying myself: CDAS's instructions require the Principal Investigator, the Data Access Requestor, to be a permanent employee of the submitting institution at professor level or senior-researcher level, to register on CDAS, and to be responsible for the proposal's submission, its renewals and its close-out. I hold no current institutional appointment, so I cannot take that role. What I am asking is that you carry it and let me do the research under it.

The project. The relapse-competent state is a drug-tolerant subpopulation of tumour cells. Its definition is transcriptional rather than electrical, but we have measured, in three public single-cell deposits, that it is electrically marked and disease-specifically so: it over-expresses the potassium channel KCa3.1 at a 2.97-fold detection ratio in EGFR-mutant lung adenocarcinoma, that marking is carried within an individual patient's tumour in 20 of 23 libraries and in 7 of 7 residual-disease libraries, and it does not hold in relapsed small-cell lung cancer, where most tumours carry too little of the state to read. We have also measured, in the same data, that the channel's expression co-allocates with the state's transcriptional programme beyond what cell complexity explains, so we know the question is the direction of causation and not whether the two travel together. Whether the same plasma measurement can carry that, and how to assay it, is written down in [`../PLASMA-ASSAY-SPECIFICATION.md`](../PLASMA-ASSAY-SPECIFICATION.md). Whether the state can be read in blood at all is the open question, and it has to be settled in a real cohort rather than in a simulation. PLCO can settle it: archived plasma drawn at screening visits, with the clinical data to align them, in a cohort of about 155,000 participants.

What I would ask you to do. Register on CDAS with RAS, and give CDAS your institution and its location. Review and submit the proposal: the fields are already written, the project description, the aims, the data requested and the reason each element is necessary, and the analysis is pre-specified, with the panel, the operating point, the thresholds and the per-patient applicability rule fixed before any data are opened, and the code behind every published figure public. Be the point of contact for CDAS staff's questions, for the renewal at twelve months, and for the close-out. And let your institution's Signing Official execute the Data Transfer and Use Agreement through DocuSign, which is the institution's step and starts from your giving CDAS the contact details.

What I would do. The science, the analysis, the pre-specified plan and the code, and I would write it up whether or not it is favourable. One point I want to be straight about: if the data cannot be downloaded by me, because approved users have to hold institutional addresses at your institution and I have none there, then the analysis would have to be run by someone at your institution on the pre-specified plan and code, or I would have to work from your institution as a visiting researcher. I would want to agree that with you before anything is submitted, not after.

What the proposal asks for. The clinical data that go with PLCO's archived plasma: date and site of diagnosis in a Limited Data Set, treatment, mortality with follow-up time, smoking history, and the visit dates of the blood draws, for participants diagnosed with lung cancer and for matched participants who were not. The archived plasma and the matched tumour material come through NCI's separate biospecimen programme rather than through this proposal. Nothing in the proposal is confidential: CDAS publishes it once access is granted.

The timeline. Data-only projects have been delivered one to four weeks after approval. The biospecimen route runs through NCI's Etiologic and Early Marker Studies programme, whose next application period closes on 18 February, so the answers to the scope questions have to be in before then. The assay cost on the delivered aliquots is not yet known and does not fall to your institution; I will confirm how it is covered before anything is ordered.

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
