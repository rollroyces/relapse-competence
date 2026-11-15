# Where a contribution is recorded, and how to get one

**Status: a plan, not an agreement.** Nothing has been filed, submitted or
agreed with anyone. This document sets out where a contribution to this
programme can be recorded, what a record is worth, and what the programme
proposes to ask for in each letter.

**Why this document exists.** The requester's position is unusual: he has no
institutional appointment, so he cannot be a Principal Investigator, and the
data route requires the requester to be "part of the institution" to reach
the data at all. The obvious worry is that the contribution will be
unrecorded — that he will design the panel, run the analysis, and write it
up under someone else's name. **That worry is answerable, because the
programme's contributions are not recorded in a paper first. They are recorded
in an application, and the application is public.**

---

## 1. The three records, and what each one is worth

| # | Record | What it is | Public? | When it is made |
|---|---|---|---|---|
| 1 | **The collaborators line on the approved-project page** | CDAS publishes every approved project with its named investigators. Where the application names collaborators, the project page lists them with their institutions. | **Yes, permanently** | When the application is filed |
| 2 | **The proposal abstract and contact information** | The applicant agrees that "the abstract of your research proposal and your contact information (provided in your application)" will be publicly displayed on the CDAS website | **Yes** | When access is granted |
| 3 | **The investigative team and its NIH biosketches** | The full application requires: "You must list all members of your investigative team and upload an NIH biosketch for each member" | Not published, but a personal record | When the application is filed |
| 4 | The paper's author and contribution statement | The usual record, settled by the paper's own conventions | With the paper | When the result exists |

**Record 1 is the one that answers the question, and it is verified.** Read
from the live CDAS site on 2026-11-15:

- **PLCO-2057** (Denton's project) publishes three collaborators: Brian Denton,
  Viswanath Nagarajan and Blake Harris, all at The University of Michigan.
- **PLCO-380** (Robbins' project) publishes two: Stephen Duffy of Queen Mary
  University of London and John Field of the University of Liverpool.
- **NLST-621** publishes one: Gary Gao of Singlera Genomics Inc.
- **2026-0185** (Wholomics' pilot) publishes none, and **NLST-43** publishes
  none — because those applications named no collaborators.

So the collaborators line is not automatic: **it is written by whoever files
the application.** A person who is named on an approved PLCO project has a
permanent, public, citable record saying they worked on it, at an
institution, on a project anyone can look up.

**A note on how this was read, because it is the same trap twice.** CDAS
encodes names and e-mail addresses as HTML numeric entities. A first pass
that strips numeric entities before extracting the text drops the collaborators
and reports them as absent — which is how the record came to say that a
project page carried no e-mail address when it did. The same class of error
once hid a quotation across a line break. **Both were found by a mutation
test that asked whether the check would fail if the text were changed, rather
than by reading the output and believing it.** Any claim about what a CDAS
page does or does not contain is now checked against the decoded page.

## 2. The rule the programme proposes: settle it at filing, not after the result

**The evidence behind every claim about what the programme has done is in
[`PARTNER-SUMMARY.md`](PARTNER-SUMMARY.md)**, which separates it into
measured, projected and simulated and lists the kill conditions with their
status. This document does not restate it.

**Contribution is settled when the application is filed, because that is the
moment the names are recorded and published.** After a result exists, "who
did what" is a negotiation between people who each have something to lose;
before it, it is a plan, and it can be written down.

This cuts both ways and the programme says so: asking for a named place on an
application is a small, specific and legitimate request that a PI can
reasonably grant. Asking for authorship of a paper that does not exist yet,
from a stranger, is a large and vague request that a PI can reasonably
decline. **The letters therefore ask for the first and do not ask for the
second.**

## 3. The draft contribution statement

A CRediT-style statement, in the roles the programme's own record supports.
It is proposed to the other party with the application, and carried into any
paper if one results. The right-hand column is theirs to fill; the left-hand
column is what the requester actually does.

| Role | The requester | The partner |
|---|---|---|
| Conceptualization | The state as an electrical question; the per-molecule attribution as the mechanism that could make it readable in plasma | |
| Methodology | The 200-locus panel at the stated operating point; the attribution mechanism; the six stop rules | |
| Software | The evidence chain, its simulators, the audits and the package; all public under AGPL-3.0-or-later | |
| Formal analysis | The gate review, the leukocyte audit, the per-patient audit, the localisation audit, the treatment-naive SCLC audit | |
| Investigation | The data work on the public deposits; the per-library recomputation; the pilot, if it is run | |
| Data curation | The tumour-tissue measurements the programme rests on | |
| Writing – original draft | The documents and the letters | |
| Writing – review & editing | | |
| Funding acquisition | | |
| Supervision | | |
| Resources | | |
| Data curation, PLCO | | |
| Project administration | | |
| Software, formal analysis, verification | | |

**The one thing this statement must not do is claim a role the requester
does not hold.** He holds no funding, supervises nobody, and has no
institutional resources. Those rows are left blank deliberately, and saying
so in the letter is better than leaving a reader to wonder.

## 4. What each route asks, and what it would record

| Route | The ask | The record it would make |
|---|---|---|
| **Denton (PLCO data, and the 10-tube EEMS request)** | to be the Principal Investigator, to sponsor a standing, and to carry the specimen request; **and to name the requester on the application** with the role that is actually his | the collaborators line on a public PLCO project page, and a published abstract naming the team |
| **Wholomics (the company's own PLCO pilot)** | ten tubes through the same request, and **to be named on the application** as the person who designed the transcript assay | the collaborators line — their project publishes none today, so this would be the first |
| **Bryant (the fallback host)** | the PI role, a sponsorship, and **a name on the application** | the collaborators line on a UM PLCO project |
| **Taizhou (a collaboration, not a CDAS application)** | the two consent answers and ten aliquots, and **the contribution roles settled in writing at the start of the collaboration** | co-authorship of the resulting paper, agreed before the data exist, plus the public code and the public documents |

## 5. What this does not promise, and the two things that could still go wrong

- **A collaborators line is not authorship.** It is a record of who worked on
  a project; it is not a place on a paper, and it is not a citation. It is,
  however, permanent, public and checkable, and on this programme it is
  available at a moment when authorship cannot honestly be discussed.
- **Nothing is guaranteed until an application is filed and approved.** A
  named place on an application that is never approved is a name on a
  rejected form.
- **The EEMS route requires an NIH biosketch, and the biosketch route is
  open to a researcher with no appointment — through NIH's own route for
  unaffiliated individuals.** eRA Commons is explicit that a scientist cannot
  create their own account: "Only officials from your own organization can
  create a new eRA Commons account. If you are a principal investigator
  (PI), co-PI, trainee, researcher, post-doctoral student or any other similar
  scientific role, you CANNOT create your own eRA Commons account"
  (<https://www.era.nih.gov/manage-accounts/create-and-edit-an-account.htm>,
  read 2026-11-15). And it is explicit that everyone named on an application
  needs an account: "All Senior/Key Personnel and Other Significant
  Contributors listed on an application are required to have active eRA
  Commons usernames (Commons IDs)"
  (<https://www.era.nih.gov/register-accounts/understanding-era-commons-accounts.htm>,
  read 2026-11-15). **NIH's answer to that is a documented route for people in
  exactly this position.** Its own instructions for unaffiliated and
  independent applicants say that "Individual applicants not affiliated with
  an organization or who want to submit a grant application independently must
  complete all the required registrations as though they are an organization.
  There is NO cost associated with ANY of these registrations", and that the
  route "is an option for independent consultants or other individuals not
  affiliated with an organization"
  (<https://grants.nih.gov/grants/ElectronicReceipt/UnaffiliatedUserRegistration.pdf>;
  quoted from two independent university research offices that reproduce the
  NIH FAQ, because that PDF is behind a bot challenge for this machine). So a
  researcher with no appointment can register himself as the organisation,
  become its own signing official, obtain a Commons ID, and file a certified
  biosketch. NIH advises starting that registration "at least six weeks prior
  to a deadline", and the EEMS preliminary application is due 2027-02-18.

  **What this does not settle.** Whether a self-registered individual
  organisation can be the "institution" that satisfies CDAS's "part of the
  institution" test, or the institution that verifies full-time employment for
  a dbGaP application, is not established by any of this. Those are questions
  for CDAS and for dbGaP. But the blocker was never the biosketch, and the
  biosketch can now be obtained without anyone's permission, at no cost, and
  before the application is filed.
- **The CDAS side has an unanswered question in it too.** Whether a
  sponsored affiliation counts as "part of the institution" for the
  approved-users list is with CDAS and outstanding. If the answer is no,
  then being named on the application is still possible — the application
  names the investigative team — but the requester would still not reach the
  data, and the analysis would have to run inside the institution.

## 6. What this document does not do

- It does not claim the requester will be an author of anything. The paper
  does not exist.
- It does not treat a collaborators line as equivalent to authorship, and
  the letters do not either.
- It does not put a name against a role the requester does not hold.
- It does not presume any route will be accepted, by CDAS, by an
  institution or by a company.
