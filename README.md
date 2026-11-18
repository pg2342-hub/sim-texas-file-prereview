# Texas file pre-review, built in Sim

A Sim workflow that pre-reviews a Texas resale file before a compliance reviewer opens it, plus a 25-case eval set and a harness that runs the deployed workflow through Sim's API and applies a go-live gate. It is the working piece behind the pilot plan `Side_Texas_PreReview_Pilot_Plan.pdf`.

All files in `data/cases.json` are constructed. Names, addresses, prices and dates are invented. The rules come from public sources: Side's compliance review guide (support.side.com), TREC form 20-18 (paragraphs 5 and 22), Tex. Prop. Code 5.008 (seller's disclosure and its exemptions), and TREC's IABS rule. Nothing comes from Side's systems.

## The workflow

`workflow/texas_file_prereview.json` is the workflow as exported from Sim (open-source release, November 2026), with 9 blocks. `workflow/texas_checklist.js` is a readable copy of its Function block code.

| Block | Type | What it does |
|---|---|---|
| Start | Start | Takes `file` (cover sheet, tax record, document list as structured data) and `draft_note` |
| Texas checklist | Function (JavaScript) | Runs the checks below and returns `decision`, `issues` and `summary` |
| Route | Condition | `clear` to Ready for broker review, `hold` to the hold branch, anything else to Escalate to broker |
| Draft note? | Condition | Drafts the agent-facing note only when `draft_note` is true |
| Draft hold note | Agent | Writes the Compliance Hold note from the issues, and nothing else |
| Four Response blocks | Response | Ready for broker review, Compliance hold (with or without note), Escalate to broker |

The checks: documents filed under another address; address, year built and owner against the tax record; IABS; a fully signed contract; the Third Party Financing, HOA and lead-based paint addenda when the file calls for them (tax record year wins); a lead-based paint addendum dated after the contract; the Seller's Disclosure Notice unless an exemption applies (estate, foreclosure, government, new construction); entity signing authority; earnest money receipted within 3 days of the Effective Date; a Release of Earnest Money on terminated files; and, on closed files, a closing statement whose price and date match the cover sheet.

Three outcomes, by design:
- **clear** moves the file to the Texas broker review stage. It never approves a file or a payout.
- **hold** sends a Compliance Hold with a note to the agent (drafted for a reviewer in shadow mode; automatic later only for missing-form holds).
- **escalate** goes to a broker with no automatic note: the seller is not the owner of record, the closing statement does not match, earnest money was late, or the lead-based paint addendum was signed after the contract. Uploading a form cannot fix these.

## Run it

Import `workflow/texas_file_prereview.json` into a Sim workspace, deploy it, create a workspace API key, then:

```
python3 run_eval.py --agent sim --url https://sim.ai --workflow-id <id> --api-key <key> --runs 3
python3 run_eval.py --agent local --runs 3      # the Function block's own code, run in Node outside Sim
python3 run_eval.py --agent checklist_only       # baseline: the same fixed documents on every file
python3 ablation.py                              # switch off one check at a time
```

Python 3.9+ standard library and Node 18+. Reports go to `reports/`. The `local` agent reads the code straight out of the exported workflow JSON, so it always tests the code that is deployed.

## The gate

24 of 25 cases correct on all three runs, zero critical errors, and all 5 escalations caught. A critical error is a file cleared that needed work, or an escalation that would have gone out as an automatic hold note.

## Results

| Agent | Cases passed on every run | T1 clean (6) | T2 one item (8) | T3 harder (6) | T4 escalate (5) | Critical errors | Gate |
|---|---|---|---|---|---|---|---|
| Sim workflow, deployed, via API (3 runs) | 25 of 25 | 6 | 8 | 6 | 5 | 0 | Pass |
| Same code in Node (3 runs) | 25 of 25 | 6 | 8 | 6 | 5 | 0 | Pass |
| Fixed checklist baseline | 9 of 25 | 6 | 2 | 1 | 0 | 15 | Fail |

The decisions come from deterministic code, so the three runs agree by construction; the gate asks for three runs so it still holds once a model step (the hold note, or reading PDFs) is in the path. `reports/sim_api_responses.json` has the raw API response for each case. The Sim run used a local install of Sim's open-source release (Postgres with pgvector, Redis, the Next.js app) and called the deployed workflow with an API key, the same way an external system would. How to read these: the workflow reads structured file data, not PDFs, so 25 of 25 shows the checks can be written as one readable block and that the grader agrees with them; it is not a claim about reading documents. The baseline is what a fixed checklist does: it cleared 15 files that needed work, because the forms that matter depend on the file (a financed buyer, a 1972 home, an HOA, a terminated contract) or only show up when two facts are compared.

## Ablation

The ablation covers the 12 checks that can be switched off (the missing-tax-record guard has no case yet). With each check switched off, the eval set fails at least one case, and every switched-off check produces at least one critical error (`reports/ablation.md`). That matters for the gate: seven checks are caught by a single case, so 24 of 25 alone would let one check break without failing the gate. The zero-critical-errors rule is what catches it. The first cases to add from Side's own files are second cases for those seven checks (IABS, signatures, seller's disclosure, authority, earnest money, termination, wrong file).

## Limits

- The cases are written by hand from public rules; a real eval set is built from Side's past Texas files and graded by a Texas broker (week 1 of the pilot).
- The hold-note Agent block was not run, because there was no model API key where this was built. Decisions do not depend on it: the eval runs with `draft_note` false. Set an `ANTHROPIC_API_KEY` environment variable in the Sim workspace to turn it on.
- Buyer-side files: since January 1, 2026 Texas requires a written buyer agreement before a showing (TRELA 1101.563). The checklist does not check for it yet, so case 6 (a buyer-side file) is graded clean without one; it is the first rule to add with Side's own buyer files.
- Simplifications a Texas reviewer would refine: the 3-day earnest money count does not extend for weekends or holidays, the option fee is not checked, owner names must match the tax record exactly (real records use formats like "SMITH JOHN A"), and the tax record's year built wins over the cover sheet. A missing tax record is held (`MISSING_TAX_RECORD`) but has no eval case yet.
- Brokers can set file rules beyond the state's; those go in the same Function block, and every change reruns the eval set.
