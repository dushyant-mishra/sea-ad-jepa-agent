"""Validate the committed V79 V2_CORE realization audit-freeze bundle (controller ruling 6118398840, PR #295).

The bundle holds exact byte copies from the realized Q00–Q11 package on the locked Windows machine, plus the complete
498-file ledger. These tests use only the committed bytes and the standard library. They never open an observation
array, run a fit, or score anything.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BUNDLE = ROOT / "results" / "v79" / "v2_core_realization_audit_freeze_v1"
PACKAGE = BUNDLE / "package"
LEDGER = BUNDLE / "REALIZED_WORLDS_V1_COMPLETE_SHA256_LEDGER.tsv"
RECEIPT = BUNDLE / "V79_V2_CORE_REALIZATION_AUDIT_FREEZE_RECEIPT_V1.json"
FROZEN_AUTHORIZATION = (ROOT / "results" / "v79" / "v2_core_qualification" / "authorization"
                        / "V79_V2_CORE_WORLD_REALIZATION_AUTHORIZATION_V1.json")

SOURCE_HEAD = "cd6425b29f3fbd70b6d93351feb7c188f8b17cc8"
AUTHORIZATION_SHA = "8a2140f8d8ae721f403871de4465db5f0f8caaf3ffa1be9ee71cff7f6d96bba9"
ROOT_MANIFEST = "V79_V2_CORE_WORLD_SET_MANIFEST_V1.json"
ROOT_MANIFEST_SHA = "84949723305dc2211ebcd451b64dd9adc8518f3580d2122f5600fcf4b38de0de"
DIRECTORY_DIGEST = "40458efea66e62f3f39cb773641d29c24b80505529baa65bdab31d3975a2a286"
RUNTIME_RECEIPT_SHA = "781d880ada58dfde06c9074401a15d49cf17887460987865655837884dbf9184"
INDEX = "blinded_fit_inputs/V79_V2_CORE_BLINDED_FIT_INDEX_V1.json"
INDEX_SHA = "8ea3e0cb6637c97b3e940eac54476622bd4f790febb07abee2e8ccdeea751e40"
TOP_LEVEL = {ROOT_MANIFEST, "runtime_environment_receipt.json", "realization_authorization.json"}
OPAQUE = r"[0-9a-f]{12}"
# grammar of every file the realized package may hold: no fit, score or benchmark output can hide in it
PACKAGE_GRAMMAR = re.compile(
    r"^(?:" + "|".join([
        re.escape(ROOT_MANIFEST), r"runtime_environment_receipt\.json", r"realization_authorization\.json",
        re.escape(INDEX),
        rf"blinded_fit_inputs/{OPAQUE}/(?:manifest\.json|support\.npy|design/(?:src|donor|cls|log_lib)\.npy"
        rf"|observations/(?:train|same_donor|new_donor)/(?:observed|detected)\.npy)",
        rf"controller_truth/{OPAQUE}/(?:manifest\.json|support\.npy|design/op\.npy|truth/[a-z0-9_/]+\.npy)",
    ]) + r")$")
FIT_OR_SCORE = re.compile(r"posterior|scor(?:e|ing)|benchmark|nuts|draws|fit_result|fits?_output|qualification_fit",
                          re.IGNORECASE)


def sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path: Path) -> dict:
    return json.loads(Path(path).read_bytes().decode("utf-8"))


def ledger() -> dict[str, str]:
    out: dict[str, str] = {}
    for line in LEDGER.read_bytes().decode("utf-8").split("\n")[:-1]:
        rel, digest = line.split("\t")
        assert rel not in out
        out[rel] = digest
    return out


def committed() -> dict[str, Path]:
    return {p.relative_to(PACKAGE).as_posix(): p for p in sorted(PACKAGE.rglob("*")) if p.is_file()}


def root_manifest() -> dict:
    return load(PACKAGE / ROOT_MANIFEST)


def test_ledger_is_complete_canonical_and_reproduces_the_frozen_digest():
    raw = LEDGER.read_bytes()
    assert raw.endswith(b"\n") and b"\r" not in raw
    lines = raw.decode("utf-8").split("\n")[:-1]
    assert len(lines) == 498
    rels = [line.split("\t")[0] for line in lines]
    assert rels == sorted(rels) and len(set(rels)) == 498
    led = ledger()
    assert all(re.fullmatch(r"[0-9a-f]{64}", d) for d in led.values())
    h = hashlib.sha256()
    for rel in sorted(led):
        h.update(rel.encode("utf-8")); h.update(b"\0"); h.update(bytes.fromhex(led[rel])); h.update(b"\0")
    assert h.hexdigest() == DIRECTORY_DIGEST              # the ledger alone reproduces the world-set digest
    assert led[ROOT_MANIFEST] == ROOT_MANIFEST_SHA
    assert sha(LEDGER) == load(RECEIPT)["complete_ledger_sha256"]


def test_every_original_file_is_in_the_ledger_and_matches_the_package_grammar():
    led = ledger()
    assert all(PACKAGE_GRAMMAR.match(rel) for rel in led), [r for r in led if not PACKAGE_GRAMMAR.match(r)]
    assert sum(r.startswith("controller_truth/") for r in led) == 350
    assert sum(r.startswith("blinded_fit_inputs/") for r in led) == 145
    assert sum("/observations/" in r for r in led) == 72


def test_committed_files_are_exactly_the_selected_copies_and_match_the_ledger():
    led, files = ledger(), committed()
    expected = (TOP_LEVEL | {INDEX} | {r for r in led if r.startswith("controller_truth/")}
                | {r for r in led if re.fullmatch(rf"blinded_fit_inputs/{OPAQUE}/manifest\.json", r)})
    assert set(files) == expected and len(files) == 366
    for rel, path in files.items():
        assert sha(path) == led[rel], rel
    assert {p.name for p in BUNDLE.iterdir()} == {"package", LEDGER.name, RECEIPT.name}


def test_no_observation_or_fit_side_array_was_committed():
    files = committed()
    assert not any("/observations/" in r for r in files)
    assert not any(r.startswith("blinded_fit_inputs/") and r.endswith(".npy") for r in files)


def test_twelve_truth_and_twelve_blinded_manifests_map_one_to_one():
    files, root = committed(), root_manifest()
    blinded = {r.split("/")[1] for r in files if re.fullmatch(rf"blinded_fit_inputs/{OPAQUE}/manifest\.json", r)}
    truth = {r.split("/")[1] for r in files if re.fullmatch(rf"controller_truth/{OPAQUE}/manifest\.json", r)}
    root_ids = [w["opaque_world_id"] for w in root["worlds"]]
    index_ids = [w["opaque_world_id"] for w in load(PACKAGE / INDEX)["worlds"]]
    assert len(blinded) == len(truth) == len(set(root_ids)) == len(root_ids) == len(set(index_ids)) == 12
    assert blinded == truth == set(root_ids) == set(index_ids)
    for w in root["worlds"]:
        oid = w["opaque_world_id"]
        assert w["truth_manifest_path"] == f"controller_truth/{oid}/manifest.json"
        assert load(PACKAGE / "controller_truth" / oid / "manifest.json")["opaque_world_id"] == oid
        assert load(PACKAGE / "blinded_fit_inputs" / oid / "manifest.json")["opaque_world_id"] == oid
    assert len({w["world_name"] for w in root["worlds"]}) == 12


def test_truth_manifest_outputs_resolve_to_the_ledger_and_the_committed_bytes():
    led, files, root = ledger(), committed(), root_manifest()
    for w in root["worlds"]:
        oid = w["opaque_world_id"]
        tm_path = PACKAGE / "controller_truth" / oid / "manifest.json"
        assert sha(tm_path) == w["truth_manifest_sha256"] == led[f"controller_truth/{oid}/manifest.json"]
        outputs = load(tm_path)["generated_outputs"]
        arrays = {r for r in files if r.startswith(f"controller_truth/{oid}/") and r.endswith(".npy")}
        listed = {f"controller_truth/{oid}/{rel}" for rel in outputs}
        assert listed == arrays, oid                     # every committed truth array is bound, and nothing else
        for rel, digest in outputs.items():
            full = f"controller_truth/{oid}/{rel}"
            assert led[full] == digest == sha(files[full]), full


def test_blinded_manifest_shas_agree_with_root_index_truth_and_ledger():
    led, root = ledger(), root_manifest()
    index = {w["opaque_world_id"]: w for w in load(PACKAGE / INDEX)["worlds"]}
    for w in root["worlds"]:
        oid = w["opaque_world_id"]
        bm_path = PACKAGE / "blinded_fit_inputs" / oid / "manifest.json"
        s = sha(bm_path)
        assert s == w["fit_manifest_sha256"] == index[oid]["manifest_sha256"] == led[f"blinded_fit_inputs/{oid}/manifest.json"]
        assert load(PACKAGE / "controller_truth" / oid / "manifest.json")["blinded_fit_manifest_sha256"] == s
        for rel, digest in load(bm_path)["generated_outputs"].items():   # uncommitted arrays stay ledger-bound
            assert led[f"blinded_fit_inputs/{oid}/{rel}"] == digest


def test_root_manifest_binds_the_index_runtime_receipt_and_authorization():
    root, led = root_manifest(), ledger()
    assert sha(PACKAGE / ROOT_MANIFEST) == ROOT_MANIFEST_SHA
    assert root["blinded_fit_index_sha256"] == sha(PACKAGE / INDEX) == INDEX_SHA == led[INDEX]
    assert root["runtime_environment_receipt_sha256"] == sha(PACKAGE / "runtime_environment_receipt.json") == RUNTIME_RECEIPT_SHA
    assert root["realization_authorization_sha256"] == sha(PACKAGE / "realization_authorization.json")
    assert sha(FROZEN_AUTHORIZATION) == AUTHORIZATION_SHA
    assert load(PACKAGE / "realization_authorization.json") == load(FROZEN_AUTHORIZATION)   # canonical re-serialization
    assert (root["world_count"], root["mode"]) == (12, "QUALIFICATION_TRUTH_FREEZE")
    assert root["benchmark_run"] is False and root["qualification_fits_run"] == 0 and root["training_authorized"] is False


def test_no_fit_score_or_benchmark_outputs_exist():
    results = ROOT / "results" / "v79"
    hits = [p.relative_to(results).as_posix() for p in results.rglob("*")
            if p.is_file() and FIT_OR_SCORE.search(p.relative_to(results).as_posix())]
    assert hits == []


def test_receipt_records_the_freeze_and_keeps_every_gate_off():
    r, led, files = load(RECEIPT), ledger(), committed()
    truth = [p for p in files if p.startswith("controller_truth/")]
    assert r["schema"] == "V79_V2_CORE_REALIZATION_AUDIT_FREEZE_RECEIPT_V1"
    assert (r["source_checkout_sha"], r["authorization_receipt_sha256"], r["root_manifest_sha256"],
            r["world_set_directory_digest"], r["total_file_count"], r["world_count"], r["mode"],
            r["runtime_environment_receipt_sha256"], r["blinded_fit_index_sha256"]) == (
        SOURCE_HEAD, AUTHORIZATION_SHA, ROOT_MANIFEST_SHA, DIRECTORY_DIGEST, len(led), 12,
        "QUALIFICATION_TRUTH_FREEZE", RUNTIME_RECEIPT_SHA, INDEX_SHA)
    assert r["committed_package_file_count"] == len(files) == 366
    assert r["committed_controller_truth_file_count"] == len(truth) == 350
    assert r["committed_controller_truth_authority_array_count"] == 338
    assert r["not_committed_file_count"] == 498 - 366 and r["not_committed_observation_array_count"] == 72
    assert "not committed" in r["not_committed_note"] and "ledger" in r["not_committed_note"]
    assert r["complete_ledger_equals_post_realization_records_ledger"] is True and r["source_unchanged_after_freeze"] is True
    assert r["benchmark_run"] is False and r["qualification_fits_run"] == 0 and r["scoring_run"] is False
    assert r["real_train_posterior_run"] is False and r["factorial_science_run"] is False
    assert r["training_authorized"] is False
