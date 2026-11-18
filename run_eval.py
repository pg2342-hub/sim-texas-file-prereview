"""Scores the Texas file pre-review workflow on the 25-case eval set and applies the go-live gate.

  python3 run_eval.py --agent sim --url http://localhost:3000 --workflow-id <id> --api-key <key> --runs 3
  python3 run_eval.py --agent local --runs 3          # same Function block code, run in Node outside Sim
  python3 run_eval.py --agent checklist_only          # baseline: a fixed checklist, no conditional rules
"""
import argparse, json, os, subprocess, sys, urllib.request
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
WORKFLOW = os.path.join(HERE, "workflow", "texas_file_prereview.json")
OUTCOME = {"ready_for_broker_review": "clear", "compliance_hold": "hold", "escalate_to_broker": "escalate"}

def run_sim(file, a):
    req = urllib.request.Request(f"{a.url}/api/workflows/{a.workflow_id}/execute",
                                 data=json.dumps({"file": file, "draft_note": False}).encode(),
                                 headers={"Content-Type": "application/json", "X-API-Key": a.api_key})
    out = json.load(urllib.request.urlopen(req, timeout=120))
    return {"decision": OUTCOME[out["outcome"]], "codes": sorted(i["code"] for i in out["issues"])}

def run_local(file, a=None):
    p = subprocess.run(["node", os.path.join(HERE, "harness", "run_local.js"), WORKFLOW],
                       input=json.dumps(file), capture_output=True, text=True, check=True)
    out = json.loads(p.stdout)
    return {"decision": out["decision"], "codes": sorted(i["code"] for i in out["issues"])}

def run_checklist_only(file, a=None):
    """A static checklist: the same four documents on every file, plus a closing statement once closed."""
    have = {d["type"] for d in file["documents"]}
    need = {"IABS": "MISSING_IABS", "Resale Contract": "MISSING_CONTRACT",
            "Seller's Disclosure Notice": "MISSING_SELLER_DISCLOSURE", "Earnest Money Receipt": "MISSING_EM_RECEIPT"}
    if file["cover_sheet"]["status"] == "closed":
        need["Closing Statement"] = "MISSING_CLOSING_STATEMENT"
    codes = sorted(c for t, c in need.items() if t not in have)
    return {"decision": "hold" if codes else "clear", "codes": codes}

AGENTS = {"sim": run_sim, "local": run_local, "checklist_only": run_checklist_only}

def grade(case, got):
    exp = case["expected"]
    errors = []
    if got["decision"] != exp["decision"]:
        errors.append(f"decision {got['decision']} (expected {exp['decision']})")
    if got["codes"] != exp["codes"]:
        missed = sorted(set(exp["codes"]) - set(got["codes"])); extra = sorted(set(got["codes"]) - set(exp["codes"]))
        if missed: errors.append("missed " + ", ".join(missed))
        if extra: errors.append("extra " + ", ".join(extra))
    # Critical: a file cleared that needed work, or a broker escalation that would go out as an automatic note
    critical = (got["decision"] == "clear" and exp["decision"] != "clear") or \
               (exp["decision"] == "escalate" and got["decision"] == "hold")
    return {"pass": not errors, "errors": errors, "critical": critical}

def evaluate(agent, cases, runs, a=None, transform=None):
    res = defaultdict(list)
    for r in range(runs):
        for c in cases:
            f = transform(c["file"]) if transform else c["file"]
            got = AGENTS[agent](f, a)
            res[c["id"]].append({**grade(c, got), "got": got})
    rows = []
    for c in cases:
        rr = res[c["id"]]
        rows.append({"id": c["id"], "tier": c["tier"], "title": c["title"], "pass": all(x["pass"] for x in rr),
                     "critical": any(x["critical"] for x in rr),
                     "errors": sorted({e for x in rr for e in x["errors"]}), "got": rr[-1]["got"]})
    return rows

def gate(rows):
    n = sum(r["pass"] for r in rows); crit = sum(r["critical"] for r in rows)
    t4 = [r for r in rows if r["tier"] == "T4"]; t4p = sum(r["pass"] for r in t4)
    ok = n >= 24 and crit == 0 and t4p == len(t4)
    return {"passed": n, "total": len(rows), "critical": crit, "t4": f"{t4p} of {len(t4)}", "gate": "Pass" if ok else "Fail"}

def report(agent, rows, g, runs):
    tiers = defaultdict(lambda: [0, 0])
    for r in rows: tiers[r["tier"]][0] += r["pass"]; tiers[r["tier"]][1] += 1
    lines = [f"# Eval report: {agent} agent, {runs} run(s) per case", "",
             f"Cases passed on every run: {g['passed']} of {g['total']}. Cases with a critical error: {g['critical']}. "
             f"T4 escalations: {g['t4']}. Gate (24 of 25 on all runs, zero critical errors, T4 5 of 5): **{g['gate']}**.", "",
             "| Tier | Passed |", "|---|---|"] + [f"| {t} | {p} of {n} |" for t, (p, n) in sorted(tiers.items())] + \
            ["", "| # | Tier | Case | Result | Errors |", "|---|---|---|---|---|"] + \
            [f"| {r['id']} | {r['tier']} | {r['title']} | {'pass' if r['pass'] else ('FAIL, critical' if r['critical'] else 'FAIL')} | {'; '.join(r['errors'])} |" for r in rows]
    return "\n".join(lines) + "\n"

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--agent", choices=AGENTS, default="local"); ap.add_argument("--runs", type=int, default=1)
    ap.add_argument("--url", default="http://localhost:3000"); ap.add_argument("--workflow-id"); ap.add_argument("--api-key")
    a = ap.parse_args()
    cases = json.load(open(os.path.join(HERE, "data", "cases.json")))
    rows = evaluate(a.agent, cases, a.runs, a); g = gate(rows)
    os.makedirs(os.path.join(HERE, "reports"), exist_ok=True)
    open(os.path.join(HERE, "reports", f"{a.agent}_report.md"), "w").write(report(a.agent, rows, g, a.runs))
    json.dump({"gate": g, "rows": rows}, open(os.path.join(HERE, "reports", f"{a.agent}_results.json"), "w"), indent=1)
    print(json.dumps(g))
