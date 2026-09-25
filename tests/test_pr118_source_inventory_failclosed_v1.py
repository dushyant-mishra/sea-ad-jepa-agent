"""Adversarial tests of PR118 physical inventory: independent expected roots vs mutable sidecars."""
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = (Path(__file__).resolve().parents[1] /
          "analysis/therapeutic_perturbation_etl/scripts/physical_source_inventory_vnext.py")


class PhysicalInventoryFailClosed(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.store = self.root / "source"
        self.store.mkdir()
        self.a = self.store / "GSE_A"
        self.a.mkdir()
        self.b = self.store / "GSE_B"
        self.b.mkdir()
        self.content = {"GSE_A/a.tar": b"ustar synthetic a",
                        "GSE_B/b.tar": b"ustar synthetic b"}
        for key, data in self.content.items():
            f = self.store / key
            f.write_bytes(data)
            (f.parent / (f.name + ".sha256")).write_text(hashlib.sha256(data).hexdigest()+"\n")
        assets = [{"study":k.split("/")[0], "asset":k.split("/")[1],
                   "bytes":len(v), "sha256":hashlib.sha256(v).hexdigest()}
                  for k,v in sorted(self.content.items())]
        self.expected = self.root / "expected.json"
        self.receipt = {"schema":"PERTURBATION_EXPECTED_SOURCE_ROOTS_REVIEW_V1",
                        "total_primary_bytes":sum(x["bytes"] for x in assets),
                        "assets":assets,"review_status":"TEST_ONLY"}
        self.expected.write_text(json.dumps(self.receipt))
        self.readiness = self.root / "readiness.json"
        self.readiness.write_text("{}")
        self.out = self.root / "out"

    def invoke(self, expected_success, reason=None):
        cp = subprocess.run([sys.executable, str(SCRIPT), "--store", str(self.store),
              "--out-dir", str(self.out), "--readiness", str(self.readiness),
              "--expected-manifest", str(self.expected)],
              capture_output=True, text=True, timeout=12)
        if expected_success:
            self.assertEqual(cp.returncode,0, cp.stdout+"\n"+cp.stderr)
            out = json.loads((self.out/"STUDY_SOURCE_INVENTORY_RECEIPT_VNEXT.json").read_text())
            self.assertEqual(out["primary_assets"],2)
            self.assertEqual(out["authenticity_summary"]["verified"],2)
            self.assertTrue(out["readiness_assertions_are_self_reported_not_reconciled"])
        else:
            self.assertNotEqual(cp.returncode,0, cp.stdout+"\n"+cp.stderr)
            self.assertIn(reason,cp.stderr+cp.stdout)
            self.assertFalse((self.out/"STUDY_SOURCE_INVENTORY_RECEIPT_VNEXT.json").exists())

    def test_positive_and_no_overwrite(self):
        self.invoke(True)
        self.invoke(False,"STOP_OUTPUT_EXISTS")

    def test_missing_sidecar_rejected(self):
        (self.a/"a.tar.sha256").unlink()
        self.invoke(False,"no_sidecar")

    def test_same_size_tamper_even_with_resealed_sidecar(self):
        f = self.a/"a.tar"
        altered = f.read_bytes().replace(b"a", b"x")
        self.assertEqual(len(altered),len(f.read_bytes()))
        f.write_bytes(altered)
        (self.a/"a.tar.sha256").write_text(hashlib.sha256(altered).hexdigest()+"\n")
        self.invoke(False,"REVIEWED_SOURCE_ROOT_MISMATCH")

    def test_missing_expected_file(self):
        (self.b/"b.tar").unlink()
        self.invoke(False,"missing")

    def test_extra_source_rejected(self):
        f = self.a/"extra.tar"
        f.write_bytes(b"extra bytes")
        (self.a/"extra.tar.sha256").write_text(hashlib.sha256(f.read_bytes()).hexdigest()+"\n")
        self.invoke(False,"unexpected")

    def test_expected_manifest_duplicate_rejected(self):
        self.receipt["assets"].append(dict(self.receipt["assets"][0]))
        self.expected.write_text(json.dumps(self.receipt))
        self.invoke(False,"STOP_DUPLICATE_OR_UNSAFE_EXPECTED_SOURCE")

    def test_unreviewed_study_directory_rejected(self):
        (self.store/"GSE_EXTRA").mkdir()
        self.invoke(False,"unexpected_studies")

    def test_output_inside_source_rejected(self):
        self.out = self.a / "results"
        self.invoke(False,"STOP_OUTPUT_INSIDE_SOURCE_STORE")

    def test_manifest_missing_fails(self):
        self.expected.unlink()
        self.invoke(False,"No such file")

    def test_source_sidecar_wrong_digest_fails(self):
        (self.a/"a.tar.sha256").write_text("0"*64+"\n")
        self.invoke(False,"no_sidecar") if False else self.invoke(False,"mismatch")


if __name__ == "__main__":
    unittest.main()
