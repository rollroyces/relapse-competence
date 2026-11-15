# Becoming the institution: a runbook for the affiliation the applications need

**Status: a plan, not an action.** Nothing here has been started, filed or
registered. This document sets out what the applications actually require, the
two ways the requirement can be met, and what each way costs.

**Why this document exists.** Every PLCO route in
[`DATA-ACCESS-APPLICATIONS.md`](DATA-ACCESS-APPLICATIONS.md) turns on the same
three things, and all three are fields in an application rather than
qualities of a person:

| What the application asks for | Where it asks | Route |
|---|---|---|
| an institution, and its location | the project and PI block of the data-only proposal | PLCO-DATA |
| a name and an **institutional e-mail address** for each approved user | the approved-users table | PLCO-DATA |
| an **institutional e-mail address** and an **NIH biosketch** for each member of the investigative team | the EEMS application | PLCO-EEMS |

The requester has none of the three. The routes for obtaining them are set out
in [`HOSTING-ROUTES.md`](HOSTING-ROUTES.md), and this document is the part
that can be carried out without anybody's permission.

---

## 1. Two ways to satisfy the requirement, and which is which

**Route 1 — be sponsored.** An institution takes him on: a faculty sponsor and
a sponsoring unit under SPG 601.42 at the University of Michigan, a visiting
appointment elsewhere, or employment. The application then lists him under that
institution, with that institution's e-mail address, and a signing official at
that institution creates whatever account the application needs. This is what
the letters ask for, and it is the better route where it is available,
because it brings a PI who can carry the proposal at the same time.

**Route 2 — be the institution.** He registers himself as an organisation,
with himself as the signing official, and the application lists his own
organisation. This route exists because NIH documents it, and it requires
nobody's agreement. It is the fallback for when Route 1 does not arrive, and
it is the route that turns the requester's standing from a favour into a fact.

**The two are not exclusive.** A sponsored affiliation can be affiliated with
a self-registered organisation — eRA Commons will affiliate an existing
account to a new institution, and a signing official there can do it — so
Route 1 and Route 2 can be combined if the host's sponsorship is a
Covered Visitor arrangement rather than employment.

## 2. The steps of Route 2

**Step 1 — an ORCID iD.** Free, self-service, and the anchor for everything
else: a Commons ID "must be linked to an ORCID iD" for anyone listed as
Senior/Key Personnel, and the biosketch's persistent-identifier field takes
the ORCID. This step is worth doing whatever else happens, because it also
belongs in this repository: `CITATION.cff` already names the author, and
adding the ORCID there makes the software citable by identifier rather than
by name.

**Step 2 — register the organisation.** NIH's instructions for unaffiliated
and independent applicants: "Individual applicants not affiliated with an
organization or who want to submit a grant application independently must
complete all the required registrations as though they are an organization.
**There is NO cost associated with ANY of these registrations.**" The route is
described as "an option for independent consultants or other individuals not
affiliated with an organization"
(<https://grants.nih.gov/grants/ElectronicReceipt/UnaffiliatedUserRegistration.pdf>;
quoted from two independent university research offices reproducing the NIH
FAQ, because that PDF is behind a bot challenge for this machine). Registering
an organisation means the organisation's own registration, with a signing
official — which, in this route, is him.

**Step 3 — a Commons ID linked to the ORCID.** eRA Commons is explicit that
the scientist cannot do this alone: "Only officials from your own organization
can create a new eRA Commons account. If you are a principal investigator
(PI), co-PI, trainee, researcher, post-doctoral student or any other similar
scientific role, you CANNOT create your own eRA Commons account"
(<https://www.era.nih.gov/manage-accounts/create-and-edit-an-account.htm>,
read 2026-11-15). Step 2 is what supplies the "official" who can. And the
requirement is real: "All Senior/Key Personnel and Other Significant
Contributors listed on an application are required to have active eRA Commons
usernames (Commons IDs)"
(<https://www.era.nih.gov/register-accounts/understanding-era-commons-accounts.htm>,
read 2026-11-15).

**Step 4 — a CDAS account.** The EEMS instructions name the three login
services — "ID.me, Login.gov, or the NIH Login Service" — and recommend
ID.me or Login.gov for anyone who has not already established NIH
credentials. **This is worth noting: the University of Michigan's RAS is an
institutional sign-on, so it is not the route for a self-registered
organisation, while ID.me and Login.gov are.** The approved-projects
instructions list the same three services.

**Step 5 — a SciENv profile and a certified biosketch.** The biosketch is
what the EEMS application asks for per investigative-team member. The Common
Form's fields accommodate this situation: appointments and positions include
any titled position "whether or not remuneration is received, and whether
full-time, part-time, or voluntary", and the organisation's location takes a
country.

**Step 6 — put the identifiers in the places that ask for them.** The
application's approved-users row and investigative-team entry take a name, an
institutional e-mail address and an institution; the biosketch carries the
ORCID and the Commons ID; this repository's `CITATION.cff` carries the
ORCID.

## 3. What it costs, and what it does not solve

**Cost.** No money: NIH states there is no cost for the registrations. The
real cost is time, and NIH's own guidance is to start "at least six weeks
prior to a deadline". The deadline that matters is the EEMS preliminary
application, **2027-02-18**, with the full application due 2027-04-01 and
"4-6 months from application submission to review outcome" on top of that.

**What it does not solve.**

- **Whether CDAS accepts such an organisation as "part of the
  institution".** That is the question in message G, and it is unanswered.
  A self-registered organisation is not the same thing as a self-description
  typed into a form; the precedent for a self-description is NLST-43, whose
  Institution field reads "Statistical Consultant", but that is a 2013
  approval.
- **Whether it can be the institution that verifies full-time employment for
  a dbGaP application**, which is the germline half of the attribution. The
  dbGaP application requires "verification by the institution that the
  investigators are full time employees"; whether a sole-person
  organisation can verify that about its own principal is not established by
  anything here, and is a question for dbGaP.
- **The applicant's own seniority.** If the requester is to be the
  Principal Investigator of his own proposal, the "level equivalent to an
  academic professor … or senior researcher" test has to be argued on a
  publication record rather than on a job title. A registered organisation
  does not supply that.

## 4. One thing that is not a formality

Registering an organisation is a binding act. It creates a public
registration record in his own name, with a signing official who can sign on
its behalf, and an organisation profile that any reviewer can look up. It is
also, on the evidence of the eRA rules, the only way for a person in his
position to hold the accounts that the applications require.

**That is why this document stops at a checklist.** It is the requester's
decision to create that record, it is his name on it, and the decision does
not depend on anybody else answering anything. It should be taken knowing
that it produces a durable, public statement that the requester is
conducting this work as an organisation, which is a different thing from
conducting it as an individual.

## 5. What this document does not do

- It does not assert that CDAS or dbGaP will accept a self-registered
  organisation. Both questions are open and are named as such.
- It does not assert that the requester qualifies as a senior researcher.
- It does not claim any part of the registration has been started.
- It does not treat the absence of a sponsor as a reason to wait, because
  the point of Route 2 is that it does not need one.
