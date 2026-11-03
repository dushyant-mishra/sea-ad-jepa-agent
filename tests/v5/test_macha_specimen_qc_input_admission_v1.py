"""Tiny-fixture tests for the #513 specimen/QC input admission wrapper (stdlib only, no real data)."""
from __future__ import annotations

import csv
import gzip
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "macha_specimen_qc_input_admission_v1",
    ROOT / "scripts/v5/review_probes/macha_20261103/specimen_qc_input_admission_v1.py",
)
A = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(A)

LIMIT = 64          # fixture re-hash limit: the 200-byte SEA-AD "H5AD" is stat-only
MTIME = 1_786_000_000_000_000_000


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _csv(rows: list[dict]) -> bytes:
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=list(rows[0]), lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue().encode()


class Fixture:
    """A miniature data root whose receipts match, with one HVS, one SEA_AD and one NPH52 matrix."""

    def __init__(self, root: Path, *, ledger_class: str = "EXACT_SHA_ALREADY_VERIFIED", conflict: bool = False):
        self.root = root
        shard = A.F104 + "01_full104_metadata_adapter/FULL104_ROW_LINEAGE_SHARDS/part-operator-00.csv.gz"
        meta = A.L4 + "blocks/op00/block-00000.meta.csv"
        self.write(shard, gzip.compress(_csv([
            {"source": "HVS", "matrix_id": "HVS::a"},
            {"source": "SEA_AD", "matrix_id": "SEA_AD::b"},
            {"source": "NPH52", "matrix_id": "NPH52::c"},  # never opened by the probe
        ]), mtime=0))
        self.write(meta, b"canonical_cell_id,source_library\nx,10\n")
        self.write("data/a.h5ad", b"0123456789")
        self.write("data/b.h5ad", b"B" * 200)
        os.utime(root / "data/b.h5ad", ns=(MTIME, MTIME))
        self.write(A.REGISTRY, _csv([
            {"dataset_id": "HVS::a", "matrix_path_or_object": "data/a.h5ad"},
            {"dataset_id": "SEA_AD::b", "matrix_path_or_object": "data/b.h5ad"},
        ]))
        self.write(A.FREEZE_REPORT, json.dumps(
            {"files": {"stage81a2_canonical_asset_registry.csv": self.sha(A.REGISTRY)}}).encode())
        self.write(A.BLOCK_MANIFEST, _csv([{"meta_path": "blocks/op00/block-00000.meta.csv", "meta_sha256": self.sha(meta)}]))
        self.write(A.ASSET_AUTH, _csv([
            {"matrix_id": "HVS::a", "source": "HVS", "path": "data/a.h5ad", "bytes": "10", "mtime_ns": "1",
             "sha256": self.sha("data/a.h5ad")},
            {"matrix_id": "SEA_AD::b", "source": "SEA_AD", "path": "data/b.h5ad", "bytes": "200",
             "mtime_ns": str(MTIME), "sha256": self.sha("data/b.h5ad")},
        ]))
        rows = [{"located_at": p, "classification": ledger_class if p == shard else "EXACT_SHA_ALREADY_VERIFIED",
                 "recorded_sha256": self.sha(p)} for p in (shard, A.BLOCK_MANIFEST, A.ASSET_AUTH)]
        if conflict:
            rows.append(dict(rows[1], recorded_sha256="0" * 64))
        self.write(A.LEDGER, json.dumps({"rehash_limit_bytes": LIMIT, "rows": rows}).encode())
        self.pins = {A.LEDGER: self.sha(A.LEDGER), A.FREEZE_REPORT: self.sha(A.FREEZE_REPORT)}

    def write(self, rel: str, data: bytes) -> None:
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def sha(self, rel: str) -> str:
        return _sha((self.root / rel).read_bytes())

    def admit(self, **kw):
        return A.admit(self.root, pins=self.pins, **kw)


class AdmissionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.fx = Fixture(Path(self.tmp.name))

    def refused(self, fx=None, **kw):
        with self.assertRaises(A.AdmissionRefused):
            (fx or self.fx).admit(**kw)

    def test_admits_matching_inputs_and_declares_each_scope(self):
        receipt = self.fx.admit()
        self.assertEqual(receipt["status"], "ADMITTED")
        self.assertEqual(receipt["verification_scope"]["REHASHED"], {
            "asset_registry": 1, "level4_block_manifest": 1, "asset_authentication": 1,
            "lineage_shard": 1, "level4_block_meta": 1, "h5ad_HVS": 1})
        self.assertEqual(receipt["verification_scope"]["STAT_ONLY_IDENTITY_INHERITED"], {"h5ad_SEA_AD": 1})
        self.assertEqual(receipt["matrices_admitted"], 2)  # the NPH52 matrix is never admitted or opened

    def test_refuses_a_ledger_that_does_not_match_its_pin(self):
        path = self.fx.root / A.LEDGER
        path.write_bytes(path.read_bytes() + b" ")
        self.refused()

    def test_refuses_a_registry_that_differs_from_the_freeze_report(self):
        self.fx.write(A.REGISTRY, (self.fx.root / A.REGISTRY).read_bytes() + b"X::z,data/z.h5ad\n")
        self.refused()

    def test_refuses_a_changed_lineage_shard(self):
        rel = A.F104 + "01_full104_metadata_adapter/FULL104_ROW_LINEAGE_SHARDS/part-operator-00.csv.gz"
        self.fx.write(rel, gzip.compress(_csv([{"source": "HVS", "matrix_id": "HVS::a"}]), mtime=0))
        self.refused()

    def test_refuses_an_unreceipted_extra_shard_and_a_missing_receipted_shard(self):
        extra = A.F104 + "01_full104_metadata_adapter/FULL104_ROW_LINEAGE_SHARDS/part-operator-01.csv.gz"
        self.fx.write(extra, gzip.compress(_csv([{"source": "HVS", "matrix_id": "HVS::a"}]), mtime=0))
        self.refused()
        (self.fx.root / extra).unlink()
        (self.fx.root / A.F104 / "01_full104_metadata_adapter/FULL104_ROW_LINEAGE_SHARDS/part-operator-00.csv.gz").unlink()
        self.refused()

    def test_refuses_changed_extra_or_missing_block_meta(self):
        meta = self.fx.root / A.L4 / "blocks/op00/block-00000.meta.csv"
        original = meta.read_bytes()
        meta.write_bytes(original.replace(b"10", b"11"))
        self.refused()
        meta.write_bytes(original)
        self.fx.write(A.L4 + "blocks/op00/block-00001.meta.csv", original)
        self.refused()
        (self.fx.root / A.L4 / "blocks/op00/block-00001.meta.csv").unlink()
        meta.unlink()
        self.refused()

    def test_refuses_a_changed_small_h5ad(self):
        self.fx.write("data/a.h5ad", b"9123456789")
        self.refused()

    def test_refuses_a_large_h5ad_whose_size_or_mtime_changed(self):
        self.fx.write("data/b.h5ad", b"B" * 201)
        os.utime(self.fx.root / "data/b.h5ad", ns=(MTIME, MTIME))
        self.refused()
        self.fx.write("data/b.h5ad", b"B" * 200)
        os.utime(self.fx.root / "data/b.h5ad", ns=(MTIME + 10**9, MTIME + 10**9))
        self.refused()

    def test_limit_same_size_same_mtime_rewrite_of_a_large_h5ad_is_admitted_as_stat_only(self):
        # Declared limit, not a defect: bytes above the ledger's re-hash limit are not re-hashed.
        self.fx.write("data/b.h5ad", b"C" * 200)
        os.utime(self.fx.root / "data/b.h5ad", ns=(MTIME, MTIME))
        receipt = self.fx.admit()
        self.assertEqual(receipt["verification_scope"]["STAT_ONLY_IDENTITY_INHERITED"], {"h5ad_SEA_AD": 1})
        self.assertIn("not re-hashed", A.__doc__.replace("NOT", "not"))

    def test_refuses_a_registry_path_that_is_not_the_authenticated_path(self):
        fx = self.fx
        fx.write(A.REGISTRY, _csv([
            {"dataset_id": "HVS::a", "matrix_path_or_object": "data/a_copy.h5ad"},
            {"dataset_id": "SEA_AD::b", "matrix_path_or_object": "data/b.h5ad"},
        ]))
        fx.write(A.FREEZE_REPORT, json.dumps({"files": {"stage81a2_canonical_asset_registry.csv": fx.sha(A.REGISTRY)}}).encode())
        fx.pins[A.FREEZE_REPORT] = fx.sha(A.FREEZE_REPORT)
        self.refused()

    def test_refuses_receipts_that_are_not_exact_or_conflict(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.refused(Fixture(Path(tmp), ledger_class="VERIFIED_AT_LIMITED_SCOPE"))
        with tempfile.TemporaryDirectory() as tmp:
            self.refused(Fixture(Path(tmp), conflict=True))

    def test_evidence_root_may_be_separate_from_the_data_root(self):
        with tempfile.TemporaryDirectory() as evidence:
            target = Path(evidence) / A.LEDGER
            target.parent.mkdir(parents=True)
            (self.fx.root / A.LEDGER).replace(target)
            self.refused()
            self.assertEqual(self.fx.admit(evidence_root=evidence)["status"], "ADMITTED")

    def test_run_probe_executes_only_the_pinned_probe_after_admission(self):
        probe = b"import json\nprint(json.dumps({'fixture': 1}))\n"
        self.fx.write(A.PROBE, probe)
        expected = (json.dumps({"fixture": 1}) + "\n").encode()
        pins = dict(self.fx.pins, **{A.PROBE: _sha(probe), A.PROBE_OUTPUT: _sha(expected)})
        out = self.fx.root / "out.json"
        receipt = A.run_probe(self.fx.root, out, pins=pins)
        self.assertTrue(receipt["probe_output_equals_committed_513_output"])
        self.fx.write(A.PROBE, probe + b"# edited\n")
        out.unlink()
        with self.assertRaises(A.AdmissionRefused):
            A.run_probe(self.fx.root, out, pins=pins)
        self.assertFalse(out.exists(), "an unpinned probe must not run")


if __name__ == "__main__":
    unittest.main()
