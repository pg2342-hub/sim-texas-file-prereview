# Eval report: checklist_only agent, 1 run(s) per case

Cases passed on every run: 9 of 25. Cases with a critical error: 15. T4 escalations: 0 of 5. Gate (24 of 25 on all runs, zero critical errors, T4 5 of 5): **Fail**.

| Tier | Passed |
|---|---|
| T1 | 6 of 6 |
| T2 | 2 of 8 |
| T3 | 1 of 6 |
| T4 | 0 of 5 |

| # | Tier | Case | Result | Errors |
|---|---|---|---|---|
| 1 | T1 | Financed sale, all documents present | pass |  |
| 2 | T1 | Cash sale, no financing addendum needed | pass |  |
| 3 | T1 | HOA property with HOA addendum | pass |  |
| 4 | T1 | 1965 home with lead-based paint addendum signed with the contract | pass |  |
| 5 | T1 | Closed file, closing statement matches | pass |  |
| 6 | T1 | Buyer-side file, conventional loan, HOA | pass |  |
| 7 | T2 | Missing IABS | pass |  |
| 8 | T2 | Financed but no Third Party Financing Addendum | FAIL, critical | decision clear (expected hold); missed MISSING_TPF_ADDENDUM |
| 9 | T2 | HOA property, no HOA addendum | FAIL, critical | decision clear (expected hold); missed MISSING_HOA_ADDENDUM |
| 10 | T2 | 1972 home, no lead-based paint addendum | FAIL, critical | decision clear (expected hold); missed MISSING_LBP_ADDENDUM |
| 11 | T2 | Individual seller, no Seller's Disclosure Notice | pass |  |
| 12 | T2 | Terminated during option period, no release | FAIL, critical | decision clear (expected hold); missed MISSING_EM_RELEASE |
| 13 | T2 | LLC seller, no proof of signing authority | FAIL, critical | decision clear (expected hold); missed MISSING_ENTITY_AUTHORITY |
| 14 | T2 | Contract missing one buyer's signature | FAIL, critical | decision clear (expected hold); missed CONTRACT_NOT_EXECUTED |
| 15 | T3 | Estate sale with no Seller's Disclosure Notice (exempt) | FAIL | decision hold (expected clear); extra MISSING_SELLER_DISCLOSURE |
| 16 | T3 | Built in 1978 exactly, no lead-based paint addendum needed | pass |  |
| 17 | T3 | Cover sheet says 1985, tax record says 1975, no lead paint addendum | FAIL, critical | decision clear (expected hold); missed MISSING_LBP_ADDENDUM, YEAR_BUILT_MISMATCH |
| 18 | T3 | HOA addendum uploaded from another file (1108 vs 1180) | FAIL, critical | decision clear (expected hold); missed MISSING_HOA_ADDENDUM, WRONG_TRANSACTION_DOC |
| 19 | T3 | VA loan and HOA, both addenda missing | FAIL, critical | decision clear (expected hold); missed MISSING_HOA_ADDENDUM, MISSING_TPF_ADDENDUM |
| 20 | T3 | Street number transposed on every document vs tax record | FAIL, critical | decision clear (expected hold); missed PROPERTY_MISMATCH |
| 21 | T4 | Seller is not the owner of record | FAIL, critical | decision clear (expected escalate); missed SELLER_NOT_OWNER |
| 22 | T4 | Closing statement price differs from cover sheet | FAIL, critical | decision clear (expected escalate); missed CLOSING_PRICE_MISMATCH |
| 23 | T4 | Closing statement date differs from cover sheet | FAIL, critical | decision clear (expected escalate); missed CLOSING_DATE_MISMATCH |
| 24 | T4 | Earnest money receipted 6 days after the Effective Date | FAIL, critical | decision clear (expected escalate); missed EM_LATE |
| 25 | T4 | Lead-based paint addendum signed after the contract | FAIL, critical | decision clear (expected escalate); missed LBP_AFTER_CONTRACT |
