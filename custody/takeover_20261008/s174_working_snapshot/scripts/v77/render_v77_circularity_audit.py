#!/usr/bin/env python3
"""Render the V77 regulatory circularity audit JSON as Markdown. The JSON is the record; the V77
suite checks that the committed rendering matches.

Usage: python render_v77_circularity_audit.py AUDIT.json OUT.md
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


def render(a: dict) -> str:
    L = [f"# {a['title']}", "", f"**Status:** {a['status']}", "", f"**Question:** {a['question']}", "",
         f"**Answer:** {a['summary']}", "", "## Circularity classes", ""]
    L += _table(["Class", "Meaning"], [[c["id"], c["meaning"]] for c in a["circularity_classes"]])
    L += ["", a["selection_flag"], "", "## Where the query RNA enters a SCENIC+-style pipeline", ""]
    L += _table(["Step", "Query RNA", "Consequence"], [[p["step"], p["query_rna"], p["consequence"]] for p in a["pipeline"]])
    L += ["", "## The three settings", ""]
    for s in a["settings"]:
        L += [f"### {s['id']}: {s['setting']}", "",
              f"- **Circularity class:** `{s['circularity_class']}`; verdict `{s['verdict']}`; matrix rows "
              f"{', '.join(s['matrix_rows'])}.",
              f"- **Can it tell regulation from a capture process producing the same RNA covariance?** {s['can_distinguish']}",
              f"- **Twins it can break:** {', '.join(s['twins_broken']) or 'none'}. **Twins it absorbs or passes:** "
              f"{', '.join(s['twins_absorbed']) or 'none'}.", ""]
    L += ["## Not only ATAC", ""]
    L += _table(["Evidence", "Circularity class", "Selection-coupled", "Matrix row", "Note"],
                [[e["evidence"], e["circularity_class"], "yes" if e["selection_coupled"] else "no", e["matrix_row"],
                  e.get("note", "")] for e in a["not_only_atac"]])
    L += ["", "## Project evidence folded in", ""]
    L += _table(["Evidence", "Where", "Status", "Bearing on circularity"],
                [[e["evidence"], e["where"], e["status"], e["bearing"]] for e in a["project_evidence"]])
    L += ["", "## What any use of SCENIC+ as discriminating evidence would require (not a decision)", ""]
    L += [f"- {r}" for r in a["requirements_if_used"]]
    L += ["", "## What this does not do", ""] + [f"- {x}" for x in a["does_not"]] + [""]
    return NL.join(L)


def main() -> None:
    a = json.loads(open(sys.argv[1], encoding="utf-8").read())
    with open(sys.argv[2], "w", encoding="utf-8", newline=NL) as fh:
        fh.write(render(a))
    print("rendered", sys.argv[2], "|", len(a["settings"]), "settings")


if __name__ == "__main__":
    main()
