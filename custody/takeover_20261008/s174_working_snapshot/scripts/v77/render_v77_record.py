#!/usr/bin/env python3
"""Generic, deterministic Markdown rendering of a V77 JSON record (pre-registrations, handoffs).
The JSON is the record; the V77 suite checks that each committed rendering matches.

Usage: python render_v77_record.py RECORD.json OUT.md
"""
from __future__ import annotations

import json
import sys

NL = chr(10)


def _fmt(x) -> str:
    if isinstance(x, list):
        return "; ".join(_fmt(i) for i in x)
    if isinstance(x, dict):
        return json.dumps(x, ensure_ascii=False, separators=(", ", ": "))
    return str(x).replace("|", "/").replace(NL, " ")


def _block(key: str, v, level: int) -> list[str]:
    h = "#" * min(level, 6)
    if not isinstance(v, (list, dict)):
        return [f"**{key}:** {v}", ""]
    out = [f"{h} {key}", ""]
    if isinstance(v, dict):
        for k, vv in v.items():
            out += _block(k, vv, level + 1)
        return out
    if v and all(isinstance(i, dict) for i in v):
        cols: list[str] = []
        for i in v:
            cols += [c for c in i if c not in cols]
        out += ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
        out += ["| " + " | ".join(_fmt(i.get(c, "")) for c in cols) + " |" for i in v]
        return out + [""]
    return out + [f"- {_fmt(i)}" for i in v] + [""]


def render(rec: dict) -> str:
    L = [f"# {rec.get('title', rec.get('schema', 'record'))}", ""]
    for k, v in rec.items():
        if k != "title":
            L += _block(k, v, 2)
    return NL.join(L)


def main() -> None:
    rec = json.loads(open(sys.argv[1], encoding="utf-8").read())
    with open(sys.argv[2], "w", encoding="utf-8", newline=NL) as fh:
        fh.write(render(rec))
    print("rendered", sys.argv[2])


if __name__ == "__main__":
    main()
