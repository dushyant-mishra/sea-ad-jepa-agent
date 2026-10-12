#!/usr/bin/env python3
"""Build the Q10/Q11 pairing amendment bound to the canonical Contract V2 (controller rebind ruling 6115340528).

The paired-counterfactual semantics are those frozen by controller comment 6114906562 in amendment
09f60d91... (PR #291), copied verbatim. Only the authority binding changes: the canonical Contract V2 57e19295...,
obtained through PR #290's require_launch_authority(), replaces the obsolete non-canonical contract. Usage:
  build_v79_v2_core_pairing_amendment.py <repo_root>           write the amendment and its .sha256 (refuses to overwrite)
  build_v79_v2_core_pairing_amendment.py <repo_root> --check   regenerate and compare byte for byte
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import v79_v2_core_launch as L  # noqa: E402

AMENDMENT_REL = "results/v79/v2_core_qualification_amendments/V79_V2_CORE_Q10_Q11_PAIRING_AMENDMENT_V1.json"
PAYLOAD_SHA256 = "cbfa332b419f12205d26b7f1ebd645299acb9ecc7f1ed8cdccc526ebf88477b3"
SUPERSEDED = {"amendment_sha256": "09f60d91817a041badaa4fc5108125f02a02d1ebbe8242a0f012aa6978d56f7c",
              "bound_final_contract_sha256": "8be47cb2d36ec9ddfdf4fd820ed0d51adea871dc115c1414cbe4edfb9223ee1d",
              "reason": "bound to the non-canonical PR #289 contract line; semantics unchanged"}
PAIRED_COUNTERFACTUAL = {
    "parent_world": {"name": "Q10_S174_DESIGN_IMBALANCE", "world_index": 10},
    "child_world": {"name": "Q11_OMITTED_OPERATOR", "world_index": 11},
    "q11_inherits_q10_exactly": ["design", "structural_support_mask", "all_non_operator_planted_core_parameters",
                                 "donor_effects_and_shared_donor_factor", "factor_loading_assignment",
                                 "base_detection_observation_noise", "base_positive_observation_noise",
                                 "heldout_same_donor_base_noise", "new_donor_base_effects_and_noise"],
    "q11_new_randomness_only": {"operator_offsets_detection": 22, "operator_offsets_positive": 23},
    "effective_seed_parent_rule": "For Q11, every stream except 22 and 23 uses world_index=10; streams 22/23 retain world_index=11.",
    "common_random_numbers": True,
    "operator_offsets": {"distribution": "Normal(0, (0.5 x that gene donor SD)^2)", "centering": "unweighted within source",
                         "fitted": False},
    "truth_hash_rule": "Q10 and Q11 non-operator truth components must hash identically; only operator-offset fields may differ.",
    "all_q11_gates_remain": "HARD_FAIL",
}
AUTHORIZATION = {"world_realization": False, "benchmark": False, "qualification_fitting": False,
                 "real_train_posterior": False, "factorial_science": False, "training": False}


def build(root: Path) -> str:
    contract = L.require_launch_authority(Path(root) / "results/v79/v2_core_qualification" / L.FINAL_CONTRACT_NAME,
                                          root=root)
    if contract["finalization"]["from_accepted_draft_sha256"] != PAYLOAD_SHA256:
        raise SystemExit("STOP: canonical contract does not derive from the immutable payload")
    a = {
        "schema": "V79_V2_CORE_Q10_Q11_PAIRING_AMENDMENT_V1",
        "date": "2026-10-11",
        "status": "FROZEN_PROSPECTIVE_WORLD_REALIZATION_SEMANTICS__NO_WORLDS_GENERATED",
        "controller_comment": 6114906562,
        "rebind_controller_comment": 6115340528,
        "final_contract_sha256": L.FINAL_CONTRACT_SHA256,
        "qualification_payload_sha256": PAYLOAD_SHA256,
        "launch_gate": "scripts/v79/v79_v2_core_launch.py::require_launch_authority",
        "supersedes": SUPERSEDED,
        "worlds_generated_at_freeze": 0,
        "qualification_fits_at_freeze": 0,
        "reason": ("Q11-minus-Q10 is intended to isolate omitted operator perturbation; world-index-keyed independent "
                   "redraws would confound that contrast."),
        "paired_counterfactual": PAIRED_COUNTERFACTUAL,
        "authorization": AUTHORIZATION,
    }
    return json.dumps(a, indent=1) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("root", type=Path)
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    text = build(a.root).encode("utf-8")
    digest = hashlib.sha256(text).hexdigest()
    path = a.root / AMENDMENT_REL
    side = f"{digest}  {path.name}\n".encode("utf-8")
    if a.check:
        if not path.is_file() or path.read_bytes() != text or path.with_suffix(".sha256").read_bytes() != side:
            raise SystemExit("STOP: committed pairing amendment differs from a rebuild")
        print("pairing amendment rebuild identical:", digest)
        return
    if path.exists():
        raise SystemExit("STOP: pairing amendment already exists; never overwritten")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text)
    path.with_suffix(".sha256").write_bytes(side)
    print(json.dumps({"amendment": str(path), "sha256": digest}))


if __name__ == "__main__":
    main()
