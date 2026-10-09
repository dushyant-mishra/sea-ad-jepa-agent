#!/usr/bin/env python3
"""Render the V77 independent-evidence matrix JSON as Markdown. The JSON is the record; the Markdown
is derived from it and the V77 suite checks that the committed rendering matches.

Usage: python render_v77_evidence_matrix.py MATRIX.json OUT.md
"""
from __future__ import annotations

import json
import sys

NL = chr(10)


def _cell(x) -> str:
    return str(x).replace("|", "/").replace(NL, " ")


def _table(header, rows) -> list[str]:
    out = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    out += ["| " + " | ".join(_cell(c) for c in r) + " |" for r in rows]
    return out


def render(m: dict) -> str:
    L = [f"# {m['title']}", "", f"**Status:** {m['status']}", "", f"**Scope:** {m['scope']}", "",
         f"**Query:** {m['query_definition']}", "", "## The constraint that decides most rows", ""]
    for p in m["principles"]:
        L += [f"- **{p['id']}.** {p['text']}"]
    L += ["", "## Twin catalogue", ""]
    L += _table(["Twin", "Lineage", "Definition", "Status"],
                [[t["id"], t["lineage"], t["definition"], t["status"]] for t in m["twin_catalogue"]])
    L += ["", "## Classification rule", "", f"Declared {m['classification_rule']['declared']}.", ""]
    L += [f"{i}. {s}" for i, s in enumerate(m["classification_rule"]["order"], 1)]
    L += ["", f"`class_if_qualified`: {m['classification_rule']['class_if_qualified']}.", "",
          "## Summary", ""]
    L += _table(["Row", "Evidence object", "Query matching", "Lineage twins it can break", "Strongest twin remaining",
                 "Class now", "Class if qualified"],
                [[r["id"], r["name"], r["query_matching"],
                  ", ".join(t for t in r["c6_twins_it_can_falsify"]["twins"] if t in m["lineage_twins"]) or "none",
                  r["c7_stronger_twin_remaining"], r["c10_classification"], r["class_if_qualified"]]
                 for r in m["rows"]])
    L += ["", "## Rows in full", ""]
    for r in m["rows"]:
        L += [f"### {r['id']}. {r['name']}", "", f"Candidate {r['candidate']}; query matching {r['query_matching']}.", ""]
        L += [f"1. **Quantity measured.** {r['c1_quantity_measured']}",
              f"2. **Physically independent of the query RNA?** {r['c2_physically_independent_of_query_rna']['verdict']}: "
              f"{r['c2_physically_independent_of_query_rna']['why']}",
              f"3. **Construction independence.** {r['c3_construction_independence']['verdict']}: "
              f"{r['c3_construction_independence']['why']}",
              f"4. **Biological specificity.** {r['c4_biological_specificity']}",
              f"5. **Nuisance that can mimic it.** {r['c5_nuisance_that_can_mimic']}",
              f"6. **Twins it can falsify.** {', '.join(r['c6_twins_it_can_falsify']['twins']) or 'none'}: "
              f"{r['c6_twins_it_can_falsify']['condition']}",
              f"7. **Stronger twin remaining.** {r['c7_stronger_twin_remaining']}",
              "8. **Provenance and ETL already in the project.**"]
        L += [f"   - {p}" for p in r["c8_provenance_and_etl_in_project"]]
        L += ["9. **Missing controls blocking use.**"]
        L += [f"   - {c}" for c in r["c9_missing_controls_blocking_use"]]
        L += [f"10. **Classification now:** `{r['c10_classification']}`; if qualified: `{r['class_if_qualified']}`.", ""]
    L += ["## Older statements this narrows (marked, not rewritten)", ""]
    L += _table(["Where", "Statement", "Narrowed to"],
                [[s["where"], s["statement"], s["narrowed_to"]] for s in m["supersedes"]])
    L += ["", "## What this does not do", ""] + [f"- {x}" for x in m["does_not"]] + [""]
    return NL.join(L)


def main() -> None:
    m = json.loads(open(sys.argv[1], encoding="utf-8").read())
    with open(sys.argv[2], "w", encoding="utf-8", newline=NL) as fh:
        fh.write(render(m))
    print("rendered", sys.argv[2], "|", len(m["rows"]), "rows")


if __name__ == "__main__":
    main()
