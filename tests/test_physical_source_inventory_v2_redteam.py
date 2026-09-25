"""Adversarial suite for physical_source_inventory_v2.

Every fixture below must make the producer exit NONZERO. The suite asserts the
exit status, not the message text, because a producer that prints a warning and
exits 0 is exactly the defect this replaces: v1 returned 0 whenever `mismatches`
was empty, even with an unverifiable asset present.

Fixtures are synthetic and isolated. They exercise the real code path — the real
producer is invoked as a subprocess against a real frozen manifest and a real
assertion registry — but never touch the authenticated store, so a test cannot
corrupt evidence.

A positive control runs first. If the healthy fixture does not exit 0, every
"correctly rejected" result below would be meaningless, so that case is asserted
explicitly rather than assumed.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRODUCER = os.path.join(
    REPO, "analysis", "therapeutic_perturbation_etl", "scripts",
    "physical_source_inventory_v2.py")


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def build_store(tmp, assets):
    """assets: {(study, name): (payload_bytes, sidecar_digest_or_None)}"""
    store = os.path.join(tmp, "store")
    for (study, name), (payload, sidecar) in assets.items():
        d = os.path.join(store, study)
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, name), "wb") as fh:
            fh.write(payload)
        if sidecar is not None:
            with open(os.path.join(d, name + ".sha256"), "w") as fh:
                fh.write("%s *%s\n" % (sidecar, name))
    return store


GZIP_A = b"\x1f\x8b" + b"\x00" * 62        # 64 bytes, gzip magic
GZIP_B = b"\x1f\x8b" + b"\x01" * 62        # same length, different bytes


def base_assets():
    return {
        ("GSEAAA", "a.gz"): (GZIP_A, sha256_bytes(GZIP_A)),
        ("GSEBBB", "b.gz"): (GZIP_B, sha256_bytes(GZIP_B)),
    }


def build_manifest(tmp, assets, roles=None):
    roles = roles or {}
    man = {
        "schema": "PERTURBATION_FROZEN_EXPECTED_16_ASSET_MANIFEST_V1",
        "frozen_on": "test", "asset_count": len(assets), "rule": "test",
        "assets": [
            {"study": s, "asset": n, "bytes": len(p),
             "sha256": sha256_bytes(p), "format": "gzip",
             "role": roles.get((s, n), "test_role")}
            for (s, n), (p, _) in assets.items()
        ],
    }
    path = os.path.join(tmp, "frozen.json")
    with open(path, "w") as fh:
        json.dump(man, fh)
    return path


def build_registry(tmp, studies, drop_field=None, drop_study=None):
    entries = {}
    for s in studies:
        if s == drop_study:
            continue
        e = {"etl_status": "PASS_DEVELOPMENT_ETL",
             "outcome_exposure": "INSPECTED_DEVELOPMENT",
             "biological_estimability": "NOT_ESTIMABLE",
             "source_reference": "test", "reviewer": "test",
             "asserted_on": "2026-09-25"}
        if drop_field and s == studies[0]:
            e[drop_field] = ""
        entries[s] = e
    path = os.path.join(tmp, "registry.json")
    with open(path, "w") as fh:
        json.dump({"registry_id": "TEST", "assertions": entries}, fh)
    return path


def run(store, manifest, registry, out):
    return subprocess.run(
        [sys.executable, PRODUCER, "--store", store,
         "--frozen-manifest", manifest, "--assertion-registry", registry,
         "--out-dir", out],
        capture_output=True, text=True).returncode


def scenario(tmp, assets, manifest_assets=None, roles=None,
             drop_field=None, drop_study=None):
    store = build_store(tmp, assets)
    man = build_manifest(tmp, manifest_assets or assets, roles)
    studies = sorted({s for s, _ in (manifest_assets or assets)})
    reg = build_registry(tmp, studies, drop_field, drop_study)
    return run(store, man, reg, os.path.join(tmp, "out"))


# --------------------------------------------------------------------------
# POSITIVE CONTROL - must pass, or every rejection below is meaningless
# --------------------------------------------------------------------------
def test_positive_control_healthy_store_exits_zero():
    with tempfile.TemporaryDirectory() as tmp:
        assert scenario(tmp, base_assets()) == 0


# --------------------------------------------------------------------------
# N1 - same-byte-length corruption (size check cannot catch this)
# --------------------------------------------------------------------------
def test_n1_same_length_corruption_rejected():
    with tempfile.TemporaryDirectory() as tmp:
        a = base_assets()
        good = a[("GSEAAA", "a.gz")][0]
        tampered = b"\x1f\x8b" + b"\x02" * 62      # identical length
        assert len(tampered) == len(good)
        manifest_assets = dict(a)
        a[("GSEAAA", "a.gz")] = (tampered, sha256_bytes(tampered))
        assert scenario(tmp, a, manifest_assets=manifest_assets) != 0


# --------------------------------------------------------------------------
# N2 - sidecar altered to disagree with the bytes
# --------------------------------------------------------------------------
def test_n2_altered_sidecar_rejected():
    with tempfile.TemporaryDirectory() as tmp:
        a = base_assets()
        payload = a[("GSEAAA", "a.gz")][0]
        a[("GSEAAA", "a.gz")] = (payload, "0" * 64)
        assert scenario(tmp, a) != 0


# --------------------------------------------------------------------------
# N4 - an expected asset is missing from the store
# --------------------------------------------------------------------------
def test_n4_missing_expected_asset_rejected():
    with tempfile.TemporaryDirectory() as tmp:
        full = base_assets()
        partial = {k: v for k, v in full.items() if k != ("GSEBBB", "b.gz")}
        assert scenario(tmp, partial, manifest_assets=full) != 0


# --------------------------------------------------------------------------
# N5 - an asset present that the frozen manifest does not expect
# --------------------------------------------------------------------------
def test_n5_unexpected_extra_asset_rejected():
    with tempfile.TemporaryDirectory() as tmp:
        expected = base_assets()
        extra = dict(expected)
        extra[("GSEAAA", "rogue.gz")] = (GZIP_A, sha256_bytes(GZIP_A))
        assert scenario(tmp, extra, manifest_assets=expected) != 0


# --------------------------------------------------------------------------
# N6 - THE v1 FAIL-OPEN: asset present and byte-correct, but no sidecar.
#      v1 reported it as "unverified" and exited 0.
# --------------------------------------------------------------------------
def test_n6_missing_sidecar_rejected_this_was_the_v1_fail_open():
    with tempfile.TemporaryDirectory() as tmp:
        a = base_assets()
        payload = a[("GSEAAA", "a.gz")][0]
        a[("GSEAAA", "a.gz")] = (payload, None)     # digest is correct, sidecar absent
        assert scenario(tmp, a) != 0


# --------------------------------------------------------------------------
# format declared in the manifest must match the magic bytes
# --------------------------------------------------------------------------
def test_format_mismatch_rejected():
    with tempfile.TemporaryDirectory() as tmp:
        a = base_assets()
        notgzip = b"NOTGZIP!" + b"\x00" * 56
        a[("GSEAAA", "a.gz")] = (notgzip, sha256_bytes(notgzip))
        man_assets = dict(a)   # manifest agrees on bytes, still declares gzip
        store = build_store(tmp, a)
        man = build_manifest(tmp, man_assets)       # format hard-coded gzip
        reg = build_registry(tmp, ["GSEAAA", "GSEBBB"])
        assert run(store, man, reg, os.path.join(tmp, "out")) != 0


# --------------------------------------------------------------------------
# assertion registry integrity - a study with no registered assertion, and a
# registered assertion missing a required provenance field, are both failures
# --------------------------------------------------------------------------
def test_missing_registered_assertion_rejected():
    with tempfile.TemporaryDirectory() as tmp:
        assert scenario(tmp, base_assets(), drop_study="GSEBBB") != 0


@pytest.mark.parametrize("field", ["source_reference", "reviewer", "asserted_on",
                                   "etl_status", "outcome_exposure"])
def test_assertion_missing_provenance_field_rejected(field):
    with tempfile.TemporaryDirectory() as tmp:
        assert scenario(tmp, base_assets(), drop_field=field) != 0


# --------------------------------------------------------------------------
# the manifest itself must be self-consistent
# --------------------------------------------------------------------------
def test_inconsistent_frozen_manifest_rejected():
    with tempfile.TemporaryDirectory() as tmp:
        a = base_assets()
        store = build_store(tmp, a)
        man_path = build_manifest(tmp, a)
        with open(man_path) as fh:
            man = json.load(fh)
        man["asset_count"] = 99                      # lies about its own size
        with open(man_path, "w") as fh:
            json.dump(man, fh)
        reg = build_registry(tmp, ["GSEAAA", "GSEBBB"])
        assert run(store, man_path, reg, os.path.join(tmp, "out")) != 0
