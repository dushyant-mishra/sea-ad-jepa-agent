#!/usr/bin/env python3
"""Original V5 source + public DEV2048 FIT identity gate, without importing torch.

Read-only identity verification, deliberately NOT an execution, target-selection,
data-rights, provenance-issuer, model-health or checkpoint/restart gate.
Pin the *actual original PR224 contract* (12 files, 2 private implementation
files and package init), not an invented 'canonical_runtime.py' file, the
older direct-step main, or the separate V4 production teacher/student runtime.

PR547 FIT-only development ZIP is safe to hash here; no sealed V80 controller
or real donor RNA is read. No imports of the model or any training/optimizer APIs.
"""
from __future__ import annotations

import argparse
import ast
from hashlib import sha1, sha256
import json
from pathlib import Path
import zipfile


class SourceDataRefusal(ValueError):
    pass


def refuse(reason: str) -> None:
    raise SourceDataRefusal("REFUSE_V5_SOURCE_DATA_LOCK__" + reason)


AUTHORITY = ("TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__"
             "REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED")
ORIGINAL_V5_HEAD = "9d00684e08ba34ef8d7b04e478b9c380cd36d537"
INTEGRATED_JOURNAL_BASE_HEAD = "e71d864b0496de0b86fe7442ba51d53b44e0b225"
SOURCE_DECLARATION = "src/sea_ad_jepa/v5/_inactive_checkpoint_binding_impl_v1.py"
READINESS_ADAPTER = "scripts/v5/jepa_synth2048_v5_readiness.py"
READINESS_BLOB = "6a6c219402d7acd24c1b54b3c2571133a08e4a0a"
EXPECTED_SOURCE_RELATIVE = (
    "inactive_update_reference.py",
    "inactive_guarded_update_v1.py",
    "prefreeze_runtime_authority.py",
    "inactive_checkpoint_binding_v1.py",
    "ema_presentation_v1.py",
    "ema_bound_runtime_proof_v1.py",
    "ema_persisted_continuation_v2.py",
    "data_first_geometry.py",
    "keyed_dropout_prototype_v2.py",
    "keyed_rng_contract_v2.py",
    "../v4/ipb_jepa.py",
    "../v4/gene_tokenizer.py",
)
ORIGINAL_SOURCE_GIT_BLOBS = {
    "src/sea_ad_jepa/v5/inactive_update_reference.py": "ab266faa31ac7d3e51acf695a7deff1702368cde",
    "src/sea_ad_jepa/v5/inactive_guarded_update_v1.py": "59647eb0122dfd98068844f68b6d48c2c33d67ca",
    "src/sea_ad_jepa/v5/prefreeze_runtime_authority.py": "41a6ebde613ee3ec5c898fa39e5a212c14eaac66",
    "src/sea_ad_jepa/v5/inactive_checkpoint_binding_v1.py": "8d7ad56a4cefe011f95d491511d3c165386e4020",
    "src/sea_ad_jepa/v5/ema_presentation_v1.py": "6f4442e25a6f891b9548b11403154233f616d842",
    "src/sea_ad_jepa/v5/ema_bound_runtime_proof_v1.py": "b6bf21cc129358c0708fbd3cc08977cf90191003",
    "src/sea_ad_jepa/v5/ema_persisted_continuation_v2.py": "865f6991dd5822a37aa223604799eefcf0eddb9f",
    "src/sea_ad_jepa/v5/data_first_geometry.py": "93b08f49f9d92b5c158e1a53fd5331b964f0e13f",
    "src/sea_ad_jepa/v5/keyed_dropout_prototype_v2.py": "0fd06ae0891625924761ef097b20ba6e11495cb3",
    "src/sea_ad_jepa/v5/keyed_rng_contract_v2.py": "dcd4abf9790f25db1f576fbf821a75e13057a03e",
    "src/sea_ad_jepa/v4/ipb_jepa.py": "3bd9d601a6779818a45c437cc21fd4a64749eb6e",
    "src/sea_ad_jepa/v4/gene_tokenizer.py": "0fd283136323a49b5554f2fb33d0c65ee31be576",
    "src/sea_ad_jepa/v5/_inactive_checkpoint_binding_impl_v1.py": "5be5177a0d5893ddc1140d69844549cd76c95bf0",
    "src/sea_ad_jepa/v5/_ema_bound_runtime_proof_impl_v1.py": "fac5f7c704c8e303f52c04ade91e8acc364dae9d",
    "src/sea_ad_jepa/v5/__init__.py": "5b80f3e917fc7f319f4340ad8cde16c99a20a538",
}
SOURCE_SUBSET_IN_PR548 = (
    "src/sea_ad_jepa/v5/keyed_dropout_prototype_v2.py",
    "src/sea_ad_jepa/v5/keyed_rng_contract_v2.py",
    "src/sea_ad_jepa/v5/data_first_geometry.py",
    "src/sea_ad_jepa/v5/inactive_update_reference.py",
    "src/sea_ad_jepa/v5/inactive_guarded_update_v1.py",
    "src/sea_ad_jepa/v5/prefreeze_runtime_authority.py",
    "src/sea_ad_jepa/v5/ema_presentation_v1.py",
    "src/sea_ad_jepa/v5/ema_persisted_continuation_v2.py",
    "src/sea_ad_jepa/v4/ipb_jepa.py",
    "src/sea_ad_jepa/v4/gene_tokenizer.py",
)
DEV_FIT_ZIP_SHA256 = "87fe3ec2038305c797c439cd9780036fe22cc22b647242749b1af0bfb444c06f"
DEV_FIT_ZIP_BYTES = 25023562
DEV_FIT_MEMBERS = {
    "teacher_measured.npz": "f38133844359017174e070fb5e4b5afc48334db86c80f17e99ef7b54014d6cc1",
    "student_qexcluded.npz": "a1fce3b79beb0d7632a0ffcdc9f28e94aadb4a594e9c76a8f6f6c48d1b99a0b5",
    "roster_evaluation_only.npz": "0427f1221f55e607cf32abb827db1be1026274b2acf3134f3a05e9f513a48c18",
    "atac_separate_nucleus_negative.npz": "26b35ab4e43ad3ee3e98c81d017b300dab2e70945a608e25154d9346ba2df321",
    "DEVELOPMENT_RECEIPT.json": "91310b3c3d86e28ce19a4090c624b53d4a6d0e31b5984dc9a8e159d08a4b1b0d",
}
DEV_ROSTER = {"cells": 1440, "genes": 2048, "donors": 36}
DEV_QUERY_GENE_ADDRESSES = (1672, 1673, 1674, 1675)


def _regular_bytes(root: Path, relative: str) -> bytes:
    path = root / relative
    if not path.is_file() or path.is_symlink():
        refuse("REQUIRED_REGULAR_FILE_MISSING_OR_SYMLINK__" + relative)
    return path.read_bytes()


def _git_sha1(raw: bytes) -> str:
    return sha1(f"blob {len(raw)}\0".encode("ascii") + raw).hexdigest()


def _literal_name(raw: bytes, symbol: str, path: str):
    """Read an assignment's literal AST without executing or importing Python."""
    try:
        tree = ast.parse(raw.decode("utf-8"), filename=path)
        matches = [node.value for node in tree.body
                   if isinstance(node, ast.Assign)
                   and any(isinstance(t, ast.Name) and t.id == symbol
                           for t in node.targets)]
        if len(matches) != 1:
            refuse("EXPECTED_EXACTLY_ONE_DECLARATION__" + symbol)
        return ast.literal_eval(matches[0])
    except (SyntaxError, UnicodeDecodeError, ValueError, TypeError) as exc:
        raise SourceDataRefusal("REFUSE_V5_SOURCE_DATA_LOCK__INVALID_STATIC_DECLARATION__"
                                + symbol) from exc


def audit_sources(repo_root: Path) -> dict:
    """Require all 15 original V5 source Git blobs, not only ten from U0."""
    root = Path(repo_root)
    for path, expected in ORIGINAL_SOURCE_GIT_BLOBS.items():
        observed = _git_sha1(_regular_bytes(root, path))
        if observed != expected:
            refuse("ORIGINAL_V5_SOURCE_CHANGED__" + path)

    original = _regular_bytes(root, SOURCE_DECLARATION)
    declared = _literal_name(original, "CANONICAL_RUNTIME_SOURCE_FILES",
                             SOURCE_DECLARATION)
    if type(declared) is not tuple or declared != EXPECTED_SOURCE_RELATIVE:
        refuse("ORIGINAL_12_FILE_RUNTIME_CONTRACT_CHANGED")

    readiness = _regular_bytes(root, READINESS_ADAPTER)
    if _git_sha1(readiness) != READINESS_BLOB:
        refuse("PR548_2048_INPUT_ADAPTER_CHANGED")

    adapter_source = _literal_name(readiness, "SOURCE_SHA1", READINESS_ADAPTER)
    if (type(adapter_source) is not dict
            or tuple(adapter_source) != SOURCE_SUBSET_IN_PR548
            or any(adapter_source[key] != ORIGINAL_SOURCE_GIT_BLOBS[key]
                   for key in SOURCE_SUBSET_IN_PR548)):
        refuse("PR548_INPUT_ACTOR_SOURCE_CROSSED_OR_CHANGED")

    if (_literal_name(readiness, "ZIP_SHA256", READINESS_ADAPTER)
            != DEV_FIT_ZIP_SHA256
            or _literal_name(readiness, "MEMBER_SHA256", READINESS_ADAPTER)
            != DEV_FIT_MEMBERS
            or _literal_name(readiness, "N_CELLS", READINESS_ADAPTER)
            != DEV_ROSTER["cells"]
            or _literal_name(readiness, "N_ADDRESSES", READINESS_ADAPTER)
            != DEV_ROSTER["genes"]
            or _literal_name(readiness, "Q", READINESS_ADAPTER)
            != DEV_QUERY_GENE_ADDRESSES):
        refuse("PR548_SYNTHETIC_DATA_OR_QUERY_IDENTITY_CHANGED")

    return {
        "original_v5_source_head": ORIGINAL_V5_HEAD,
        "all_15_original_v5_git_blobs_match": True,
        "canonical_runtime_file_count": len(EXPECTED_SOURCE_RELATIVE),
        "private_implementation_count": 2,
        "initializer_checked": True,
        "v4_utilities_in_original_v5_declaration": [
            "src/sea_ad_jepa/v4/ipb_jepa.py",
            "src/sea_ad_jepa/v4/gene_tokenizer.py",
        ],
        "older_v4_production_trainer_substituted": False,
        "legacy_canonical_runtime_py_required": False,
        "pr548_u0_actor_and_data_declarations_match": True,
        "source_revision_authorized_for_training": False,
    }


def audit_dev_fit(fit_zip: Path) -> dict:
    """Byte-verify only the public PR547 FIT; no NPZ torch/load or controller."""
    path = Path(fit_zip)
    if not path.is_file() or path.is_symlink() or path.stat().st_size != DEV_FIT_ZIP_BYTES:
        refuse("PUBLIC_DEV_FIT_ZIP_MISSING_OR_WRONG_SIZE")
    if sha256(path.read_bytes()).hexdigest() != DEV_FIT_ZIP_SHA256:
        refuse("PUBLIC_DEV_FIT_ZIP_SHA_MISMATCH")
    try:
        with zipfile.ZipFile(path, "r") as bundle:
            names = bundle.namelist()
            if len(names) != len(DEV_FIT_MEMBERS) or set(names) != set(DEV_FIT_MEMBERS):
                refuse("PUBLIC_DEV_FIT_MEMBER_SET_CHANGED")
            for name, digest in DEV_FIT_MEMBERS.items():
                if sha256(bundle.read(name)).hexdigest() != digest:
                    refuse("PUBLIC_DEV_FIT_MEMBER_SHA_CHANGED__" + name)
    except (zipfile.BadZipFile, OSError, RuntimeError) as exc:
        raise SourceDataRefusal("REFUSE_V5_SOURCE_DATA_LOCK__PUBLIC_DEV_FIT_INVALID") from exc
    return {
        "pr547_public_fit_archive_sha256": DEV_FIT_ZIP_SHA256,
        "pr547_public_fit_archive_bytes": DEV_FIT_ZIP_BYTES,
        "exact_member_digests_verified": True,
        "member_names": sorted(DEV_FIT_MEMBERS),
        "dimensions_declared_from_pr547": DEV_ROSTER,
        "query_ids_declared_from_pr547": list(DEV_QUERY_GENE_ADDRESSES),
        "real_human_rna": False,
        "private_v80_controller_read": False,
        "learned_state_or_controller_truth_inspected": False,
    }


def audit(*, repo_root: Path, fit_zip: Path | None = None) -> dict:
    source = audit_sources(repo_root)
    return {
        "schema": "JEPA_V5_DEV2048_SOURCE_DATA_IDENTITY_GATE_V1",
        "source": source,
        "data": audit_dev_fit(fit_zip) if fit_zip is not None else {
            "fit_bytes_verified": False,
            "expected_public_fit_sha256": DEV_FIT_ZIP_SHA256,
            "reason": "NO_FIT_PATH_SUPPLIED__MUST_NOT_CALL_THIS_COMPLETE",
        },
        "pipeline": {
            "active_model": "ORIGINAL_GUARDED_V5_ONE_UPDATE",
            "active_input": "PR547_PUBLIC_SYNTHETIC_2048_FIT_ONLY",
            "checkpoint": "PR582_SYNTHETIC_JOURNAL_ONLY",
            "separate_posttd_pr525_runtime_identity": "V4_FILES__NOT_SAME_ACTOR_BINDING",
            "single_end_to_end_model_journal_train_path_proved": False,
            "multi_update_v5_driver_exists_or_proved": False,
            "real_training_authorized": False,
            "physical_probes_proved": False,
            "source_rights_issuer_or_real_PANEL_authority_proved": False,
        },
        "training_authorized": False,
        "authority": AUTHORITY,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--fit-zip", type=Path)
    args = parser.parse_args()
    print(json.dumps(audit(repo_root=args.repo_root, fit_zip=args.fit_zip),
                     indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
