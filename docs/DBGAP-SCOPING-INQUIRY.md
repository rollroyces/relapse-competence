# Scoping inquiry to dbGaP — the paste-ready version

**One question, three parts.** It asks whether a researcher with no
institutional appointment can be the Principal Investigator of a dbGaP data
access request through an organisation he has registered himself. The answer
decides whether the germline half of the programme's attribution set is
reachable at all without a professor's time.

**Status: draft, not sent.** No request has been started, no application has
been filed, and no organisation has been registered. A question sent to dbGaP
is his to send.

**It is not part of the PLCO submission package.** The CDAS scoping
inquiries are in
[`plco-cdas-submission-package/07-scoping-inquiry.md`](plco-cdas-submission-package/07-scoping-inquiry.md),
because they go to CDAS. This one goes to NCBI.

---

## 1. The route, and the fields

Two routes, both published:

| Route | Where | What it is |
|---|---|---|
| the contact form | `https://dbgap.ncbi.nlm.nih.gov/classic/aa/wga.cgi?page=email` | "Contact dbGaP Staff". It is public: the page was read on 2026-11-15 without a login, and it asks for Name, E-mail, Phone (optional) and Question / Comment. |
| e-mail | `dbgap-help@ncbi.nlm.nih.gov` | Published on `https://dbgap.ncbi.nlm.nih.gov/ss/`: "please contact the dbGaP staff at dbgap-help@ncbi.nlm.nih.gov". |

**The form is the route for this letter.** The Question / Comment box is a
single textarea (`rows="8" cols="60"`, no `maxlength`), so the whole letter
goes into it; the e-mail address is the alternative if the desk prefers it.

**Read on 2026-11-15, the form carries no bot check and no token.** There is
no captcha element and no hidden token in the markup, so a person does not
have to solve anything before the message can be sent. That is a difference
from the Wholomics form, which is captcha-protected and cannot be filled by
a script.

**The legacy site is being replaced.** `https://dbgap.ncbi.nlm.nih.gov/ss/`
carries the notice "Try the new NCBI dbGaP registration system. The new
registration system will replace this legacy site in fall 2026." The
contact route may move; the address `dbgap-help@ncbi.nlm.nih.gov` is the
part that is unlikely to move with it.

---

## 2. Why it exists: two requirements that pull in opposite directions

**The PLCO programme's own rule.** The PLCO EEMS Policies and Procedures,
§10, on the germline route:

> "Any bona fide research group may apply through dbGaP … This application
> includes verification by the institution that **the investigators are full
> time employees**, the IT system meets specific standards for the protection
> of sensitive data, any posted embargo will be respected, and the research
> will conform to standard protections of privacy and confidentiality."

(<https://cdas.cancer.gov/files/download/l0g32brjto/policies_procedures_plco.pdf>,
p. 15 of 17, read 2026-11-13.)

**And dbGaP's own rule, which is stricter and is not PLCO's to waive.** The
dbGaP Authorized Access page:

> "Extramural Investigators must be permanent employees of their institution
> at a level equivalent to a tenure-track professor or senior scientist with
> responsibilities that most likely include laboratory administration and
> oversight. Laboratory staff and trainees such as graduate students and
> postdoctoral fellows are not permitted to submit project requests."

(<https://dbgap.ncbi.nlm.nih.gov/classic/aa/wga.cgi?page=login>, read
2026-11-15.)

**And the two people the request needs, neither of whom may be the PI.** The
NIH guide to requesting access, *How to Request and Access Datasets from
dbGaP* (page footer: "This page last updated on: September 16, 2026"), lists
among the most common reasons for rejection:

> "Personnel errors (for example: requestor is not the PI, collaborators are
> from different institutions, the information technology (IT) director is not
> identified; **PI has identified him/herself as the signing official or the
> IT director for the project**)"

and states:

> "In addition, the signing official's and IT director's emails must be from
> their organization, instead of a personal email address (for example, a
> personal gmail address.)"

and: "For all non-intramural investigators, dbGaP receives information on the
signing official through eRA."

(Read on 2026-11-15 from the Internet Archive's capture of
`grants.nih.gov/policy-and-compliance/policy-topics/sharing-policies/accessing-data/dbgap`,
capture of 2026-10-14; the live page is behind a bot check that blocks
non-browser clients.)

The Data Use Certification for this study defines the role:

> "Institutional Signing Official: The label, 'Signing Official,' is used in
> conjunction with the NIH eRA Commons and refers to the individual that has
> institutional authority to legally bind the institution in grants
> administration matters."

(the PLCO Data Use Certification, version January 25, 2025, p. 9, read
2026-11-15 from
`https://dbgap.ncbi.nlm.nih.gov/aa/wga.cgi?view_pdf&stacc=phs001286.v5.p2`.)

**What the three rules together appear to do.** A one-person organisation
satisfies "permanent employee of their institution" on its face, but it has
nobody who can be the Institutional Signing Official, because the one person
in it is the PI and the PI may not be the signing official — and nobody who
can be the IT Director either.
**That is an inference from the rules and not a ruling**, and it is exactly the
thing that has to be put to dbGaP rather than
assumed here.

**The route this sits on.** This is the germline half of the attribution set.
The clinical-data half can be reached by an affiliation, because that is
what CDAS's approved-project record shows; this half needs employment. That
asymmetry is what reorders the hosting routes, and it is why the
self-registered organisation — the one route that needs nobody's permission —
has to be tested rather than assumed.

---

## 3. The message

Plain text, 3,392 characters.

<!-- BEGIN DBGAP MESSAGE -->
Dear dbGaP staff,

I am scoping a data access request for the PLCO genome-wide association study data, and I cannot answer one question from the published instructions, because the answer decides whether the request can be filed at all. I would like to ask it in a specific form, so that it can be answered yes or no.

What I am asking about. I am a researcher with no current institutional appointment, employed by nobody. NIH provides a route for this: an applicant who is not affiliated with an organisation, or who wants to submit independently, "must complete all the required registrations as though they are an organization", there is no cost for any of those registrations, and NIH describes that route as an option for "independent consultants or other individuals not affiliated with an organization". The registration would produce an organisation of one, with its own institutional e-mail address and its own record in eRA Commons. Whether such an organisation can also supply the people your process needs is exactly what I am asking.

Three of your own rules bear on that, and I would rather ask than assume.

Your Authorized Access page states that "Extramural Investigators must be permanent employees of their institution at a level equivalent to a tenure-track professor or senior scientist", and that "Laboratory staff and trainees such as graduate students and postdoctoral fellows are not permitted to submit project requests". The PLCO programme's own policy for this study adds that the application "includes verification by the institution that the investigators are full time employees".

Your guide to requesting access lists among the common reasons for rejection that the "PI has identified him/herself as the signing official or the IT director for the project", and states that "the signing official's and IT director's emails must be from their organization, instead of a personal email address (for example, a personal gmail address)". The Data Use Certification defines the Institutional Signing Official as "the individual that has institutional authority to legally bind the institution in grants administration matters".

Three questions.

1. If the Principal Investigator holds no appointment, is employed by nobody, and files through an organisation he has registered himself under the NIH route for unaffiliated and independent applicants, will dbGaP accept that organisation as the Requester institution for a data access request for phs001286.v5.p2?

2. If it will, who may serve as the Institutional Signing Official for such an organisation? The signing official must be able to legally bind the institution, and a request in which the Principal Investigator has identified himself as the signing official is rejected, so in an organisation of one there appears to be nobody who can fill that role.

3. And the same question for the IT Director, whose e-mail address must also be organisational rather than personal.

I ask because this is the one route to this data that does not depend on a professor's time, and because I would rather be told no now than after months of paperwork. I am not filing a request and I am not asking for an exception to any rule: if the answer is that an organisation of one cannot request this data, that is a complete answer and it settles the question for me.

Thank you for your help.

Royce Lam
roycelam@umich.edu
<!-- END DBGAP MESSAGE -->

**The form was filled and read back on 2026-11-15 at 19:27 HKT.
The submission has not been made.** The form at
`https://dbgap.ncbi.nlm.nih.gov/classic/aa/wga.cgi?page=email` was filled
with the text above, and every field was read back out of the page rather
than assumed: Name `Royce Lam`, E-mail `roycelam@umich.edu`, Phone left
empty, and the Question / Comment box holding exactly the text between the
markers above — 3,392 characters, and the digest
`a700bd3132af7d53cef49b2328b7be829707edad1891edcef555a0b621417cb7`.
`scripts/verify_report_consistency.py` recomputes that digest from the
block between the markers, so an edit to the message breaks the check
instead of passing unnoticed. **Nothing has been sent.** The form is filled
and ready; sending it is a separate and irreversible action, and it needs
an explicit instruction.

---

## 4. Before you send

1. **Which route.** The form at
   `https://dbgap.ncbi.nlm.nih.gov/classic/aa/wga.cgi?page=email`, with
   Name `Royce Lam`, E-mail `roycelam@umich.edu`, Phone left blank, and the
   letter above in the Question / Comment box. Or e-mail to
   `dbgap-help@ncbi.nlm.nih.gov` with the same subject and body.
2. **The subject.** The form has no subject field; e-mail needs one.
   `Question about Authorized Access for phs001286.v5.p2` names the study
   and the part of the process.
3. **The reply comes back to `roycelam@umich.edu`**, which is the address
   the form asks for and the one that reads.
4. **The legacy site is being replaced in fall 2026.** If the form has moved
   by the time this goes out, the e-mail address is the stable route.
5. **No exception is requested.** The letter asks what the rules require,
   and says so in the last paragraph. If the answer is no, that is a
   complete answer and the route map changes accordingly.

---

## 5. What this letter deliberately does not do

- It does not file a data access request, start one, or register an
  organisation. It asks a question about eligibility and stops there.
- It does not ask for an exception, and it does not suggest that the rules
  are unreasonable.
- It does not claim that the organisation route is open. It says the rules
  appear to conflict and asks which way they resolve.
- It does not disclose what the programme is for in detail. The germline
  data is being asked about because the attribution needs a tumour genotype
  matched to a plasma genotype, and that is enough for the desk to answer
  the eligibility question; the rest of the programme is not the desk's
  business.
- It does not quote anybody else's e-mail address, and it does not name any
  other researcher.
