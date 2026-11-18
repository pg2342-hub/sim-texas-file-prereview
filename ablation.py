"""Switches off one check at a time and reruns the eval, to show which cases test which check.
An eval set that still passes with a check switched off is not testing that check."""
import json, os
from run_eval import evaluate, gate, HERE
CHECKS = ["wrong_file", "tax_match", "iabs", "signatures", "financing", "hoa", "lead_paint",
          "seller_disclosure", "authority", "earnest_money", "termination", "closing"]
cases = json.load(open(os.path.join(HERE, "data", "cases.json")))
lines = ["# Ablation: one check switched off at a time (local agent)", "",
         "| Check switched off | Cases passed | Cases with a critical error | Cases that caught it |", "|---|---|---|---|"]
for ch in CHECKS:
    rows = evaluate("local", cases, 1, transform=lambda f, ch=ch: {**f, "test_options": {"disabled_checks": [ch]}})
    g = gate(rows); failed = [str(r["id"]) for r in rows if not r["pass"]]
    lines.append(f"| {ch} | {g['passed']} of 25 | {g['critical']} | {', '.join(failed)} |")
open(os.path.join(HERE, "reports", "ablation.md"), "w").write("\n".join(lines) + "\n")
print("\n".join(lines))
