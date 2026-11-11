# PLCO CDAS submission package

**Study:** PLCO (Prostate, Lung, Colorectal, and Ovarian Cancer Screening Trial)
**Access route:** CDAS — Data-Only Project
**Prepared:** 2026-11-10
**Parent document:** [`../DATA-ACCESS-APPLICATIONS.md`](../DATA-ACCESS-APPLICATIONS.md)

---

## 1. What this package is

The CDAS proposal is a web form. This package is everything that goes into it
and everything that has to be signed around it, written out so that the PI can
read it once, the Signing Official can read it once, and nobody has to
reconstruct what was asked from a tracker.

| Part | What it is | Who signs it |
|---|---|---|
| [`01-project-details.md`](01-project-details.md) | Every field of the CDAS form, pre-filled. Includes the project description, which CDAS caps at 500 words. | PI reads and submits |
| [`02-proposal-narrative.md`](02-proposal-narrative.md) | The scientific narrative attached to the proposal: background, aims, data requested and why each element is necessary, the pre-specified analysis, data handling, limitations, timeline, publication plan, references. | PI reads and submits |
| [`03-pi-cover-sheet.md`](03-pi-cover-sheet.md) | The Principal Investigator's identity, the attestations CDAS requires of the PI, the approved-users table, and the signature block. | **PI signs** |
| [`04-signing-official-letter.md`](04-signing-official-letter.md) | The institutional letter. CDAS contacts the Signing Official separately and the Data Transfer and Use Agreement is executed through DocuSign; this letter is the institutional endorsement that sits behind that. | **Signing Official signs** |
| [`05-documents-checklist.md`](05-documents-checklist.md) | Every document CDAS needs, who supplies it, and where it goes. | — |
| [`06-submission-runbook.md`](06-submission-runbook.md) | The operational sequence: the exact URLs, the field-by-field paste map, the questions CDAS will ask and the answers, and what gets a proposal delayed. | — |
| [`07-scoping-inquiry.md`](07-scoping-inquiry.md) | The two messages to CDAS, with the contact form's fields mapped and the traps marked. These ask how many lung-cancer participants have serial plasma and an archived tumour. No account, no signature, and they go first. **Sent on 2026-11-11**; §0 is the sending record. | **sent 2026-11-11** |

## 2. The submission sequence

CDAS's own instructions define the order, and the order matters because two
of the steps cannot be started by the same person.

1. **Register** for CDAS with a login service and fill in the private profile.
2. **Agree to the Data Use Policies.** Two of them bear on this package:
   the data may not be used to identify or contact any participant or
   physician, and **the research proposal will be published on the CDAS
   website** once access is granted. The proposal text below is written to be
   publishable.
3. **The PI creates the project** and fills in the project details from
   `01-project-details.md` and the narrative from `02-proposal-narrative.md`.
4. **The PI identifies the Signing Official** and the approved users.
5. **The PI submits the proposal.** CDAS's instructions are explicit that the
   PI submits it; a delegate may fill in the form, but the PI reviews and
   submits.
6. **CDAS staff assess** whether the data requested are available and
   necessary to answer the research questions, and may ask for more
   information. Their assessment is about availability and necessity, not
   scientific merit.
7. **The NCI Data Access Committee reviews** whether the project addresses a
   scientific question and whether the data are appropriate for it.
8. **After approval, the Signing Official executes the Data Transfer and Use
   Agreement** through DocuSign. CDAS contacts the Signing Official directly
   for this.
9. **Access is granted for 12 months**, after which the project is extended or
   closed out. Renewals and close-out also go through the Signing Official.

## 3. The constraints this package was written against

These are CDAS's rules, not our preferences, and they shape what is in the
package.

- **The PI must be a permanent employee at professor level** — assistant,
  associate, tenure-track or tenured professor, or a senior researcher. CDAS
  states that the PI cannot be a post-doc, trainee or lab technician. The
  position title field has to reflect that.
- **The PI is the person who submits, renews and closes out the project.**
  CDAS's instructions say the Data Access Requestor "will register and be
  responsible for the project, its submission, renewals and close-out", and
  the Signing Official is "permanently employed at the institution" and
  authorised to sign for it. A researcher with no institutional appointment
  at professor level therefore cannot submit either PLCO application; the
  route needs an institutional PI who agrees to carry it, with the
  researcher's own work done under it.
- **The project description is capped at 500 words.** The checker
  `scripts/check_plco_cdas_package.py` counts the words between the markers
  in `01-project-details.md` and fails if the cap is exceeded, so the limit
  cannot be discovered by rejection.
- **The proposal becomes public.** CDAS publishes it on the website once
  access is granted. Nothing in the package depends on it being confidential,
  and the conflicts disclosure in the narrative is written for publication.
- **Dates of diagnosis are not in the standard de-identified dataset.** CDAS
  can release them in a Limited Data Set where they are essential to a
  specific research project, and the Data Transfer and Use Agreement satisfies
  the HIPAA requirement for that. The lead time between the blood draw and
  diagnosis is the measurement this project turns on, so the request for the
  Limited Data Set is explicit rather than implied.
- **Collaborators at other institutions need their own project proposal** with
  the same project details. The approved-users table in
  `03-pi-cover-sheet.md` is therefore split by institution, and anyone
  outside the PI's institution cannot simply be added to it.

## 4. What is still missing

Everything marked `[PI]` or `[SO]` needs a person, and it is filled in a
**local copy** of this package, not in the repository:

```bash
python scripts/build_plco_cdas_pdf.py --init-local     # copy into build/package-private
$EDITOR build/package-private/03-pi-cover-sheet.md     # fill in the markers
python scripts/check_plco_cdas_package.py --package-dir build/package-private
                                            # what is still to fill?
python scripts/build_plco_cdas_pdf.py --package-dir build/package-private
                                            # print the filled copy
```

`build/` is gitignored, so the filled copy never reaches the repository, and
the checker fails if a `[PI]` or `[SO]` field is filled in in the committed
package — the repository stays a template, and what gets signed is the copy.
Running `--init-local` again refreshes the documents that have not been
edited and leaves the edited ones alone.

The checklist in
`05-documents-checklist.md` is the authoritative list; the state of the
application as a whole is tracked in
[`../DATA-ACCESS-APPLICATIONS.md`](../DATA-ACCESS-APPLICATIONS.md) and, in
machine-readable form, in `results/application_tracker/application_tracker.json`.

Two items are not paperwork. The **number of lung-cancer participants with
usable serial plasma and a matched tumour** determines whether the request is
worth the assay cost, and it can be asked of the coordinating centre without
an application. And the **assay cost and timeline** for running the
transcript assay on the aliquots is not yet in the package, because it
depends on that count.

## 5. Checking and printing this package

```bash
python scripts/check_plco_cdas_package.py     # check the package
python scripts/build_plco_cdas_pdf.py         # print it to build/
python scripts/build_plco_cdas_pdf.py --init-local
                                            # copy it for filling in, and print
                                            # the filled copy with
                                            #   --package-dir build/package-private
python scripts/check_plco_cdas_package.py --package-dir build/package-private
                                            # check the filled copy: reports
                                            # every value still to fill in
```

`--init-local` never overwrites a document that has already been edited: the
local copy is the only place the PI's details exist, so a refresh brings the
template's later changes in without taking away what has been filled in.

The checker verifies the 500-word cap, that every CDAS field is present and
filled or explicitly marked as the PI's to complete, that the numbers quoted
in the package match this repository's artefacts, that both signature blocks
have a ruled line to sign on, that the runbook carries the entry points
and the points a person has to cross, and that the committed package still
holds the PI's and the Signing Official's own details as markers rather than
filled in. It runs in CI. Pointed at the local copy it checks the same
things and reports how many values are still to fill in.

The PDF builder renders the package from these markdown files, so the thing
that gets signed is the thing that is in the repository. It is a build
product and is not committed, because a committed PDF would drift from the
markdown the moment either side was edited. Each document in the PDF ends
with the hash of the sources it was built from, so a printed copy carries the
state it was printed from.
