#!/usr/bin/env python3
"""Read-only, fail-closed reproduction of the frozen T1 u0/u205 evaluation."""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch

ROOT = Path(__file__).resolve().parents[2]
T1_ROOT = ROOT / "exports" / "prod41k_teacher_t1_20260823"
T1_RUN = T1_ROOT / "t1_run"
OUT = ROOT / "exports" / "prod41k_t1_contextual_recovery_v1"
STAGING = OUT / "_staging_original_reproduction"
sys.path.insert(0, str(ROOT / "scripts" / "v4"))
sys.path.insert(0, str(ROOT / "exports" / "static_context_decomposition_v4_20260821"))

import stage81a3_prod41k_teacher_t1 as t1  # noqa: E402
from production_train_loader import ProductionTrainLoader  # noqa: E402


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_checkpoint(update: int, device: torch.device):
    manifest = json.loads((T1_RUN / "checkpoint_manifest.json").read_text())
    row = next((x for x in manifest["checkpoints"] if int(x["update"]) == update), None)
    if row is None:
        raise RuntimeError(f"authenticated checkpoint u{update} absent")
    path = ROOT / row["path"]
    if path.stat().st_size != int(row["bytes"]) or sha256(path) != row["sha256"]:
        raise RuntimeError(f"checkpoint u{update} identity mismatch")
    state = torch.load(path, map_location=device, weights_only=False)
    components = t1.phase_e.build_components(t1.SEED, device)
    online, target = components[:2]
    online.load_state_dict(state["online_encoder"])
    target.load_state_dict(state["target_encoder"])
    online.eval(); target.eval()
    return online, target, path, row


def compare_csv(original: Path, reproduced: Path, update: int) -> dict:
    a = pd.read_csv(original)
    b = pd.read_csv(reproduced)
    if list(a.columns) != list(b.columns) or a.shape != b.shape:
        raise RuntimeError(f"serialization schema/shape mismatch: {original.name}")
    text_columns = [c for c in a if not (pd.api.types.is_numeric_dtype(a[c]) and pd.api.types.is_numeric_dtype(b[c]))]
    for column in text_columns:
        if not a[column].fillna("<NA>").astype(str).equals(b[column].fillna("<NA>").astype(str)):
            raise RuntimeError(f"text mismatch: {original.name}:{column}")
    maximum = 0.0
    for column in [c for c in a if c not in text_columns]:
        av = pd.to_numeric(a[column], errors="coerce").to_numpy(float)
        bv = pd.to_numeric(b[column], errors="coerce").to_numpy(float)
        if not np.array_equal(np.isnan(av), np.isnan(bv)):
            raise RuntimeError(f"NA mismatch: {original.name}:{column}")
        if np.any(np.isfinite(av)):
            maximum = max(maximum, float(np.max(np.abs(av[np.isfinite(av)] - bv[np.isfinite(av)]))))
    # Frozen evaluation serialization is the authority: require exact parsed values.
    if maximum != 0.0:
        raise RuntimeError(f"exact frozen-value reproduction failed: {original.name} max_abs={maximum}")
    return {
        "update": update, "artifact": original.name, "rows": len(a),
        "columns": len(a.columns), "max_abs_numeric_difference": maximum,
        "exact_parsed_match": True, "original_sha256": sha256(original),
        "reproduced_sha256": sha256(reproduced),
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    if STAGING.exists():
        shutil.rmtree(STAGING)
    STAGING.mkdir()
    contract = t1.validate_contract()
    manifest = json.loads((T1_RUN / "checkpoint_manifest.json").read_text())
    if manifest["contract_sha256"] != sha256(T1_ROOT / "T1_BIOLOGY_EVALUATION_FREEZE.json"):
        raise RuntimeError("checkpoint manifest/contract hash mismatch")
    u0_path = T1_RUN / "u0_evaluation_features.npz"
    if sha256(u0_path) != manifest["u0_features_sha256"]:
        raise RuntimeError("u0 feature hash mismatch")
    with np.load(u0_path, allow_pickle=False) as packed:
        u0 = {key: packed[key] for key in ("rich_H", "rich_CELL", "partial_H", "partial_CELL")}
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if device.type != "cuda":
        raise RuntimeError("exact frozen T1 reproduction requires the qualified CUDA path")
    loader = ProductionTrainLoader()
    evaluation = t1.load_evaluation(loader)
    original_run = t1.RUN
    rows = []
    checkpoint_rows = []
    try:
        t1.RUN = STAGING
        for update in (0, 205):
            online, target, checkpoint_path, checkpoint_row = load_checkpoint(update, device)
            before_online = sha256(checkpoint_path)
            _, summary = t1.evaluate_checkpoint_rng_neutral(update, online, target, evaluation, u0, device)
            if sha256(checkpoint_path) != before_online:
                raise RuntimeError("read-only checkpoint changed during evaluation")
            checkpoint_rows.append({"update": update, "checkpoint": str(checkpoint_path.relative_to(ROOT)), "sha256": before_online, "summary": summary})
            for stem in ("t1_biology_metrics", "t1_source_operator_metrics", "t1_address_reader_metrics"):
                name = f"{stem}_u{update:04d}.csv"
                rows.append(compare_csv(T1_RUN / name, STAGING / name, update))
    finally:
        t1.RUN = original_run
    frame = pd.DataFrame(rows)
    frame.to_csv(OUT / "T1_RECOVERY_ORIGINAL_REPRODUCTION.csv", index=False, lineterminator="\n")
    exact = bool(frame["exact_parsed_match"].all())
    md = [
        "# T1 original-evidence reproduction",
        "",
        f"Verdict: **{'PASS' if exact else 'STOP'}**",
        "",
        "The authenticated u0 and u205 checkpoints were evaluated through the frozen T1 evaluator on the exact frozen cohort, masks, labels, donor roles, controls, donor shuffle, and molecular-reader dependencies. No encoder, predictor, optimizer, or EMA update was performed.",
        "",
        f"- contract SHA-256: `{sha256(T1_ROOT / 'T1_BIOLOGY_EVALUATION_FREEZE.json')}`",
        f"- u0 feature SHA-256: `{sha256(u0_path)}`",
        f"- evaluation device: `{device}`",
        f"- all six frozen CSV comparisons exact after parsing: `{exact}`",
        f"- maximum numeric difference: `{frame.max_abs_numeric_difference.max():.1f}`",
        "",
        "Recovery decomposition is authorized to proceed only because this reproduction passed exactly.",
    ]
    (OUT / "T1_RECOVERY_ORIGINAL_REPRODUCTION.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    (STAGING / "REPRODUCTION_AUDIT.json").write_text(json.dumps({"contract_status": contract["status"], "checkpoints": checkpoint_rows, "comparisons": rows}, indent=2, default=str) + "\n")
    print(frame.to_string(index=False))


if __name__ == "__main__":
    main()
