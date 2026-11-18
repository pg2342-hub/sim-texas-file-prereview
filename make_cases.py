"""Builds data/cases.json: 25 constructed Texas resale files. All names, addresses and numbers are invented."""
import json, copy

def base(fid, addr, buyers, sellers, price, year, financing="conventional", hoa=False, status="pending",
         side="listing", seller_type="individual", eff="2026-10-06", close="2026-11-06", apn=None):
    cs = dict(file_id=fid, address=addr, side=side, status=status, price=price, effective_date=eff,
              close_date=close, financing=financing, hoa=hoa, year_built=year, seller_type=seller_type,
              buyers=buyers, sellers=sellers)
    tax = dict(owner=sellers[0], address=addr, apn=apn or "R" + str(100000 + sum(map(ord, addr)) * 37 % 900000), year_built=year)
    docs = [
        dict(type="IABS", address=addr, date="2026-09-20"),
        dict(type="Resale Contract", form="TREC 20-18", address=addr, date=eff, signed_by=buyers + sellers),
        dict(type="Seller's Disclosure Notice", address=addr, date="2026-09-28"),
        dict(type="Earnest Money Receipt", address=addr, date="2026-10-08", amount=round(price * 0.01)),
    ]
    if financing != "cash":
        docs.append(dict(type="Third Party Financing Addendum", form="TREC 40-11", address=addr, date=eff))
    if hoa:
        docs.append(dict(type="HOA Addendum", form="TREC 36-10", address=addr, date=eff))
    if year < 1978:
        docs.append(dict(type="Lead-Based Paint Addendum", form="TREC OP-L", address=addr, date=eff))
    if status == "closed":
        docs.append(dict(type="Closing Statement", address=addr, price=price, close_date=close))
    return dict(file_id=fid, cover_sheet=cs, tax_record=tax, documents=docs)

def drop(f, t):
    f["documents"] = [d for d in f["documents"] if d["type"] != t]; return f
def doc(f, t):
    return next(d for d in f["documents"] if d["type"] == t)

cases = []
def case(tier, title, f, decision, codes, why):
    cases.append(dict(id=len(cases) + 1, tier=tier, title=title, file=f,
                      expected=dict(decision=decision, codes=sorted(codes)), why=why))

# T1: clean files that must clear (6)
case("T1", "Financed sale, all documents present",
     base("TX-1001", "2207 Larkspur Trace, Austin, TX 78745", ["Dana Whitfield"], ["Marcus Oyelaran"], 465000, 2004),
     "clear", [], "Standard financed resale with every required document.")
case("T1", "Cash sale, no financing addendum needed",
     base("TX-1002", "918 Quarry Hollow Dr, San Antonio, TX 78258", ["Priya Raman"], ["Helen Castillo"], 389000, 2011, financing="cash"),
     "clear", [], "Cash buyers do not need the Third Party Financing Addendum.")
case("T1", "HOA property with HOA addendum",
     base("TX-1003", "4410 Cypress Wren Ln, Katy, TX 77494", ["Owen Brandt", "Lia Brandt"], ["Tomasz Nowak"], 512000, 2016, hoa=True),
     "clear", [], "Mandatory owners association, addendum present.")
case("T1", "1965 home with lead-based paint addendum signed with the contract",
     base("TX-1004", "1312 Pecan Grove St, Houston, TX 77008", ["Jun Park"], ["Ruth Adeyemi"], 598000, 1965),
     "clear", [], "Pre-1978 home, addendum dated the same day as the contract.")
case("T1", "Closed file, closing statement matches",
     base("TX-1005", "77 Bluebonnet Ridge, Round Rock, TX 78664", ["Sam Ortiz"], ["Kelly Huang"], 342500, 1999, status="closed"),
     "clear", [], "Closed file with matching price and date.")
case("T1", "Buyer-side file, conventional loan, HOA",
     base("TX-1006", "5120 Heron Point Ct, Frisco, TX 75034", ["Amara Diallo"], ["Victor Lindqvist"], 735000, 2019, hoa=True, side="buyer"),
     "clear", [], "Buyer-side file with every required document.")

# T2: one missing or defective item, hold with a note to the agent (8)
case("T2", "Missing IABS", drop(base("TX-2001", "6034 Saddle Creek Rd, Fort Worth, TX 76132", ["Ian Mercer"], ["Gloria Reyes"], 318000, 1996), "IABS"),
     "hold", ["MISSING_IABS"], "Most common Texas return reason in Side's own guide.")
case("T2", "Financed but no Third Party Financing Addendum",
     drop(base("TX-2002", "240 Mesquite Bend, Georgetown, TX 78628", ["Hana Sato"], ["Derek Molloy"], 429000, 2008, financing="FHA"), "Third Party Financing Addendum"),
     "hold", ["MISSING_TPF_ADDENDUM"], "FHA loan, addendum missing.")
case("T2", "HOA property, no HOA addendum",
     drop(base("TX-2003", "3318 Willow Lake Dr, Sugar Land, TX 77479", ["Ben Okafor"], ["Irene Kwan"], 476000, 2002, hoa=True), "HOA Addendum"),
     "hold", ["MISSING_HOA_ADDENDUM"], "Mandatory association, addendum missing.")
case("T2", "1972 home, no lead-based paint addendum",
     drop(base("TX-2004", "901 Elmhurst Ave, Dallas, TX 75214", ["Carla Mendes"], ["Arthur Pike"], 655000, 1972), "Lead-Based Paint Addendum"),
     "hold", ["MISSING_LBP_ADDENDUM"], "Pre-1978 home, addendum missing.")
case("T2", "Individual seller, no Seller's Disclosure Notice",
     drop(base("TX-2005", "1450 Prairie Clover Way, Plano, TX 75023", ["Nina Volkova"], ["George Abbott"], 452000, 1988), "Seller's Disclosure Notice"),
     "hold", ["MISSING_SELLER_DISCLOSURE"], "No exemption applies.")
f = base("TX-2006", "8823 Canyon Oak Trl, Austin, TX 78759", ["Rafael Cruz"], ["Megan Doyle"], 548000, 1994, status="terminated")
case("T2", "Terminated during option period, no release", f, "hold", ["MISSING_EM_RELEASE"],
     "Side's guide lists a missing Release of Earnest Money as a common Texas return.")
f = base("TX-2007", "12 Harbor Light Ln, League City, TX 77573", ["Tess Morgan"], ["Bayline Holdings LLC"], 389900, 2013, seller_type="entity")
case("T2", "LLC seller, no proof of signing authority", f, "hold", ["MISSING_ENTITY_AUTHORITY"],
     "Entity sellers need articles or a resolution; owner of record matches, so no escalation.")
f = base("TX-2008", "3907 Lantana Hill, McKinney, TX 75070", ["Aaron Feld", "Mira Feld"], ["Paula Grant"], 501000, 2010)
doc(f, "Resale Contract")["signed_by"] = ["Aaron Feld", "Paula Grant"]
case("T2", "Contract missing one buyer's signature", f, "hold", ["CONTRACT_NOT_EXECUTED"], "Co-buyer did not sign.")

# T3: harder files (6): traps that must clear, and problems that only show when two facts are compared
f = base("TX-3001", "615 Ash Street, Waco, TX 76704", ["Leo Tran"], ["Estate of Doris Kell"], 214000, 1958, seller_type="estate")
f = drop(f, "Seller's Disclosure Notice"); f["tax_record"]["owner"] = "Doris Kell"
f["documents"].append(dict(type="Letters Testamentary", address="615 Ash Street, Waco, TX 76704", date="2026-08-14"))
case("T3", "Estate sale with no Seller's Disclosure Notice (exempt)", f, "clear", [],
     "Tex. Prop. Code 5.008(e) exempts a fiduciary administering an estate; owner of record explained by letters testamentary. Must not over-flag.")
case("T3", "Built in 1978 exactly, no lead-based paint addendum needed",
     drop(base("TX-3002", "2711 Maple Terrace, Arlington, TX 76015", ["Elena Ruiz"], ["Chris Dunn"], 287000, 1978), "Lead-Based Paint Addendum"),
     "clear", [], "The rule covers homes built before 1978. Must not over-flag.")
f = base("TX-3003", "4502 Juniper Hill Rd, Austin, TX 78731", ["Kai Nakamura"], ["Laura Bishop"], 870000, 1975)
f = drop(f, "Lead-Based Paint Addendum"); f["cover_sheet"]["year_built"] = 1985
case("T3", "Cover sheet says 1985, tax record says 1975, no lead paint addendum", f, "hold",
     ["YEAR_BUILT_MISMATCH", "MISSING_LBP_ADDENDUM"], "Only the tax record shows the home is pre-1978.")
f = base("TX-3004", "1180 Sycamore Bend, Cedar Park, TX 78613", ["Joy Adams"], ["Peter Holm"], 455000, 2006, hoa=True)
doc(f, "HOA Addendum")["address"] = "1108 Sycamore Bend, Cedar Park, TX 78613"
case("T3", "HOA addendum uploaded from another file (1108 vs 1180)", f, "hold",
     ["WRONG_TRANSACTION_DOC", "MISSING_HOA_ADDENDUM"], "The only HOA addendum belongs to a different address.")
f = drop(drop(base("TX-3005", "7340 Stonewall Pass, Frisco, TX 75036", ["Will Chen"], ["Ana Ferreira"], 689000, 2015, financing="VA", hoa=True),
              "Third Party Financing Addendum"), "HOA Addendum")
case("T3", "VA loan and HOA, both addenda missing", f, "hold", ["MISSING_TPF_ADDENDUM", "MISSING_HOA_ADDENDUM"],
     "Two issues in one note.")
f = base("TX-3006", "2219 Brazos View Dr, Bryan, TX 77803", ["Grace Lee"], ["Tom Becker"], 305000, 1990)
f["cover_sheet"]["address"] = "2291 Brazos View Dr, Bryan, TX 77803"
for d in f["documents"]: d["address"] = "2291 Brazos View Dr, Bryan, TX 77803"
case("T3", "Street number transposed on every document vs tax record", f, "hold", ["PROPERTY_MISMATCH"],
     "File is internally consistent but does not match the county record.")

# T4: escalate to the broker, never an automatic note (5)
f = base("TX-4001", "88 Live Oak Cir, Boerne, TX 78006", ["Nora Field"], ["James Ward"], 615000, 2001)
f["tax_record"]["owner"] = "Ward Family Trust"
case("T4", "Seller is not the owner of record", f, "escalate", ["SELLER_NOT_OWNER"],
     "Possible trust or title problem; a broker decides what is needed.")
f = base("TX-4002", "3301 Rio Grande St, Austin, TX 78705", ["Ethan Cole"], ["Maya Singh"], 540000, 1997, status="closed")
doc(f, "Closing Statement")["price"] = 532000
case("T4", "Closing statement price differs from cover sheet", f, "escalate", ["CLOSING_PRICE_MISMATCH"],
     "Commission is calculated from price; payout must not run on the wrong number.")
f = base("TX-4003", "509 Magnolia Pl, The Woodlands, TX 77380", ["Ivy Brooks"], ["Hugo Martin"], 720000, 2009, status="closed")
doc(f, "Closing Statement")["close_date"] = "2026-11-10"
case("T4", "Closing statement date differs from cover sheet", f, "escalate", ["CLOSING_DATE_MISMATCH"],
     "Close date drives review priority and the 8-day upload window.")
f = base("TX-4004", "1600 Vista Ridge Dr, El Paso, TX 79912", ["Ruben Soto"], ["Clare Young"], 398000, 2012)
doc(f, "Earnest Money Receipt")["date"] = "2026-10-12"
case("T4", "Earnest money receipted 6 days after the Effective Date", f, "escalate", ["EM_LATE"],
     "TREC 20-18 paragraph 5 gives 3 days; a late deposit can put the buyer in default, which is a broker call.")
f = base("TX-4005", "422 Oakmont Dr, Tyler, TX 75701", ["Dev Patel"], ["Marion Fisk"], 268000, 1969)
doc(f, "Lead-Based Paint Addendum")["date"] = "2026-10-14"
case("T4", "Lead-based paint addendum signed after the contract", f, "escalate", ["LBP_AFTER_CONTRACT"],
     "Federal rule requires the disclosure before the buyer is obligated; uploading a form cannot fix this.")

assert len(cases) == 25, len(cases)
json.dump(cases, open("data/cases.json", "w"), indent=1)
from collections import Counter; print(Counter(c["tier"] for c in cases), Counter(c["expected"]["decision"] for c in cases))
