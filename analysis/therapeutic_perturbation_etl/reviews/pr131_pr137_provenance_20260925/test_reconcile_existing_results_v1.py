"""Synthetic/adversarial checks, not a physical replay of deposited CRISPRbrain screens."""
import csv
import hashlib
import io
import json
import tempfile
import unittest
from pathlib import Path
import reconcile_existing_results_v1 as m


def fixture_science():
    old = {k: {} for k in m.EXACT_SCIENCE_SECTIONS}
    old["S3_concordance"] = {"n_sig_both": 3, "pooled_pearson_log2fc": 0.0723,
                             "jointly_significant_rows_by_target": {"A": 2, "B": 1}}
    new = json.loads(json.dumps(old))
    new["S3_concordance"].update({
        "hypergeom_caveat": "NOT independent biological inference",
        "n_jointly_significant_rows": 3,
        "n_distinct_readout_genes_among_jointly_significant": 3,
        "n_distinct_targets_among_jointly_significant": 2,
        "joint_count_unit": "target x gene pairs",
    })
    return old, new


def make_fixture(base: Path, *, malicious=False):
    o = base / "original"
    c = base / "clean"
    p = m.PRODUCER
    old, new = fixture_science()
    output_rel = m.ROOT / "evidence/crisprbrain_reliability"
    for root, receipt, script in ((o, old, b"old committed script"),
                                  (c, new, b"clean executed script")):
        (root / p).parent.mkdir(parents=True)
        (root / p).write_bytes(script)
        outputs = []
        for name in sorted(m.EXPECTED_OUTPUT_NAMES):
            path = root / output_rel / name
            path.parent.mkdir(parents=True, exist_ok=True)
            contents = ("name,Gene\nA,g1\nA,g2\nB,g3\n"
                        if name == "jointly_significant_rows.csv"
                        else "field,value\nx,1\n")
            path.write_text(contents)
            outputs.append({"path": (output_rel / name).as_posix(),
                            "sha256": m.sha(path.read_bytes()),
                            "rows": 3 if name == "jointly_significant_rows.csv" else 1})
        receipt.update({
            "schema": "CRISPRBRAIN_SCREEN_RELIABILITY_V1",
            "status": "COMPLETE",
            "git_head": "1" * 40,
            "git_dirty": root == o,
            "producer_sha256": "f" * 64 if root == o else m.sha(script),
            "outputs": outputs,
        })
        (root / m.RECEIPT).write_text(json.dumps(receipt), encoding="utf8")
    if malicious:
        f = c / output_rel / "per_target_concordance.csv"
        f.write_text("field,value\nx,FAKE\n")
    return o, c


class ReconciliationFixtures(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def test_01_complete_synthetic_positive_without_git_authority(self):
        o, c = make_fixture(self.root)
        result = m.reconcile(o, c, verify_git=False)
        self.assertEqual(result["status"], "PASS_EXISTING_OUTPUT_BYTES_AND_COMMON_SCIENCE_MATCH")
        self.assertFalse(result["clean_source_at_declared_anchor_verified"])
        self.assertEqual(result["joint_table_crosscheck"]["distinct_targets"], 2)
        self.assertFalse(result["raw_deposited_screens_reexecuted_by_this_script"])

    def test_02_numeric_science_mutation_stops(self):
        o, c = make_fixture(self.root)
        path = c / m.RECEIPT
        rec = json.loads(path.read_text())
        rec["S3_concordance"]["pooled_pearson_log2fc"] += .01
        path.write_text(json.dumps(rec))
        with self.assertRaisesRegex(ValueError, "continuous-concordance field changed"):
            m.reconcile(o, c, verify_git=False)

    def test_03_new_scientific_annotation_not_allowlisted_stops(self):
        old, new = fixture_science()
        new["S3_concordance"]["mysterious_new_p"] = 0.99
        with self.assertRaisesRegex(ValueError, "unexpected or missing"):
            m.compare_science(old, new)

    def test_04_deleted_science_field_stops(self):
        old, new = fixture_science()
        del new["S3_concordance"]["pooled_pearson_log2fc"]
        with self.assertRaises(ValueError):
            m.compare_science(old, new)

    def test_05_tampered_committed_csv_stops(self):
        o, c = make_fixture(self.root, malicious=True)
        with self.assertRaisesRegex(ValueError, "committed output SHA-256"):
            m.reconcile(o, c, verify_git=False)

    def test_06_forged_internal_csv_hash_with_new_content_stops(self):
        o, c = make_fixture(self.root, malicious=True)
        receipt = c / m.RECEIPT
        rec = json.loads(receipt.read_text())
        for item in rec["outputs"]:
            if item["path"].endswith("per_target_concordance.csv"):
                item["sha256"] = m.sha((c / item["path"]).read_bytes())
        receipt.write_text(json.dumps(rec))
        with self.assertRaisesRegex(ValueError, "scientific CSV changed"):
            m.reconcile(o, c, verify_git=False)

    def test_07_path_traversal_stops(self):
        o, c = make_fixture(self.root)
        rec = json.loads((c / m.RECEIPT).read_text())
        rec["outputs"][0]["path"] = "../outside.csv"
        with self.assertRaisesRegex(ValueError, "output path escapes"):
            m.normalize_outputs(c, rec)

    def test_08_joint_row_vs_unique_gene_false_claim_stops(self):
        old, new = fixture_science()
        new["S3_concordance"]["n_distinct_readout_genes_among_jointly_significant"] = 4
        with self.assertRaisesRegex(ValueError, "annotation disagrees"):
            m.validate_joint_table(b"name,Gene\nA,g1\nA,g2\nB,g3\n", new)

    def test_09_dirty_origin_must_stay_dirty(self):
        o, c = make_fixture(self.root)
        rec_path = o / m.RECEIPT
        rec = json.loads(rec_path.read_text())
        rec["git_dirty"] = False
        rec_path.write_text(json.dumps(rec))
        with self.assertRaisesRegex(ValueError, "dirty/clean provenance"):
            m.reconcile(o, c, verify_git=False)

    def test_10_clean_producer_digest_must_match_exact_bytes(self):
        o, c = make_fixture(self.root)
        rec_path = c / m.RECEIPT
        rec = json.loads(rec_path.read_text())
        rec["producer_sha256"] = "e" * 64
        rec_path.write_text(json.dumps(rec))
        with self.assertRaisesRegex(ValueError, "clean current producer differs"):
            m.reconcile(o, c, verify_git=False)


if __name__ == "__main__":
    unittest.main()
