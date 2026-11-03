"""Macha repair regressions for GPT #529 R01/R02 on the #528 admission wrapper (tiny fixtures only).

R01 family: inputs must resolve inside their declared root.
R02 family: a replay that fails or mismatches must refuse and leave no output.
Hold: replaying the real frozen probe is refused before any input is read.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest

from tests.v5.test_macha_specimen_qc_input_admission_v1 import A, Fixture, _csv


def _symlinks_supported() -> bool:
    with tempfile.TemporaryDirectory() as d:
        try:
            os.symlink(d, Path(d) / "probe-link", target_is_directory=True)
            return True
        except (OSError, NotImplementedError):
            return False


SYMLINKS = _symlinks_supported()
PROBE = b"import json\nprint(json.dumps({'fixture': 1}))\n"
EXPECTED = (json.dumps({"fixture": 1}) + "\n").encode()


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _rebind_receipts(fx: Fixture) -> None:
    """Recompute the freeze report, ledger and pins after a fixture edit, as an honest re-issue would."""
    fx.write(A.FREEZE_REPORT, json.dumps({"files": {"stage81a2_canonical_asset_registry.csv": fx.sha(A.REGISTRY)}}).encode())
    ledger = json.loads((fx.root / A.LEDGER).read_text(encoding="utf-8"))
    for row in ledger["rows"]:
        row["recorded_sha256"] = fx.sha(row["located_at"])
    fx.write(A.LEDGER, json.dumps(ledger).encode())
    fx.pins = {A.LEDGER: fx.sha(A.LEDGER), A.FREEZE_REPORT: fx.sha(A.FREEZE_REPORT)}


class ContainmentRepair(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "root"
        self.root.mkdir()
        self.fx = Fixture(self.root)

    def test_dotdot_path_in_receipts_is_refused_even_when_every_hash_matches(self):
        outside = self.root.parent / "outside.h5ad"
        outside.write_bytes((self.root / "data/a.h5ad").read_bytes())
        self.fx.write(A.REGISTRY, _csv([
            {"dataset_id": "HVS::a", "matrix_path_or_object": "../outside.h5ad"},
            {"dataset_id": "SEA_AD::b", "matrix_path_or_object": "data/b.h5ad"},
        ]))
        self.fx.write(A.ASSET_AUTH, _csv([
            {"matrix_id": "HVS::a", "source": "HVS", "path": "../outside.h5ad", "bytes": "10", "mtime_ns": "1",
             "sha256": _sha(outside.read_bytes())},
            {"matrix_id": "SEA_AD::b", "source": "SEA_AD", "path": "data/b.h5ad", "bytes": "200",
             "mtime_ns": str((self.root / "data/b.h5ad").stat().st_mtime_ns), "sha256": self.fx.sha("data/b.h5ad")},
        ]))
        _rebind_receipts(self.fx)
        with self.assertRaises(A.AdmissionRefused):
            self.fx.admit()

    @unittest.skipUnless(SYMLINKS, "symlink creation not permitted on this host")
    def test_symlinked_shard_directory_outside_root_is_refused(self):
        shards = self.root / A.F104 / "01_full104_metadata_adapter/FULL104_ROW_LINEAGE_SHARDS"
        moved = self.root.parent / "shards_elsewhere"
        shards.rename(moved)
        shards.symlink_to(moved, target_is_directory=True)
        with self.assertRaises(A.AdmissionRefused):
            self.fx.admit()

    @unittest.skipUnless(SYMLINKS, "symlink creation not permitted on this host")
    def test_symlinked_parent_in_the_evidence_root_is_refused(self):
        evidence = self.root.parent / "evidence"
        ledger_dir = evidence / Path(A.LEDGER).parent
        ledger_dir.parent.mkdir(parents=True)
        elsewhere = self.root.parent / "ledger_elsewhere"
        elsewhere.mkdir()
        (self.root / A.LEDGER).replace(elsewhere / Path(A.LEDGER).name)
        ledger_dir.symlink_to(elsewhere, target_is_directory=True)
        with self.assertRaises(A.AdmissionRefused):
            self.fx.admit(evidence_root=evidence)

    def test_lawful_inputs_are_still_admitted(self):
        self.assertEqual(self.fx.admit()["status"], "ADMITTED")


class ReplayRepair(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.fx = Fixture(Path(self.tmp.name))
        self.out = self.fx.root / "out.json"

    def pins(self, probe: bytes, expected: bytes) -> dict:
        self.fx.write(A.PROBE, probe)
        return dict(self.fx.pins, **{A.PROBE: _sha(probe), A.PROBE_OUTPUT: _sha(expected)})

    def assert_nothing_published(self):
        self.assertFalse(self.out.exists(), "a refused replay left an output file")
        self.assertFalse(self.out.with_name(self.out.name + ".partial").exists(), "a partial output was left")

    def test_matching_replay_publishes_output_and_says_so(self):
        receipt = A.run_probe(self.fx.root, self.out, pins=self.pins(PROBE, EXPECTED))
        self.assertEqual(receipt["status"], "ADMITTED_AND_REPLAY_MATCHED")
        self.assertEqual(self.out.read_bytes().replace(b"\r\n", b"\n"), EXPECTED)

    def test_mismatching_replay_refuses_and_publishes_nothing(self):
        with self.assertRaises(A.AdmissionRefused):
            A.run_probe(self.fx.root, self.out, pins=self.pins(PROBE, b'{"fixture": 2}\n'))
        self.assert_nothing_published()

    def test_failing_probe_refuses_and_publishes_nothing(self):
        failing = b"import sys\nprint('{\"fixture\": 1}')\nsys.exit(3)\n"
        with self.assertRaises(A.AdmissionRefused):
            A.run_probe(self.fx.root, self.out, pins=self.pins(failing, EXPECTED))
        self.assert_nothing_published()

    def test_existing_output_is_refused_before_the_probe_runs(self):
        self.out.write_bytes(b"stale")
        marker = self.fx.root / "probe-ran"
        probe = f"open({str(marker)!r}, 'w').close()\nprint('{{\"fixture\": 1}}')\n".encode()
        with self.assertRaises(A.AdmissionRefused):
            A.run_probe(self.fx.root, self.out, pins=self.pins(probe, EXPECTED))
        self.assertFalse(marker.exists(), "the probe ran although the output already existed")
        self.assertEqual(self.out.read_bytes(), b"stale")

    def test_real_frozen_probe_replay_is_held_before_any_input_is_read(self):
        missing_root = self.fx.root / "does-not-exist"
        with self.assertRaises(A.AdmissionRefused) as caught:
            A.run_probe(missing_root, self.out)
        self.assertIn("governance hold", str(caught.exception))
        self.assertEqual(A.main([str(missing_root), "--run-probe", str(self.out)]), 2)
        self.assert_nothing_published()


if __name__ == "__main__":
    unittest.main()
