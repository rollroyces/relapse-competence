# Documents checklist

Everything CDAS needs for a data-only project, who supplies it, and what has
to happen to it. Items marked **required** cannot be skipped: CDAS's
instructions make the PI, the Signing Official, the approved users and the
project details explicit requirements.

The state of the application as a whole is tracked in
[`../DATA-ACCESS-APPLICATIONS.md`](../DATA-ACCESS-APPLICATIONS.md).

## 1. Before the proposal can be submitted

| # | Document or action | Who | Required | Status |
|---|---|---|---|---|
| 1 | CDAS registration and private profile | PI | required | not started |
| 2 | Agreement to the CDAS Data Use Policies | PI | required | not started |
| 3 | Project details, from `01-project-details.md` | PI or delegate | required | prepared |
| 4 | Proposal narrative, from `02-proposal-narrative.md` | PI or delegate | required | prepared |
| 5 | PI cover sheet, from `03-pi-cover-sheet.md`, signed | PI | required | prepared, unsigned |
| 6 | Institutional letter, from `04-signing-official-letter.md`, signed | Signing Official | required | prepared, unsigned |
| 7 | Principal Investigator's CV | PI | required | not started |
| 8 | Ethics determination for secondary use of human plasma | PI | required | not started |
| 9 | Approved users' names and institutional e-mail addresses | PI | required | template prepared |
| 10 | Confirmation of the number of usable lung-cancer samples with serial plasma and a matched tumour | PI, via the coordinating centre | scoping, not a document | not started |

## 2. After approval

| # | Document or action | Who | Required | Status |
|---|---|---|---|---|
| 11 | Data Transfer and Use Agreement, executed through DocuSign | Signing Official | required | pending approval |
| 12 | Selection of the Limited Data Set fields, specifically date and site of diagnosis | PI with CDAS staff | required for this project | specified in the proposal |
| 13 | Confirmation of the assay cost and timeline on the delivered aliquots | PI and the laboratory | for planning | not started |
| 14 | Renewal request or close-out at 12 months | PI and Signing Official | required | pending |

## 3. Notes on the items that are easy to get wrong

- **The PI must be a permanent employee at professor level.** CDAS's
  instructions state that a post-doc, trainee or lab technician cannot be the
  Principal Investigator, and that the PI is the person who submits the
  proposal and is responsible for renewals and close-out.
- **The project description is capped at 500 words.** The text in
  `01-project-details.md` is 405 words, and
  `scripts/check_plco_cdas_package.py` fails if it goes over.
- **The proposal will be published** on the CDAS website once access is
  granted. The narrative is written for that, and it carries the
  conflict-of-interest declaration the review will need.
- **Diagnosis dates are not in the standard de-identified dataset.** CDAS can
  release them in a Limited Data Set where they are essential to a specific
  research project; the interval between the blood draw and diagnosis is what
  this project turns on, so the request is explicit rather than implied.
- **Collaborators at other institutions need their own project proposal**
  with the same project details. They cannot simply be added to the approved
  users list.
- **Access is granted for 12 months.** Renewals and close-out both go through
  the Signing Official.
