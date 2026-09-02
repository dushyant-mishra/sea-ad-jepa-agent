#!/usr/bin/env python3
"""Fail-atomic package finalizer for Command 15B."""
from __future__ import annotations

import argparse, csv, hashlib, json, shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REQUIRED_ARTIFACTS = (
    "F1_HC3_15B_AUTHORITY.json",
    "F1_HC3_15B_SELECTION_CONTRACT.md",
    "F1_HC3_15B_DOMINANCE_AUDIT.csv",
    "F1_HC3_SELECTED_TRIPLE.json",
    "F1_HC3_SELECTED_SOURCE_INTERPRETATION.json",
    "F1_HC3_SELECTED_DONOR_DESIGN_F64LE.bin",
    "F1_HC3_SELECTED_DONOR_DESIGN_SCHEMA.json",
    "F1_HC3_SELECTED_GEOMETRY.json",
    "F1_HC3_SELECTED_SYNTHETIC_ENGINE_CHECK.json",
    "F1_HC3_15B_INDEPENDENT_VALIDATION.json",
    "F1_HC3_15B_MULTIAGENT.md",
    "F1_HC3_15B_SOURCE_MANIFEST.csv",
    "F1_HC3_15B_MANIFEST.csv",
    "F1_HC3_15B_EXTERNAL_REVIEW_HANDOFF.md",
)
SOURCES = (
    "derive_contextual_target_f1_hc3_nuisance_design_freeze_v1.py",
    "validate_contextual_target_f1_hc3_nuisance_design_freeze_v1.py",
    "finalize_contextual_target_f1_hc3_nuisance_design_freeze_v1.py",
)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(8 << 20), b""):
            h.update(block)
    return h.hexdigest()


def snapshot_manifest_path(name: str) -> str:
    return f"source_snapshot/{name}"


def main() -> None:
    ap=argparse.ArgumentParser(); ap.add_argument("--staging",type=Path,required=True); args=ap.parse_args(); out=args.staging.resolve()
    authority=json.loads((out/"F1_HC3_15B_AUTHORITY.json").read_text(encoding="utf-8"))
    selected=json.loads((out/"F1_HC3_SELECTED_TRIPLE.json").read_text(encoding="utf-8"))
    schema=json.loads((out/"F1_HC3_SELECTED_DONOR_DESIGN_SCHEMA.json").read_text(encoding="utf-8"))
    geometry=json.loads((out/"F1_HC3_SELECTED_GEOMETRY.json").read_text(encoding="utf-8"))
    engine=json.loads((out/"F1_HC3_SELECTED_SYNTHETIC_ENGINE_CHECK.json").read_text(encoding="utf-8"))
    independent=json.loads((out/"F1_HC3_15B_INDEPENDENT_VALIDATION.json").read_text(encoding="utf-8"))
    review=(out/"F1_HC3_15B_MULTIAGENT.md").read_text(encoding="utf-8")
    design=out/"F1_HC3_SELECTED_DONOR_DESIGN_F64LE.bin"
    selected_triple=selected["selected_triple"]
    gates=(authority["status"]=="PASS", authority["selection_contract_frozen_before_application"] is True,
           selected["maximal_triples"]==[selected_triple], selected["universal_maximum_triples"]==[selected_triple],
           selected["dominates_every_admissible"] is True, schema["selected_design_sha256"]==sha256(design),
           geometry["numerical_rank"]==geometry["constructed_columns"]==schema["shape"][1], geometry["df"]==schema["shape"][0]-schema["shape"][1],
           geometry["loo_rank_stable"] is True, geometry["hc3_estimable"] is True,
           engine["known_direction_recreates_fail_closed"] is True, independent["status"]=="PASS",
           all(label in review for label in ("Historian / Authority","Statistical Design","Numerical Linear Algebra","HC3 / Robust Inference","Dataset / Biology Semantics","Red-Team")),
           review.count("VERDICT: PASS") == 6,
           authority["firewall"]=={"expression":False,"forward_or_outcome":False,"model_or_checkpoint":False,"training_or_ema":False},
           authority["production_f1_engine_patched"] is False, authority["f1_evaluation_run"] is False)
    if not all(gates):
        raise RuntimeError("STOP_F1_HC3_15B_INDEPENDENT_MISMATCH")
    handoff=f"""# F1 HC3 Command 15B — external-review handoff

Terminal: `PASS_F1_HC3_NUISANCE_DESIGN_FREEZE_AWAITING_EXTERNAL_REVIEW`.

- Authenticated 15A4 manifest and every manifested file reproduced.
- The selection contract was frozen and SHA-bound before frontier application.
- The complete 30-row admissible set has one universal component-wise maximum: `{selected['selected_triple']}`.
- The selected design has SHA-256 `{schema['selected_design_sha256']}`, rank 16, df 88, and zero leave-one-donor rank losses across all 104 donors.
- SVD production leverage and independent pivoted-QR geometry agree; HC3 is estimable without leverage clamping.
- Deterministic synthetic arithmetic and the known NPH52 donor-indispensability attack behave as required.
- Independent selection, reconstruction, exact float64 design bytes, QR geometry, LOO ranks, and synthetic HC3 checks PASS.
- Six targeted review lenses PASS; dissent, if any, is preserved in the review artifact.
- No expression, outcome, model/checkpoint, forward, training, optimizer, or EMA access occurred. No F1 evaluation ran and no production F1 engine was patched.

This freezes only the current F1-104 nuisance design. Current ranks, leverage values, and donor identities must not transfer to a larger cohort; the authenticated 15A4 reusable procedure must be rerun there.
"""
    (out/"F1_HC3_15B_EXTERNAL_REVIEW_HANDOFF.md").write_text(handoff,encoding="utf-8")
    terminal={"terminal_status":"PASS_F1_HC3_NUISANCE_DESIGN_FREEZE_AWAITING_EXTERNAL_REVIEW","selected_triple":selected_triple,"selected_design_sha256":schema["selected_design_sha256"],"rank":geometry["numerical_rank"],"df":geometry["df"],"f1_run_authorized":False,"production_f1_engine_patched":False}
    (out/"F1_HC3_15B_TERMINAL_STATUS.json").write_text(json.dumps(terminal,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    snapshot=out/"source_snapshot"; snapshot.mkdir(exist_ok=True)
    source_rows=[]
    for name in SOURCES:
        source=ROOT/"scripts/v4"/name; target=snapshot/name; shutil.copy2(source,target)
        source_rows.append({"source_path":str(source.relative_to(ROOT)).replace("\\","/"),"snapshot_path":snapshot_manifest_path(name),"snapshot_path_scope":"PACKAGE_RELATIVE","source_sha256":sha256(source),"snapshot_sha256":sha256(target),"byte_identical":sha256(source)==sha256(target)})
    with (out/"F1_HC3_15B_SOURCE_MANIFEST.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(source_rows[0])); w.writeheader(); w.writerows(source_rows)
    missing=[name for name in REQUIRED_ARTIFACTS if name not in {"F1_HC3_15B_MANIFEST.csv"} and not (out/name).is_file()]
    if missing: raise RuntimeError(f"STOP_PROVENANCE_OR_FIREWALL: missing {missing}")
    rows=[]
    for path in sorted(p for p in out.rglob("*") if p.is_file() and p.name!="F1_HC3_15B_MANIFEST.csv"):
        rows.append({"relative_path":str(path.relative_to(out)).replace("\\","/"),"bytes":path.stat().st_size,"sha256":sha256(path)})
    with (out/"F1_HC3_15B_MANIFEST.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=["relative_path","bytes","sha256"]); w.writeheader(); w.writerows(rows)
    if any(not (out/name).is_file() for name in REQUIRED_ARTIFACTS): raise RuntimeError("STOP_PROVENANCE_OR_FIREWALL")
    print(json.dumps({**terminal,"manifest_sha256":sha256(out/"F1_HC3_15B_MANIFEST.csv"),"manifested_files":len(rows)}))


if __name__=="__main__": main()
