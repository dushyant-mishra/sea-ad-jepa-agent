from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np

import build_td_relational_synthetic_package_v2 as V2


PACKAGE_ID = "JEPA_TD_RELATIONAL_SYNTHETIC_V2_1_20261013"
PACKAGE_SCHEMA = V2.PACKAGE_SCHEMA
CONTROLLER_SCHEMA = "JEPA_TD_RELATIONAL_SUCCESSOR_CONTROLLER_MANIFEST_V3"
FIT_ROOT_SCHEMA = "JEPA_TD_RELATIONAL_SYNTHETIC_FIT_ROOT_V2_1"
FEATURE_COUNT = 512
DONOR_COUNT = 6
CELLS_PER_DONOR = 35
CONTROL_COUNT = 5

CAPABILITIES = V2.CAPABILITIES
RARE_CONTROL_CAPABILITIES = V2.RARE_CONTROL_CAPABILITIES
CONTROL_ROLES = V2.CONTROL_ROLES
SEMANTIC_CLASS = V2.SEMANTIC_CLASS
FIT_VIEW_FIELDS = V2.FIT_VIEW_FIELDS
BINDING_AUTHORITY = V2.BINDING_AUTHORITY
CONTROLLER_AUTHORITY = V2.CONTROLLER_AUTHORITY


def _require_hex256(value: str, label: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or any(ch not in "0123456789abcdef" for ch in value):
        raise ValueError(f"{label} must be lowercase 256-bit hex")
    return value


def _secret_digest(seed_hex: str, label: str) -> bytes:
    seed = bytes.fromhex(_require_hex256(seed_hex, "realization_seed_hex"))
    return hashlib.sha256(seed + b"|TD_SYNTH_V2_1|" + label.encode("utf-8")).digest()


def _secret_token(seed_hex: str, label: str, prefix: str) -> str:
    return f"{prefix}-{_secret_digest(seed_hex, label).hex()[:20]}"


def _secret_permutation(seed_hex: str, label: str, n: int) -> list[int]:
    raw = int.from_bytes(_secret_digest(seed_hex, label)[:8], "big", signed=False)
    return np.random.default_rng(raw).permutation(n).tolist()


def _base_world(seed: int) -> dict[str, Any]:
    donors, operators, local_rows, global_rows = V2._base_population(DONOR_COUNT)
    library, detected = V2._technical_covariates(donors, local_rows, seed + 11)
    return {
        "source": "S0",
        "panel_id": "P0",
        "donor_ids": donors,
        "operator_ids": operators,
        "local_rows": local_rows,
        "global_rows": global_rows,
        "source_library": library,
        "detected_genes": detected,
    }


def _nuisance_controls(donors: np.ndarray, primary: np.ndarray) -> list[np.ndarray]:
    donor_s = donors.astype(str)
    out = [np.zeros(len(donors), dtype=bool) for _ in range(CONTROL_COUNT)]
    for donor in sorted(set(donor_s.tolist())):
        idx = np.where(donor_s == donor)[0]
        available = idx[~primary[idx]]
        if len(available) < CONTROL_COUNT:
            available = idx
        for j, row in enumerate(available.tolist()):
            out[j % CONTROL_COUNT][row] = True
        for j in range(CONTROL_COUNT):
            if not np.any(out[j][idx]):
                out[j][idx[j % len(idx)]] = True
    return out


def _take_sorted(candidates: np.ndarray, score: np.ndarray, k: int, *, reverse: bool = False) -> np.ndarray:
    if len(candidates) == 0:
        return candidates
    order = np.argsort(score, kind="mergesort")
    if reverse:
        order = order[::-1]
    return candidates[order[: min(k, len(candidates))]]


def _role_controls_and_apply_pseudo(world: dict[str, Any], primary: np.ndarray, *, seed: int) -> dict[str, np.ndarray]:
    donors = world["donor_ids"].astype(str)
    local = world["local_rows"].astype(float)
    library = world["source_library"]
    detected = world["detected_genes"]
    roles = {role: np.zeros(len(donors), dtype=bool) for role in CONTROL_ROLES}

    for donor in sorted(set(donors.tolist())):
        idx = np.where(donors == donor)[0]
        p = idx[primary[idx]]
        if len(p) == 0:
            continue
        common = idx[~primary[idx]]
        if len(common) == 0:
            raise ValueError("role-faithful controls require non-focal common cells")
        k = min(len(p), len(common))
        p_local = float(np.median(local[p]))
        p_lib = float(np.median(library[p]))
        p_det = float(np.median(detected[p]))

        near = _take_sorted(common, np.abs(local[common] - p_local), k)
        roles["DONOR_MATCHED_COMMON"][near] = True

        # Same source/operator are guaranteed by construction; choose a deterministic recurrent common subset.
        source_op = np.sort(common)[:k]
        roles["SOURCE_OPERATOR_MATCHED"][source_op] = True

        tech_far_score = (
            np.abs(library[common] - p_lib) / max(p_lib, 1.0)
            + np.abs(detected[common] - p_det) / max(p_det, 1.0)
            + 0.05 * np.abs(local[common] - p_local)
        )
        wrong = _take_sorted(common, tech_far_score, k, reverse=True)
        roles["WRONG_CELL"][wrong] = True

        # Pick a separate deterministic tail when possible for the technical pseudo-rare control.
        pseudo_order = np.argsort(local[common], kind="mergesort")[::-1]
        pseudo = common[pseudo_order[:k]]
        roles["PSEUDO_RARE_TECHNICAL"][pseudo] = True

    pseudo_mask = roles["PSEUDO_RARE_TECHNICAL"]
    if np.any(pseudo_mask):
        px = V2._support(int(pseudo_mask.sum()), seed=seed + 701, keep=0.78)
        py = V2._support(int(pseudo_mask.sum()), seed=seed + 702, keep=0.78)
        world["x_measured"][pseudo_mask] &= px
        world["y_measured"][pseudo_mask] &= py
        world["source_library"][pseudo_mask] *= 0.72
        world["detected_genes"][pseudo_mask] = world["x_measured"][pseudo_mask].sum(axis=1).astype(np.int64)

    # Match depth/detection after pseudo-rare degradation so this role is prospective on delivered covariates.
    for donor in sorted(set(donors.tolist())):
        idx = np.where(donors == donor)[0]
        p = idx[primary[idx]]
        if len(p) == 0:
            continue
        common = idx[~primary[idx]]
        k = min(len(p), len(common))
        p_lib = float(np.median(world["source_library"][p]))
        p_det = float(np.median(world["detected_genes"][p]))
        score = (
            np.abs(world["source_library"][common] - p_lib) / max(p_lib, 1.0)
            + np.abs(world["detected_genes"][common] - p_det) / max(p_det, 1.0)
        )
        preferred = common[~pseudo_mask[common]]
        preferred_score = score[~pseudo_mask[common]]
        chosen = _take_sorted(preferred, preferred_score, k)
        if len(chosen) < k:
            remaining = common[~np.isin(common, chosen)]
            remaining_score = (
                np.abs(world["source_library"][remaining] - p_lib) / max(p_lib, 1.0)
                + np.abs(world["detected_genes"][remaining] - p_det) / max(p_det, 1.0)
            )
            extra = _take_sorted(remaining, remaining_score, k - len(chosen))
            chosen = np.concatenate([chosen, extra])
        roles["DEPTH_DETECTED_SUM_MATCHED"][chosen] = True

    return roles


def _broad_world() -> dict[str, Any]:
    base = _base_world(51001)
    local = base["local_rows"]
    group = np.minimum(local // 7, 4).astype(np.float64)
    centered = group - 2.0
    within = (local % 7).astype(np.float64) / 6.0 - 0.5
    latent = np.column_stack((centered * 4.5, within * 1.5))
    coarse = np.column_stack((centered * 4.5, np.zeros_like(centered)))
    n = len(local)
    primary = np.ones(n, dtype=bool)
    base.update({
        "latent": latent,
        "z_values": V2._encode_latent(latent),
        "x_values": V2._encode_latent(coarse),
        "y_values": V2._encode_latent(coarse),
        "z_measured": V2._support(n, seed=51021, keep=1.0),
        "x_measured": V2._support(n, seed=51022, keep=0.99),
        "y_measured": V2._support(n, seed=51023, keep=0.99),
        "primary_focal": primary,
        "primary_pool": np.ones(n, dtype=bool),
        "nuisance_controls": _nuisance_controls(base["donor_ids"], primary),
    })
    return base


def _source_stress_from_broad(broad: dict[str, Any]) -> dict[str, Any]:
    stress = {key: (value.copy() if isinstance(value, np.ndarray) else value) for key, value in broad.items()}
    stress["nuisance_controls"] = [mask.copy() for mask in broad["nuisance_controls"]]
    n = len(stress["donor_ids"])
    stress["x_measured"] = V2._support(n, seed=51122, keep=0.90)
    stress["y_measured"] = V2._support(n, seed=51123, keep=0.84)
    stress["y_values"] = (
        stress["y_values"] + np.random.default_rng(51124).normal(0.0, 0.035, stress["y_values"].shape)
    ).astype(np.float32)
    stress["source_library"] = stress["source_library"] * 0.72
    stress["detected_genes"] = stress["x_measured"].sum(axis=1).astype(np.int64)
    # source/panel/global rows intentionally remain identical to broad so triplet hash identity is not confounded.
    return stress


def _fine_world(seed: int = 52001) -> dict[str, Any]:
    base = _base_world(seed)
    latent = V2._line_latent(base["local_rows"], scale=5.5)
    n = len(latent)
    primary = np.ones(n, dtype=bool)
    base.update({
        "latent": latent,
        "z_values": V2._encode_latent(latent, noise_seed=seed + 1, noise_sd=0.002),
        "x_values": V2._encode_latent(latent, noise_seed=seed + 2, noise_sd=0.002),
        "y_values": V2._encode_latent(latent, noise_seed=seed + 3, noise_sd=0.002),
        "z_measured": V2._support(n, seed=seed + 4, keep=0.995),
        "x_measured": V2._support(n, seed=seed + 5, keep=0.995),
        "y_measured": V2._support(n, seed=seed + 6, keep=0.995),
        "primary_focal": primary,
        "primary_pool": np.ones(n, dtype=bool),
        "nuisance_controls": _nuisance_controls(base["donor_ids"], primary),
    })
    return base


def _underpowered_world() -> dict[str, Any]:
    world = _fine_world(seed=56001)
    donors = world["donor_ids"].astype(str)
    active = sorted(set(donors.tolist()))[:4]
    focal = np.isin(donors, active)
    world["primary_focal"] = focal
    world["nuisance_controls"] = _nuisance_controls(world["donor_ids"], focal)
    return world


def _rare_world(*, multi: bool = False, donor_restricted: bool = False, seed: int = 53001) -> dict[str, Any]:
    base = _base_world(seed)
    donors = base["donor_ids"]
    local = base["local_rows"]
    donor_s = donors.astype(str)
    n = len(donors)
    primary = np.zeros(n, dtype=bool)
    latent = np.column_stack((12.0 + local.astype(np.float64) / 3.0, np.zeros(n, dtype=np.float64)))
    z_latent = latent.copy()
    background = V2._line_latent(local, scale=5.0)
    x_latent = V2._permute_within_donor(background, donors, seed=seed + 101)
    y_latent = V2._permute_within_donor(background, donors, seed=seed + 102)
    active_donors = sorted(set(donor_s.tolist()))[:5] if donor_restricted else sorted(set(donor_s.tolist()))
    for donor in active_donors:
        idx = np.where(donor_s == donor)[0]
        groups = [idx[13:21]]
        centers = [0.0]
        if multi:
            groups = [idx[:6], idx[20:26]]
            centers = [-4.0, 4.0]
        for rows, center in zip(groups, centers):
            primary[rows] = True
            coordinate = np.linspace(-0.45, 0.45, len(rows), dtype=np.float64)
            island = np.column_stack((np.full(len(rows), center), coordinate * 3.0))
            latent[rows] = island
            z_latent[rows] = island
            x_latent[rows] = island
            y_latent[rows] = island
    base.update({
        "latent": latent,
        "z_values": V2._encode_latent(z_latent, noise_seed=seed + 20, noise_sd=0.002),
        "x_values": V2._encode_latent(x_latent, noise_seed=seed + 21, noise_sd=0.003),
        "y_values": V2._encode_latent(y_latent, noise_seed=seed + 22, noise_sd=0.003),
        "z_measured": V2._support(n, seed=seed + 10, keep=0.99),
        "x_measured": V2._support(n, seed=seed + 11, keep=0.99),
        "y_measured": V2._support(n, seed=seed + 12, keep=0.99),
        "primary_focal": primary,
        "primary_pool": np.ones(n, dtype=bool),
    })
    base["role_controls"] = _role_controls_and_apply_pseudo(base, primary, seed=seed)
    return base


def _technical_twin_world(seed: int = 54001) -> dict[str, Any]:
    base = _base_world(seed)
    donors = base["donor_ids"]
    local = base["local_rows"]
    donor_s = donors.astype(str)
    n = len(donors)
    primary = np.zeros(n, dtype=bool)
    z_latent = V2._line_latent(local, scale=7.0)
    background = V2._line_latent(local, scale=5.0)
    x_latent = V2._permute_within_donor(background, donors, seed=seed + 101)
    y_latent = V2._permute_within_donor(background, donors, seed=seed + 102)
    for donor in sorted(set(donor_s.tolist())):
        idx = np.where(donor_s == donor)[0]
        rows = idx[13:21]
        primary[rows] = True
        z_latent[rows] = np.column_stack((np.zeros(len(rows)), np.linspace(-1.0, 1.0, len(rows))))
    base.update({
        "latent": background,
        "z_values": V2._encode_latent(z_latent),
        "x_values": V2._encode_latent(x_latent, noise_seed=seed + 20, noise_sd=0.004),
        "y_values": V2._encode_latent(y_latent, noise_seed=seed + 21, noise_sd=0.004),
        "z_measured": V2._support(n, seed=seed + 10, keep=0.99),
        "x_measured": V2._support(n, seed=seed + 11, keep=0.99),
        "y_measured": V2._support(n, seed=seed + 12, keep=0.99),
        "primary_focal": primary,
        "primary_pool": np.ones(n, dtype=bool),
    })
    px = V2._support(int(primary.sum()), seed=seed + 13, keep=0.80)
    py = V2._support(int(primary.sum()), seed=seed + 14, keep=0.80)
    base["x_measured"][primary] &= px
    base["y_measured"][primary] &= py
    base["source_library"][primary] *= 0.72
    base["detected_genes"][primary] = base["x_measured"][primary].sum(axis=1).astype(np.int64)
    base["role_controls"] = _role_controls_and_apply_pseudo(base, primary, seed=seed)
    return base


def _null_world(seed: int = 55001) -> dict[str, Any]:
    base = _base_world(seed)
    donors = base["donor_ids"]
    local = base["local_rows"]
    z_latent = V2._line_latent(local, scale=5.0)
    x_latent = V2._permute_within_donor(z_latent, donors, seed=seed + 101)
    y_latent = V2._permute_within_donor(z_latent, donors, seed=seed + 102)
    n = len(donors)
    primary = np.ones(n, dtype=bool)
    base.update({
        "latent": z_latent,
        "z_values": V2._encode_latent(z_latent),
        "x_values": V2._encode_latent(x_latent, noise_seed=seed + 20, noise_sd=0.004),
        "y_values": V2._encode_latent(y_latent, noise_seed=seed + 21, noise_sd=0.004),
        "z_measured": V2._support(n, seed=seed + 10, keep=0.99),
        "x_measured": V2._support(n, seed=seed + 11, keep=0.99),
        "y_measured": V2._support(n, seed=seed + 12, keep=0.99),
        "primary_focal": primary,
        "primary_pool": np.ones(n, dtype=bool),
        "nuisance_controls": _nuisance_controls(donors, primary),
    })
    return base


def build_worlds_for_self_audit() -> dict[str, dict[str, Any]]:
    broad = _broad_world()
    return {
        "REL_BROAD_MESO_POSITIVE": broad,
        "REL_FINE_RECURRENT_POSITIVE": _fine_world(),
        "REL_RARE_LOCAL_ISLAND_POSITIVE": _rare_world(seed=53001),
        "REL_MULTI_ISLAND_POSITIVE": _rare_world(multi=True, seed=53101),
        "REL_DONOR_RESTRICTED_POSITIVE": _rare_world(donor_restricted=True, seed=53201),
        "REL_SOURCE_VISIBILITY_STRESS": _source_stress_from_broad(broad),
        "REL_TECHNICAL_TWIN_NEGATIVE": _technical_twin_world(),
        "REL_NULL_NEGATIVE": _null_world(),
        "REL_UNDERPOWERED_POSITIVE": _underpowered_world(),
    }


def _challenge_id(seed_hex: str, capability: str) -> str:
    return _secret_token(seed_hex, f"challenge|{capability}", "q")


def _control_material(seed_hex: str, capability: str, challenge_id: str, world: dict[str, Any]):
    if capability in RARE_CONTROL_CAPABILITIES:
        semantic_items = [(role, world["role_controls"][role]) for role in CONTROL_ROLES]
    else:
        semantic_items = [(f"NUISANCE_{i}", mask) for i, mask in enumerate(world["nuisance_controls"])]
    records = []
    role_map: dict[str, list[str]] = {}
    for semantic_label, mask in semantic_items:
        control_id = _secret_token(seed_hex, f"control|{capability}|{semantic_label}|{challenge_id}", "c")
        records.append((semantic_label, control_id, mask))
        if capability in RARE_CONTROL_CAPABILITIES:
            role_map[semantic_label] = [control_id]
    permutation = _secret_permutation(seed_hex, f"control-order|{capability}|{challenge_id}", len(records))
    ordered = [records[index] for index in permutation]
    return ordered, role_map


def _fit_arrays(world: dict[str, Any], ordered_controls) -> dict[str, np.ndarray]:
    n = len(world["donor_ids"])
    arrays = {
        "source": np.asarray(world["source"], dtype="U8"),
        "panel_id": np.asarray(world["panel_id"], dtype="U8"),
        "z_values": np.asarray(world["z_values"], dtype=np.float32),
        "x_values": np.asarray(world["x_values"], dtype=np.float32),
        "y_values": np.asarray(world["y_values"], dtype=np.float32),
        "z_measured": np.asarray(world["z_measured"], dtype=bool),
        "x_measured": np.asarray(world["x_measured"], dtype=bool),
        "y_measured": np.asarray(world["y_measured"], dtype=bool),
        "z_feature_ids": V2._feature_ids("Z"),
        "x_feature_ids": V2._feature_ids("X"),
        "y_feature_ids": V2._feature_ids("Y"),
        "donor_ids": np.asarray(world["donor_ids"], dtype="U8"),
        "operator_ids": np.asarray(world["operator_ids"], dtype="U4"),
        "global_rows": np.asarray(world["global_rows"], dtype=np.int64),
        "source_library": np.asarray(world["source_library"], dtype=np.float64),
        "detected_genes": np.asarray(world["detected_genes"], dtype=np.int64),
        "focal_mask": np.asarray(world["primary_focal"], dtype=bool),
        "neighbor_pool_mask": np.asarray(world["primary_pool"], dtype=bool),
        "min_focal_anchors_per_donor": np.asarray(1, dtype=np.int64),
        "control_ids": np.asarray([item[1] for item in ordered_controls], dtype="U24"),
        "control_focal_masks": np.stack([item[2] for item in ordered_controls], axis=0).astype(bool),
        "control_neighbor_pool_masks": np.ones((CONTROL_COUNT, n), dtype=bool),
        "control_min_focal_anchors_per_donor": np.ones(CONTROL_COUNT, dtype=np.int64),
    }
    return arrays


def main(out_dir: str, *, realization_seed_hex: str, blind_nonce: str) -> Path:
    realization_seed_hex = _require_hex256(realization_seed_hex, "realization_seed_hex")
    blind_nonce = _require_hex256(blind_nonce, "blind_nonce")
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    fit_dir = root / "fit_views"
    fit_dir.mkdir(parents=True, exist_ok=True)
    controller_dir = root / "controller"
    controller_dir.mkdir(parents=True, exist_ok=True)

    worlds = build_worlds_for_self_audit()
    fit_records = []
    claims = {}
    realization_map = {}

    for capability in CAPABILITIES:
        challenge_id = _challenge_id(realization_seed_hex, capability)
        controls, role_map = _control_material(realization_seed_hex, capability, challenge_id, worlds[capability])
        arrays = _fit_arrays(worlds[capability], controls)
        scratch = fit_dir / f".{challenge_id}.npz"
        V2._write_deterministic_npz(scratch, arrays)
        digest = V2.file_sha256(scratch)
        final = fit_dir / f"{digest}.npz"
        scratch.replace(final)
        fit_records.append({"challenge_id": challenge_id, "sha256": digest})
        claims[capability] = {
            "challenge_id": challenge_id,
            "semantic_class": SEMANTIC_CLASS[capability],
            "control_roles": role_map,
            "expected_status": "PASS" if capability == "REL_SOURCE_VISIBILITY_STRESS" else None,
        }
        realization_map[capability] = {
            "challenge_id": challenge_id,
            "control_roles": role_map,
            "fit_view_sha256": digest,
        }

    fit_records = sorted(fit_records, key=lambda rec: rec["challenge_id"])
    fit_root = {
        "schema": FIT_ROOT_SCHEMA,
        "package_id": PACKAGE_ID,
        "fit_view_fields": list(FIT_VIEW_FIELDS),
        "fit_views": fit_records,
        "authority": dict(BINDING_AUTHORITY),
    }
    package_sha256 = V2.canonical_sha256(fit_root)
    V2._write_json(root / "fit_package_root.json", fit_root)

    controller = {
        "schema": CONTROLLER_SCHEMA,
        "package_sha256": package_sha256,
        "blind_nonce": blind_nonce,
        "claims": claims,
        "authority": dict(CONTROLLER_AUTHORITY),
    }
    controller_sha256 = V2.canonical_sha256(controller)
    V2._write_json(controller_dir / "controller_manifest.json", controller, preserve_order=True)

    binding = {
        "schema": PACKAGE_SCHEMA,
        "package_id": PACKAGE_ID,
        "package_sha256": package_sha256,
        "controller_truth_sha256": controller_sha256,
        "fit_view_fields": list(FIT_VIEW_FIELDS),
        "fit_views": fit_records,
        "authority": dict(BINDING_AUTHORITY),
    }
    V2._write_json(root / "TD_EXTERNAL_SYNTHETIC_PACKAGE_BINDING_V2.json", binding)

    realization_receipt = {
        "schema": "JEPA_TD_RELATIONAL_SYNTHETIC_V2_1_CONTROLLER_REALIZATION_V1",
        "package_id": PACKAGE_ID,
        "package_sha256": package_sha256,
        "realization_seed_hex": realization_seed_hex,
        "blind_nonce": blind_nonce,
        "mapping": realization_map,
        "authority": dict(CONTROLLER_AUTHORITY),
    }
    V2._write_json(controller_dir / "controller_realization_receipt.json", realization_receipt, preserve_order=True)
    return root


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Build sealed TD relational synthetic V2.1 package")
    parser.add_argument("output_dir")
    parser.add_argument("--realization-seed-hex", required=True)
    parser.add_argument("--blind-nonce", required=True)
    args = parser.parse_args()
    main(args.output_dir, realization_seed_hex=args.realization_seed_hex, blind_nonce=args.blind_nonce)
