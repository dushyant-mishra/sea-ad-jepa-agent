"""Fail-closed binding from audited V79 realized worlds into target discovery.

This module authenticates only the realized synthetic truth package and its world
mapping. It does not run synthetic fits, target candidates, corrected biological
replay, TD60, representation selection, Stage4, or training.
"""
from __future__ import annotations


class RealizationBindingError(ValueError):
    pass


EXACT_WORLDS = (
    "Q00_BASELINE",
    "Q01_WEAK_DONOR",
    "Q02_STRONG_DONOR",
    "Q03_WEAK_SOURCE",
    "Q04_SOURCE_ABSENT",
    "Q05_CLASS_ABSENT",
    "Q06_QUADRATIC_DEPTH_ABSENT",
    "Q07_DONOR_ABSENT",
    "Q08_SPARSE_DETECTION",
    "Q09_POSITIVE_TAIL",
    "Q10_S174_DESIGN_IMBALANCE",
    "Q11_OMITTED_OPERATOR",
)
EXPECTED = {
    "schema": "JEPA_TD_V79_REALIZATION_BINDING_V1",
    "realization_audit_pr": 297,
    "realization_audit_head": "bb8923562144a0b19a6d80795adf727986893ded",
    "realization_authority_head": "cd6425b29f3fbd70b6d93351feb7c188f8b17cc8",
    "controller_audit_comment_id": 6118626704,
    "synthetic_contract_sha256": "57e19295be824dbbb023b60a57c5039dac1f9d74e66fefe1008fc27d30fdaf26",
    "pairing_amendment_sha256": "57d7478b148cf1cab8d50a597f303c727b1a1d2d51db408ad181eab383fa4cf5",
    "generator_bundle_sha256": "119add636cffdb1db3b58c44dce6a2c5eee245f85c773e5822735537ae8dfc16",
    "root_manifest_sha256": "84949723305dc2211ebcd451b64dd9adc8518f3580d2122f5600fcf4b38de0de",
    "world_set_directory_digest_sha256": "40458efea66e62f3f39cb773641d29c24b80505529baa65bdab31d3975a2a286",
    "complete_ledger_sha256": "4e65f213d2eeb2d66b8bd7a9031eeb47eadee5801a9bd0880bd3c78dae88cd65",
    "audit_freeze_receipt_sha256": "6bd05349516a969ac7e83fc991d03d6274335b22068f8c6577f5a9de11b3f9b3",
    "blinded_fit_index_sha256": "8ea3e0cb6637c97b3e940eac54476622bd4f790febb07abee2e8ccdeea751e40",
    "seed_root": 31000000,
    "world_count": 12,
    "qualification_fits_run_at_binding": 0,
    "target_candidate_evaluations_run_at_binding": 0,
}
EXPECTED_WORLD_PINS = {
    "Q00_BASELINE": (0, "327c1c1ee188", "1fa5ce1cab4f7c3f4696b6574f2ada31d3e8f0ee7f9c1e27c1a5ae5657ae665e", "351ba0025e4296e78da5a6d57729c02e38ffcbbb1f34816c75889843d1a38dc3", "218fa16974d5c10fc79ea6a1b73f6946f013a1e15ca1531212d1b8c8f8f34236"),
    "Q01_WEAK_DONOR": (1, "f3975424edad", "2729043f518e441929da4c05394e17496dd95237b914bdb96c722ae1a4b4a782", "93637fd2255c238aaba694b6defe3bb12d70a4f7b6067107578e061f6d2fae5f", "90d1b4adfb5a3ba122af79d6a04556b4a579cc230d3b0559e9a694d0b7342974"),
    "Q02_STRONG_DONOR": (2, "4ef1ad16f002", "3d516a233ccb0c25965a6cd87e6902c659fb7b570900aab4688491b0e6af0d45", "339832557e7ba52e675deb478d24fc8fe06614bdbeea0121414a2ee66bac7436", "f73a26d750ac5f5842b532a58a788e0744c23ef3f21c0cf53d61677fa23fa86c"),
    "Q03_WEAK_SOURCE": (3, "aa187836a3b3", "432e1fc0a4e4268d03648525f68d5687290ec21003f0558a3d2f3f0008a93544", "b7b45e6c8a332d911ad167ec0d5b1ad6bed68a39870dffaddd87b9c64ba0946b", "4addf79d254cc13881648bc7f8cb3f23292d76c95e914ea80aaf8894acaf7ac2"),
    "Q04_SOURCE_ABSENT": (4, "cace57a3d450", "2f372a48b65d4ac46f9b379a833b39f7f2639a6a31827b70c60f01f149b2dd89", "d880d326f0a9b76dcc118104f59ca82f3e9c4c4c714ad60a83e1420449862465", "a0d19d5d66da345e57d946bed33c87b93e90b9cb32d01e65ef1e665986913c36"),
    "Q05_CLASS_ABSENT": (5, "eb3c7d6adfeb", "1e76833591f5d29e2430539b95da64b0abd95a8e776d8774a20b12fafbdc8aa3", "efdf606e1e84c6f8344ab659886217a614262358c63bc3bc485cdb9b68b773f8", "2e2187d6df9094c134bd15d8b8e9817845b538558555ea45207e23e60ae7ef7a"),
    "Q06_QUADRATIC_DEPTH_ABSENT": (6, "4a5e773dd737", "4b6d2e8e80e3c0cc2d5ffdc8311fdbbf5c6a96bf28e8c08bf91776e8dfa1c003", "81227f473dbc1270c15cb5279411167a5ca5474308ffcc535407120d6a5ba598", "58dee04e7908f3d06f3230824502bea8bc2467395a4d0a0586ec961940541d36"),
    "Q07_DONOR_ABSENT": (7, "d78d6e6eaf31", "35daf704d5e991297f1aee0fe6de7796d78a7b098cadd20099321773530cf7a4", "b5476e61986458c11e427adac4b334a5c0e779fdc841dc40b6a1b59ecd39890e", "cb722bb803ea465b4b5d952976aec5851b89bb03908190a6db99a2a5d23ea42e"),
    "Q08_SPARSE_DETECTION": (8, "ee384a29a9fc", "5f8000a728d6b27a5aeea49425913a1a7f36ebcd441a2f2530354f290733a94c", "4c70fcfde5ab2d0130ed480280ded4e0cb765e6b4a2346f6e923634fd29a1b75", "9581ac1bec86f02ec523f487f81a15de639958f0ba1b4c4726f2c4ab17836761"),
    "Q09_POSITIVE_TAIL": (9, "2ae1cb055fed", "ad97d0d5440725d34c63861524f8eba8e895aedd445e91c4d7dbfdc3200e7fff", "fd3df2c7c341beb1f90ecfed82076db8958e137a80dc31d04af2352592d7c4cb", "c464c99666ade8b884e1fd8ab502ada041a4f303d9bc8800b27beea2c92b2fee"),
    "Q10_S174_DESIGN_IMBALANCE": (10, "b7eecc34112f", "7d7a6c5e38e3caa49c83f1af6388243b0c438c69d278bb2a871852101a4a3302", "6f515eedcad2613a725434da92b5629f5e05d340d8d03816cd8a1b3e2afd56fe", "7cf1092d8a268df8b5b31cea86d4d560bb2cb7d47bc7484178dc47fd6c91fcaf"),
    "Q11_OMITTED_OPERATOR": (11, "aa2604cb1a3e", "6c5206aa03c36f05fd410c1d44e70e1677d8542ed4ec23a04082c9dfd7e60dcc", "b7b7152f6d2bcd65757102e2fbd3bca42d9d1381219651ad886a7504553f400f", "0fc633d443ca222d8798cf02189952d1fafffd86463b4c82507e1a100832002f"),
}
EXPECTED_TRUTH_BINDINGS = {
    "donor_sd": ["truth/detection/donor_sd.npy", "truth/positive/donor_sd.npy"],
    "donor_effects": ["truth/detection/donor_effects.npy", "truth/positive/donor_effects.npy"],
    "new_donor_truth": ["truth/new_donor/detection/donor_effects.npy", "truth/new_donor/positive/donor_effects.npy"],
    "source_contrasts": ["truth/detection/source_contrasts.npy", "truth/positive/source_contrasts.npy"],
    "class_contrasts": ["truth/detection/class_contrasts.npy", "truth/positive/class_contrasts.npy"],
    "depth2": ["truth/detection/depth2.npy", "truth/positive/depth2.npy"],
    "support": ["support.npy"],
    "detection_prevalence": ["truth/detection/prevalence.npy"],
    "sigma": ["truth/positive/sigma.npy"],
    "operator_offsets": ["truth/operator_offsets/detection.npy", "truth/operator_offsets/positive.npy"],
}
EXPECTED_PAIR = {
    "q10_world": "Q10_S174_DESIGN_IMBALANCE",
    "q11_world": "Q11_OMITTED_OPERATOR",
    "design_sha256": "bc59a2c23afba4c6c655aa993a65d762ada187ecd34d9df28612efc1e4e8c9d8",
    "support_sha256": "08744fce0264860674485724c68d77f778a696fba56141e5b4415a566c790d28",
    "non_operator_generated_outputs_identical": True,
    "q11_only_additional_truth_paths": ["truth/operator_offsets/detection.npy", "truth/operator_offsets/positive.npy"],
}
EXPECTED_BOUNDARY = {
    "realized_truth_bytes_audited": True,
    "target_discovery_truth_binding_ready": True,
    "synthetic_target_candidate_results_available": False,
    "synthetic_pass_can_establish_human_biology": False,
    "synthetic_fail_can_falsify_applicable_target_claim": True,
    "synthetic_can_rescue_real_fail": False,
    "synthetic_can_resolve_real_not_estimable": False,
}
EXPECTED_AUTHORITY_KEYS = {
    "corrected_biological_replay_authorized",
    "target_selection_authorized",
    "representation_selection_authorized",
    "td60_authorized",
    "stage4_authorized",
    "training_authorized",
}


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise RealizationBindingError(message)


def _is_sha(value: object, n: int = 64) -> bool:
    return isinstance(value, str) and len(value) == n and all(c in "0123456789abcdef" for c in value)


def validate_realization_binding(binding: dict) -> dict:
    _require(isinstance(binding, dict), "binding must be an object")
    for key, value in EXPECTED.items():
        _require(binding.get(key) == value, f"binding mismatch: {key}")
    _require(isinstance(binding.get("status"), str) and binding["status"], "status missing")

    worlds = binding.get("worlds")
    _require(isinstance(worlds, dict) and tuple(worlds) == EXACT_WORLDS, "world registry/order mismatch")
    opaque = set()
    for world in EXACT_WORLDS:
        rec = worlds[world]
        _require(isinstance(rec, dict) and set(rec) == {"index", "opaque_world_id", "truth_manifest_sha256", "scientific_truth_sha256", "fit_manifest_sha256"}, f"world record shape mismatch: {world}")
        expected = EXPECTED_WORLD_PINS[world]
        got = (rec["index"], rec["opaque_world_id"], rec["truth_manifest_sha256"], rec["scientific_truth_sha256"], rec["fit_manifest_sha256"])
        _require(got == expected, f"world pin mismatch: {world}")
        _require(isinstance(rec["opaque_world_id"], str) and len(rec["opaque_world_id"]) == 12, f"opaque id invalid: {world}")
        for field in ("truth_manifest_sha256", "scientific_truth_sha256", "fit_manifest_sha256"):
            _require(_is_sha(rec[field]), f"invalid SHA: {world}.{field}")
        _require(rec["opaque_world_id"] not in opaque, f"duplicate opaque id: {world}")
        opaque.add(rec["opaque_world_id"])

    _require(binding.get("truth_field_bindings") == EXPECTED_TRUTH_BINDINGS, "truth field binding mismatch")
    _require(binding.get("paired_counterfactual_proof") == EXPECTED_PAIR, "Q10/Q11 pair proof mismatch")
    _require(binding.get("consumption_boundary") == EXPECTED_BOUNDARY, "synthetic consumption boundary mismatch")

    authority = binding.get("authority")
    _require(isinstance(authority, dict) and set(authority) == EXPECTED_AUTHORITY_KEYS, "authority keys mismatch")
    _require(all(value is False for value in authority.values()), "realization binding cannot create authority")

    return {
        "world_count": len(worlds),
        "root_manifest_sha256": binding["root_manifest_sha256"],
        "directory_digest_sha256": binding["world_set_directory_digest_sha256"],
        "target_discovery_truth_binding_ready": binding["consumption_boundary"]["target_discovery_truth_binding_ready"],
    }


def validate_crosswalk_compatibility(binding: dict, crosswalk: dict) -> None:
    validate_realization_binding(binding)
    _require(isinstance(crosswalk, dict), "crosswalk must be an object")
    _require(crosswalk.get("synthetic_contract_sha256") == binding["synthetic_contract_sha256"], "crosswalk contract differs from realization")
    worlds = crosswalk.get("worlds")
    _require(isinstance(worlds, dict) and tuple(worlds) == EXACT_WORLDS, "crosswalk world set/order differs from realization")
    for world in EXACT_WORLDS:
        _require(worlds[world].get("index") == binding["worlds"][world]["index"], f"crosswalk index differs: {world}")
    pair = crosswalk.get("paired_counterfactual")
    _require(isinstance(pair, dict) and pair.get("worlds") == ["Q10_S174_DESIGN_IMBALANCE", "Q11_OMITTED_OPERATOR"], "crosswalk Q10/Q11 pair differs from realization")
    _require(pair.get("non_operator_truth_identical_required") is True, "crosswalk must require Q10/Q11 non-operator identity")


def expected_world_evidence_pin(binding: dict, world: str) -> dict:
    validate_realization_binding(binding)
    _require(world in EXACT_WORLDS, f"unknown world: {world}")
    rec = binding["worlds"][world]
    return {
        "world": world,
        "opaque_world_id": rec["opaque_world_id"],
        "truth_manifest_sha256": rec["truth_manifest_sha256"],
        "scientific_truth_sha256": rec["scientific_truth_sha256"],
        "fit_manifest_sha256": rec["fit_manifest_sha256"],
    }
