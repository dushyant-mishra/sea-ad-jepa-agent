#!/usr/bin/env python3
"""Historical spillover audit for the V77 lane, run before every bounded phase.

Ten checks. Three are structural and decide PASS or FAIL by themselves; seven are text checks that
flag CANDIDATE statements in V77-lane files for human review, because no pattern search can judge
meaning. A candidate is not a finding until reviewed; a clean text check is not proof of absence.

  structural   RAW_IDS_MODEL_VISIBLE        source/operator identity declared model-visible
               OLD_RUNTIME_CLASSES          runtime authority, guard or mutation names in V77 code
               ZERO_QUOTA_OPERATOR_LOSS     operators with zero cells where the source could cover them
  text         V47_V48_OVERWRITTEN          same-assay identifiability claimed as resolved
               V63_MISREPRESENTED           V63's modelled-nuisance success read as exact-twin resolution
               S149_POOLED_AS_TARGET        pooled real topology or envelopes used as a biological target
               S159_RECENTRED_AS_AUTHORITY  re-centred within-cohort intervals used as acceptance
               MORABITO_AS_VALIDATION       Morabito presented as freely available validation
               SCENIC_ATAC_CIRCULAR         SCENIC+ or ATAC presented as independent without a circularity caveat
               SEED7302_AS_CONFIRMATION     seed-7302 results called independent confirmation

Scope: scripts/v77, tests/v77, results/v77 and docs/agent/V77_*. Older lanes' history is read-only
and outside scope. Lines that carry a negation or supersession word are not flagged.

Every text candidate and every structural failure is dispositioned in <record>_DISPOSITIONS.json:
FALSE_POSITIVE with a reason, or FINDING_REPAIRED with a reason and the repair. An open finding
stops the phase, so it is never a committed disposition; the V77 suite refuses a committed record
that is not fully dispositioned.
"""
from __future__ import annotations

import argparse
import ast
import json
import re
import subprocess
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]

NEGATION = re.compile(r"\b(not|never|no|nothing|none|neither|nor|cannot|can't|withdrawn|superseded|retracted|invalid|non[-_ ]?identifiable|"
                      r"unresolved|forbidden|protected|excluded|refus\w*|circular|candidate|exploratory|without|"
                      r"unless|until|instead|rather than|only)\b", re.I)
TEXT_CHECKS = {
    "V47_V48_OVERWRITTEN": re.compile(r"(identifiab\w*\s+(is\s+)?(resolved|solved|established))|"
                                      r"(twin\s+(is\s+)?(separated|resolved|broken))|(solv\w+\s+identifiab)", re.I),
    "V63_MISREPRESENTED": re.compile(r"V63[^\n]{0,120}(exact[- ]twin)[^\n]{0,60}(resolv|solv|separat|pass)", re.I),
    "S149_POOLED_AS_TARGET": re.compile(r"pooled[^\n]{0,60}(biological target|calibration target|acceptance)", re.I),
    "S159_RECENTRED_AS_AUTHORITY": re.compile(r"(re-?cent(re|er)ed)[^\n]{0,60}(acceptance|authorit|pass/fail|decid)", re.I),
    "MORABITO_AS_VALIDATION": re.compile(r"(morabito|GSE174367)[^\n]{0,80}(validat|confirm|available|use)", re.I),
    "SCENIC_ATAC_CIRCULAR": re.compile(r"(scenic\+?|eregulon|atac)[^\n]{0,80}(independent|validat|confirm|truth)", re.I),
    "SEED7302_AS_CONFIRMATION": re.compile(r"(independent(ly)? confirm\w*|confirmatory)", re.I),
}
RUNTIME_NAMES = ("CurrentOptimizerStepGuard", "CurrentTrainingAuthority", "install_current_optimizer_guard",
                 "ProductionTrainLoader", "run_inactive_reference_update", "create_ema_target", "optimizer.step(",
                 "GradScaler(", "torch.save(")


def scope_files():
    pats = ["scripts/v77/*.py", "tests/v77/*.py", "results/v77/*.json", "docs/agent/V77_*"]
    out = []
    for p in pats:
        out += sorted(Path(ROOT).glob(p))
    return [f for f in out if f.name != Path(__file__).name]


def text_checks_lines(named_lines):
    hits = {k: [] for k in TEXT_CHECKS}
    for name, lines in named_lines:
        for i, line in enumerate(lines, 1):
            if NEGATION.search(line):
                continue
            for k, pat in TEXT_CHECKS.items():
                if pat.search(line):
                    hits[k].append(dict(file=name, line=i, text=line.strip()[:200]))
    return hits


def text_checks(files):
    named = []
    for f in files:
        try:
            named.append((str(f.relative_to(ROOT)).replace("\\", "/"),
                          f.read_text(encoding="utf-8", errors="replace").splitlines()))
        except OSError:
            continue
    return text_checks_lines(named)


def raw_ids_model_visible(src: str, bridge: str):
    """Structural: the adapter's model batch must not carry raw identity, and the bridge must never
    declare source or operator MODEL_VISIBLE."""
    problems = []
    tree = ast.parse(src)
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "SyntheticModelBatch":
            names = {n.target.id for n in node.body if isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name)}
            leaked = names & {"source_index", "operator_index", "donor_index", "global_cell_index"}
            if leaked:
                problems.append(f"SyntheticModelBatch carries {sorted(leaked)}")
    for m in re.finditer(r'F\("(source_index|operator_index|donor_id|global_cell_index)",\s*C\.(\w+)\)', bridge):
        if m.group(2) == "MODEL_VISIBLE":
            problems.append(f"bridge declares {m.group(1)} MODEL_VISIBLE")
    return dict(status="FAIL" if problems else "PASS", problems=problems)


def old_runtime_classes(sources: dict):
    problems = [f"{name}: {rn}" for name, txt in sorted(sources.items()) for rn in RUNTIME_NAMES if rn in txt]
    return dict(status="FAIL" if problems else "PASS", problems=problems)


def zero_quota_operator_loss(truth_dirs):
    out = []
    for d in truth_dirs:
        d = Path(d)
        tm = json.loads((d / "TRUTH_MANIFEST.json").read_text())
        op = np.concatenate([np.load(f)["operator_index"] for f in sorted(d.glob("TRUTH_*.npz"))]).astype(int)
        cnt = np.bincount(op, minlength=len(tm["operator_ids"]))
        fam = ["SEA_AD" if s.lower().replace("-", "_").startswith("sea_ad") else s for s in tm["operator_sources"]]
        lost = []
        for s in sorted(set(fam)):
            idx = [i for i, x in enumerate(fam) if x == s]
            cells = int(cnt[idx].sum())
            if cells >= len(idx):
                lost += [tm["operator_ids"][i] for i in idx if cnt[i] == 0]
        out.append(dict(truth=str(d), operators=len(cnt), operators_with_zero_cells=int((cnt == 0).sum()),
                        unexpected_operator_loss=lost))
    bad = any(o["unexpected_operator_loss"] for o in out)
    return dict(status="FAIL" if bad else "PASS", worlds=out)


DISPOSITIONS = ("FALSE_POSITIVE", "FINDING_REPAIRED")


def review_items(audit: dict):
    """Everything that needs a disposition: each text candidate and each failing structural check."""
    items = [(k, h["file"], h["line"]) for k, hits in audit["text_candidates"].items() for h in hits]
    items += [(k, "STRUCTURAL", 0) for k, v in audit["structural"].items() if v["status"] != "PASS"]
    return items


def disposition_gaps(audit: dict, disp: dict):
    """Review items without a lawful disposition. A structural failure must be FINDING_REPAIRED with
    the repair named."""
    have = {(d["check"], d["file"], d["line"]): d for d in disp.get("dispositions", [])}
    gaps = []
    for key in review_items(audit):
        d = have.get(key)
        if d is None or d.get("disposition") not in DISPOSITIONS or not d.get("reason"):
            gaps.append(key)
        elif (key[1] == "STRUCTURAL" or d["disposition"] == "FINDING_REPAIRED") and (
                d["disposition"] != "FINDING_REPAIRED" or not d.get("repair")):
            gaps.append(key)
    return gaps


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", required=True)
    ap.add_argument("--truth-dir", action="append", default=[], help="hidden_truth folders to check for operator loss")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    head = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=ROOT).stdout.strip()
    files = scope_files()
    rec = dict(
        schema="V77_HISTORICAL_SPILLOVER_AUDIT_V1", phase=a.phase, head=head, files_scanned=len(files),
        structural=dict(RAW_IDS_MODEL_VISIBLE=raw_ids_model_visible(
                            (HERE / "v77_synthetic_batch_adapter.py").read_text(encoding="utf-8"),
                            (HERE / "v77_qualification_bridge.py").read_text(encoding="utf-8")),
                        OLD_RUNTIME_CLASSES=old_runtime_classes(
                            {f.name: f.read_text(encoding="utf-8", errors="replace")
                             for f in sorted((ROOT / "scripts" / "v77").glob("*.py")) if f.name != Path(__file__).name}),
                        ZERO_QUOTA_OPERATOR_LOSS=zero_quota_operator_loss(a.truth_dir)),
        text_candidates=text_checks(files),
        reading=("structural checks decide PASS/FAIL; text candidates require review and carry dispositions in the "
                 "phase record; a clean text check is not proof of absence"))
    rec["structural_pass"] = all(v["status"] == "PASS" for v in rec["structural"].values())
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    with open(a.out, "w", newline="\n") as fh:
        fh.write(json.dumps(rec, indent=2) + "\n")
    print(json.dumps(dict(structural={k: v["status"] for k, v in rec["structural"].items()},
                          text_candidates={k: len(v) for k, v in rec["text_candidates"].items()}), indent=1))


if __name__ == "__main__":
    main()
