#!/usr/bin/env python3
"""Readiness test only: original V5 actor with verified PR547 synthetic FIT.

No optimizer, EMA, model fitting, controller truth, or C1-C6 PASS is performed.
Scientific or GPU training requires a separately reviewed successor.
"""
from __future__ import annotations

import argparse
from hashlib import sha1, sha256
import io
import json
import os
from pathlib import Path
import zipfile

import numpy as np

SCHEMA = "JEPA_SYNTH2048_V5_READINESS_U0_V1"
ROOT = Path(__file__).resolve().parents[2]
ZIP_SHA256 = "87fe3ec2038305c797c439cd9780036fe22cc22b647242749b1af0bfb444c06f"
MEMBER_SHA256 = {
    "teacher_measured.npz": "f38133844359017174e070fb5e4b5afc48334db86c80f17e99ef7b54014d6cc1",
    "student_qexcluded.npz": "a1fce3b79beb0d7632a0ffcdc9f28e94aadb4a594e9c76a8f6f6c48d1b99a0b5",
    "roster_evaluation_only.npz": "0427f1221f55e607cf32abb827db1be1026274b2acf3134f3a05e9f513a48c18",
    "atac_separate_nucleus_negative.npz": "26b35ab4e43ad3ee3e98c81d017b300dab2e70945a608e25154d9346ba2df321",
    "DEVELOPMENT_RECEIPT.json": "91310b3c3d86e28ce19a4090c624b53d4a6d0e31b5984dc9a8e159d08a4b1b0d",
}
SOURCE_SHA1 = {
    "src/sea_ad_jepa/v5/keyed_dropout_prototype_v2.py": "0fd06ae0891625924761ef097b20ba6e11495cb3",
    "src/sea_ad_jepa/v5/keyed_rng_contract_v2.py": "dcd4abf9790f25db1f576fbf821a75e13057a03e",
    "src/sea_ad_jepa/v5/data_first_geometry.py": "93b08f49f9d92b5c158e1a53fd5331b964f0e13f",
    "src/sea_ad_jepa/v5/inactive_update_reference.py": "ab266faa31ac7d3e51acf695a7deff1702368cde",
    "src/sea_ad_jepa/v5/inactive_guarded_update_v1.py": "59647eb0122dfd98068844f68b6d48c2c33d67ca",
    "src/sea_ad_jepa/v5/prefreeze_runtime_authority.py": "41a6ebde613ee3ec5c898fa39e5a212c14eaac66",
    "src/sea_ad_jepa/v5/ema_presentation_v1.py": "6f4442e25a6f891b9548b11403154233f616d842",
    "src/sea_ad_jepa/v5/ema_persisted_continuation_v2.py": "865f6991dd5822a37aa223604799eefcf0eddb9f",
    "src/sea_ad_jepa/v4/ipb_jepa.py": "3bd9d601a6779818a45c437cc21fd4a64749eb6e",
    "src/sea_ad_jepa/v4/gene_tokenizer.py": "0fd283136323a49b5554f2fb33d0c65ee31be576",
}
N_CELLS = 1440
N_ADDRESSES = 2048
Q = (1672, 1673, 1674, 1675)
FORBIDDEN_AUTHORITY = "TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED"


class PreflightRefusal(RuntimeError):
    pass


def insist(condition: bool, reason: str) -> None:
    if not bool(condition):
        raise PreflightRefusal("REFUSE_SYNTH2048_V5_INTEGRATION: " + reason)


def git_blob_sha1(raw: bytes) -> str:
    return sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def verify_v5_runtime_sources(root: Path = ROOT) -> dict[str, str]:
    """Refuse main's older unguarded runtime or any silently changed actor."""
    verified: dict[str, str] = {}
    for name, expected in SOURCE_SHA1.items():
        file = root / name
        insist(file.is_file() and not file.is_symlink(), "V5 source missing: " + name)
        current = git_blob_sha1(file.read_bytes())
        insist(current == expected, "V5 source identity changed: " + name)
        verified[name] = current
    return verified


def _npz(raw: bytes) -> dict[str, np.ndarray]:
    with np.load(io.BytesIO(raw), allow_pickle=False) as handle:
        result = {k: handle[k] for k in handle.files}
    insist(all(v.dtype.kind != "O" for v in result.values()), "unsafe object array")
    return result


def verified_fit(path: Path) -> tuple[dict, dict[str, np.ndarray], dict[str, np.ndarray]]:
    path = Path(path)
    insist(path.is_file() and not path.is_symlink(), "FIT archive missing or symlink")
    insist(path.stat().st_size <= 35_000_000, "FIT archive exceeds frozen bound")
    insist(sha256(path.read_bytes()).hexdigest() == ZIP_SHA256, "FIT archive SHA mismatch")
    with zipfile.ZipFile(path) as z:
        insist(set(z.namelist()) == set(MEMBER_SHA256) and len(z.namelist()) == len(MEMBER_SHA256),
               "FIT archive members changed")
        insist(all(not z.getinfo(k).is_dir() and z.getinfo(k).file_size < 100_000_000
                   for k in MEMBER_SHA256), "invalid or oversized FIT member")
        for name, expected in MEMBER_SHA256.items():
            insist(sha256(z.read(name)).hexdigest() == expected,
                   "FIT member SHA mismatch: " + name)
        receipt = json.loads(z.read("DEVELOPMENT_RECEIPT.json"))
        student = _npz(z.read("student_qexcluded.npz"))
        roster = _npz(z.read("roster_evaluation_only.npz"))
    insist(receipt.get("schema") == "JEPA_EXPANDED_COMMON_WORLD_DEVELOPMENT_FIT_ONLY_V1",
           "FIT version changed")
    insist(receipt.get("source_parent_pr328_exact_head") ==
           "25bbdbe18aa5ed3c8a39a7e4295bc36de1e328ec", "parent source changed")
    insist(receipt.get("frozen_dimensions") == {"cells": N_CELLS, "genes": N_ADDRESSES, "donors": 36},
           "FIT dimensions changed")
    insist(receipt.get("all_six_candidate_recoverability") == "UNASSESSED",
           "claimed scientific C outcome")
    for field in ("controller_truth_exported", "model_training_or_controller_scoring_executed",
                  "real_biology_or_production_authority"):
        insist(receipt.get(field) is False, "forbidden source authority: " + field)
    insist(set(student) == {"rna_base_counts", "rna_base_support",
                            "rna_base_address_ids", "projected_base_depth"},
           "student view gained other fields")
    insist(set(roster) == {"donor_id", "synthetic_source", "split", "rna_entity_id",
                           "atac_same_entity_id", "atac_separate_entity_id",
                           "perturbation_arm"}, "evaluation roster changed")
    return receipt, student, roster


def restore_full_address_space(
    student: dict[str, np.ndarray],
    *, query_ids: tuple[int, ...] = Q,
) -> tuple[np.ndarray, np.ndarray]:
    """Critical: preserve original 0..2047 gene IDs; never renumber 2044-column base."""
    count = student["rna_base_counts"]
    support = student["rna_base_support"]
    addr = student["rna_base_address_ids"]
    depth = student["projected_base_depth"]
    insist(type(query_ids) is tuple and query_ids == Q, "queries must be frozen")
    insist(count.shape == support.shape == (N_CELLS, N_ADDRESSES - len(Q)),
           "q-excluded measured arrays differ")
    insist(count.dtype == np.int32 and support.dtype == np.bool_, "count/support dtype drift")
    insist(addr.dtype == np.int32 and addr.shape == (N_ADDRESSES - len(Q),),
           "molecular address type/shape drift")
    insist(depth.dtype == np.int64 and depth.shape == (N_CELLS,), "projected depth drift")
    expected_ids = np.setdiff1d(np.arange(N_ADDRESSES), Q).astype(np.int32)
    insist(np.array_equal(addr, expected_ids), "address renumbered, aliased or duplicated")
    insist(not np.any(count < 0) and not np.any(count[~support]),
           "negative/unsupported observed count")
    insist(np.array_equal(depth, count.sum(axis=1, dtype=np.int64)),
           "whole-library depth or q descendant leaked")
    full = np.zeros((N_CELLS, N_ADDRESSES), dtype=np.int32)
    measurable = np.zeros((N_CELLS, N_ADDRESSES), dtype=np.bool_)
    full[:, addr] = count
    measurable[:, addr] = support
    insist(not np.any(full[:, Q]) and not np.any(measurable[:, Q]),
           "query truth became visible")
    insist(np.array_equal(full[:, expected_ids], count), "values changed on expand")
    insist(np.array_equal(measurable[:, expected_ids], support), "rights changed on expand")
    return full, measurable


def audit_fit(
    receipt: dict, student: dict[str, np.ndarray], roster: dict[str, np.ndarray],
) -> tuple[np.ndarray, np.ndarray, dict]:
    full, support = restore_full_address_space(student)
    roles = receipt["frozen_preoutcome_address_roles"]
    insist(roles.get("query_addresses") == list(Q), "frozen C3 q-ids changed")
    panels = roles.get("query_other8_panels")
    views = roles.get("relational_views_3x512")
    insist(isinstance(panels, list) and len(panels) == 4 and all(len(v) == 8 for v in panels),
           "C3 eight-other-gene panel mismatch")
    insist(isinstance(views, list) and len(views) == 3 and all(len(v) == 512 for v in views),
           "C2 3x512 view mismatch")
    all_roles = [int(x) for view in views + [list(Q)] + panels for x in view]
    insist(len(all_roles) == len(set(all_roles)), "C2/C3 measured addresses overlap")
    insist(all(bool(np.all(support[:, view])) for view in views + panels),
           "C2/C3 supposedly measured view lacks structural support")
    donor = roster["donor_id"]
    split = roster["split"]
    source = roster["synthetic_source"]
    insist(donor.shape == split.shape == source.shape == (N_CELLS,),
           "evaluation roster length mismatch")
    insist(donor.dtype == np.int32 and len(np.unique(donor)) == 36, "donor identity drift")
    insist(set(split.tolist()) == {"train", "val", "test"}, "split identities drift")
    insist(set(source.tolist()) == {"SYNTH_A", "SYNTH_B", "SYNTH_C"}, "source drift")
    for d in np.unique(donor):
        rows = donor == d
        insist(len(np.unique(split[rows])) == 1 and len(np.unique(source[rows])) == 1,
               "donor split or source leakage")
    report = {
        "schema": SCHEMA, "status": "DATA_AND_V5_SOURCE_VERIFIED__NO_OPTIMIZER",
        "original_dataset_sha256": ZIP_SHA256,
        "cells": N_CELLS, "vocabulary": N_ADDRESSES,
        "query_gene_ids": list(Q), "student_query_values_visible": False,
        "student_full_library_depth_visible": False, "gene_identity_restored_exactly": True,
        "relational_views_3x512": 3, "C2_relational_biology": "UNASSESSED",
        "C3_query_biology": "UNASSESSED",
        "all_C1_to_C6": "UNASSESSED",
        "train_donors": int(len(np.unique(donor[split == "train"]))),
        "val_donors": int(len(np.unique(donor[split == "val"]))),
        "test_donors": int(len(np.unique(donor[split == "test"]))),
        "actual_optimizer_updates": 0, "actual_ema_updates": 0,
        "learned_biology": "UNASSESSED", "gpu_kernel_qualified": False,
        "training_authorized": False, "execution_authorized": False,
        "production_target_authorized": False, "authority": FORBIDDEN_AUTHORITY,
    }
    return full, support, report


def run_zero_update_model_probe(full: np.ndarray, support: np.ndarray,
                                roster: dict[str, np.ndarray]) -> dict:
    """Full 2,048-position V5 six-block forward with original actor, zero updates."""
    import sys
    sys.path.insert(0, str(ROOT / "src"))
    import torch
    from sea_ad_jepa.v4.teacher_student_runtime import sample_uniform_target_blocks
    from sea_ad_jepa.v4.ipb_jepa import gather_block_states
    from sea_ad_jepa.v5.data_first_geometry import (
        pack_valid_tokens, weighted_block_jepa_loss,
    )
    from sea_ad_jepa.v5.inactive_update_reference import (
        _packed_teacher_blocks, build_reference_modules,
    )
    torch.set_num_threads(min(2, torch.get_num_threads()))
    # Frozen deterministic *mechanics selection* from TRAIN only, not scientific sampling.
    eligible = np.flatnonzero((roster["split"] == "train")
                              & (roster["synthetic_source"] == "SYNTH_A"))
    insist(len(eligible) >= 2, "no safe TRAIN-only zero-update input")
    rows = eligible[:2]
    expr = torch.from_numpy(np.log1p(full[rows]).astype(np.float32))
    mask = torch.from_numpy(support[rows].copy())
    cell_keys = torch.from_numpy(rows.astype(np.int64) + 11_000_000)
    insist(bool((expr[~mask] == 0).all()), "wrong assay support normalization")
    torch.manual_seed(8113002)
    modules = build_reference_modules(
        vocabulary_size=N_ADDRESSES, width=160, heads=4, blocks=6,
        ffn_width=320, dropout=0.10, learning_rate=1e-4,
        betas=(0.9, 0.999), eps=1e-8, weight_decay=0.01,
        init_seed=8113002,
    )
    from scripts.v5.jepa_synth2048_collapse_sentinel_v1 import (
        check_encoder_gradient_registry, geometry_diagnostic, token_geometry_diagnostic,
    )
    mandatory_registry = check_encoder_gradient_registry(modules.online)
    modules.online.eval()
    modules.predictor.eval()
    modules.teacher.eval()
    before = [p.detach().clone() for m in (modules.online, modules.teacher, modules.predictor)
              for p in m.parameters()]
    blocks = sample_uniform_target_blocks(
        mask, production_seed=8813003, cell_indices=cell_keys, sample_pass=0,
        view_index=0, mask_fraction=0.40, block_count=16,
    )
    insist(not bool((blocks.hidden_mask & ~mask).any()), "hidden unmeasured address")
    with torch.no_grad():
        tp = pack_valid_tokens(expr, mask)
        visible = mask & ~blocks.hidden_mask
        sp = pack_valid_tokens(expr, visible)
        insist(not any(x in tp.canonical_gene_ids.flatten().tolist() for x in Q),
               "teacher acquired excluded q address")
        insist(not any(x in sp.canonical_gene_ids.flatten().tolist() for x in Q),
               "student acquired excluded q address")
        t = modules.teacher(tp.canonical_gene_ids, tp.expression,
                            torch.ones_like(tp.expression, dtype=torch.bool),
                            torch.zeros_like(tp.expression, dtype=torch.bool),
                            "target", cell_keys=cell_keys, run_seed=8113002,
                            update_index=0, view_index=0)
        s = modules.online(sp.canonical_gene_ids, sp.expression,
                           torch.ones_like(sp.expression, dtype=torch.bool),
                           torch.zeros_like(sp.expression, dtype=torch.bool),
                           "student", cell_keys=cell_keys, run_seed=8113002,
                           update_index=0, view_index=1)
        pred = modules.predictor(
            modules.online.tokenizer.gene_identity, blocks, s.gene_states,
            s.cell_state, torch.ones_like(sp.expression, dtype=torch.bool),
        )
        target = gather_block_states(t.gene_states,
                                     _packed_teacher_blocks(blocks, tp.canonical_gene_ids))
        loss = weighted_block_jepa_loss(
            pred, target, torch.ones(len(rows), dtype=torch.float32))
    insist(bool(torch.isfinite(loss)), "nonfinite zero-update loss")
    insist(bool(torch.isfinite(t.cell_state).all()
                and torch.isfinite(s.cell_state).all()), "nonfinite state")
    after = [p.detach() for m in (modules.online, modules.teacher, modules.predictor)
             for p in m.parameters()]
    insist(all(torch.equal(a, b) for a, b in zip(before, after)),
           "zero-update probe mutated network parameters")
    insist(len(modules.optimizer.state) == 0, "optimizer state exists at zero updates")
    insist(all(p.grad is None for p in modules.teacher.parameters()), "teacher gradient appeared")
    teacher_geometry = geometry_diagnostic(t.cell_state.detach().cpu().numpy())
    student_geometry = geometry_diagnostic(s.cell_state.detach().cpu().numpy())
    teacher_token_geometry = token_geometry_diagnostic(
        t.gene_states.detach().cpu().numpy(),
        gene_ids=tp.canonical_gene_ids.detach().cpu().numpy(),
    )
    student_token_geometry = token_geometry_diagnostic(
        s.gene_states.detach().cpu().numpy(),
        gene_ids=sp.canonical_gene_ids.detach().cpu().numpy(),
    )
    return {
        "status": "ACTUAL_V5_SIX_BLOCK_U0_FORWARD_PASS__NO_LEARNING",
        "actor": "KeyedIPBEncoderV2Reference+BlockPredictor",
        "encoder_blocks": 6, "width": 160, "heads": 4,
        "cases": len(rows), "molecular_addresses": N_ADDRESSES,
        "measured_addresses_per_cell": [int(x) for x in mask.sum(dim=1)],
        "visible_addresses_per_cell": [int(x) for x in visible.sum(dim=1)],
        "target_block_count": 16,
        "historical_mandatory_48_registry": mandatory_registry,
        "u0_teacher_cell_geometry": teacher_geometry.__dict__,
        "u0_student_cell_geometry": student_geometry.__dict__,
        "u0_teacher_gene_token_geometry": teacher_token_geometry,
        "u0_student_gene_token_geometry": student_token_geometry,
        "u0_jepa_mse_mechanics_only": float(loss),
        "optimizer_updates": 0, "ema_updates": 0, "teacher_grads": 0,
        "training_authorized": False, "target_qualified": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fit-zip", type=Path, required=True)
    parser.add_argument("--mode", choices=("preflight", "u0"), default="preflight")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    verify_v5_runtime_sources()
    receipt, student, roster = verified_fit(args.fit_zip)
    full, support, report = audit_fit(receipt, student, roster)
    if args.mode == "u0":
        report["zero_update_model_probe"] = run_zero_update_model_probe(full, support, roster)
    if args.report:
        args.report.write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps(report, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
