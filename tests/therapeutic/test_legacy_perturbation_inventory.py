"""Synthetic-only fail-closed tests. No protected or expression data is read."""
import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts" / "therapeutic"))
from audit_legacy_perturbation_inventory import AuditError, audit, inside_existing_root


class MetadataAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.results = self.root / "results" / "v4"
        self.results.mkdir(parents=True)
        self.rel = "data/external/v4/perturbation/GSE301119/exemplar.rds"
        self.file = self.root / self.rel
        (self.file.parent).mkdir(parents=True)
        self.file.write_bytes(b"synthetic test fixture only")
        import hashlib
        self.digest = hashlib.sha256(self.file.read_bytes()).hexdigest()
        self.acq = {"processed_asset_count": 1, "study_count": 1,
                    "all_processed_assets_verified": True, "model_trained": False,
                    "perturbation_controller_trained": False, "pathology_values_used": False,
                    "raw_sequencing_downloaded": False, "rds_full_object_audit_count": 1}
        self.hashrow = {"accession": "GSE301119", "asset_id": "test_asset", "path": self.rel,
                        "size_bytes": str(self.file.stat().st_size), "sha256": self.digest,
                        "format_open_pass": "True"}
        self.readyrow = {"dataset_id": "test_asset", "study_id": "GSE301119", "source_path": self.rel,
                         "perturbation_training_ready": "False", "readiness_blockers": "unresolved_feature_ids"}
        self.seuratrow = {"accession": "GSE301119", "source_path": self.rel,
                          "full_object_audit_pass": "TRUE", "expression_matrix_materialized": "FALSE"}
        self.save()

    def csv_out(self, name, fields, rows):
        with (self.results / name).open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)

    def save(self):
        (self.results / "stage81a1c_p_acquisition_report.json").write_text(json.dumps(self.acq))
        self.csv_out("stage81a1c_p_download_hashes.csv", list(self.hashrow), [self.hashrow])
        self.csv_out("pre_stage81a2_perturbation_readiness_registry.csv", list(self.readyrow), [self.readyrow])
        self.csv_out("stage81a1c_p_seurat_object_audit.csv", list(self.seuratrow), [self.seuratrow])

    def test_metadata_only_never_implies_present_or_training_ready(self):
        result = audit(self.root)
        self.assertEqual(result["historical_asset_count"], 1)
        self.assertEqual(result["assets"][0]["physical_state"], "NOT_INSPECTED")
        self.assertFalse(result["assets"][0]["perturbation_training_authorized"])

    def test_size_probe_is_not_sha_verification(self):
        self.assertEqual(audit(self.root, "size")["assets"][0]["physical_state"],
                         "SIZE_ONLY_NOT_AUTHENTICATED")

    def test_local_sha_can_authenticate_exact_fixture(self):
        self.assertEqual(audit(self.root, "sha256")["assets"][0]["physical_state"],
                         "SHA256_AUTHENTICATED_ON_THIS_MACHINE")

    def test_missing_local_is_reported_without_fake_pass(self):
        self.file.unlink()
        self.assertEqual(audit(self.root, "sha256")["assets"][0]["physical_state"],
                         "MISSING_ON_THIS_MACHINE")

    def test_changed_same_size_file_rejected(self):
        self.file.write_bytes(b"S" + self.file.read_bytes()[1:])
        with self.assertRaisesRegex(AuditError, "SHA-256 mismatch"):
            audit(self.root, "sha256")

    def test_duplicate_acquisition_id_fails(self):
        self.csv_out("stage81a1c_p_download_hashes.csv", list(self.hashrow), [self.hashrow, self.hashrow])
        with self.assertRaisesRegex(AuditError, "Duplicate asset_id"):
            audit(self.root)

    def test_renamed_source_path_fails(self):
        self.readyrow["source_path"] += "_other"
        self.save()
        with self.assertRaisesRegex(AuditError, "Path identity"):
            audit(self.root)

    def test_unearned_training_flag_fails(self):
        self.readyrow["perturbation_training_ready"] = "True"
        self.save()
        with self.assertRaisesRegex(AuditError, "Changed historical readiness"):
            audit(self.root)

    def test_missing_blocker_fails(self):
        self.readyrow["readiness_blockers"] = ""
        self.save()
        with self.assertRaisesRegex(AuditError, "Missing readiness blocker"):
            audit(self.root)

    def test_unsafe_paths_rejected(self):
        for path in ("../outside/file", "/data/external/v4/perturbation/GSE1/a", 
                     "data/external/v4/perturbation/../../protected/foo"):
            self.assertFalse(inside_existing_root(path))
        self.hashrow["path"] = "../../pathology/fixture"
        self.readyrow["source_path"] = self.hashrow["path"]
        self.save()
        with self.assertRaisesRegex(AuditError, "Unsafe/foreign"):
            audit(self.root)

    def test_asset_symlink_to_other_data_family_fails(self):
        target = self.root / "data" / "protected" / "not_a_perturbation_asset"
        target.parent.mkdir(parents=True)
        target.write_bytes(b"synthetic test fixture only")
        self.file.unlink()
        self.file.symlink_to(target)
        with self.assertRaisesRegex(AuditError, "escapes perturbation root"):
            audit(self.root, "sha256")

    def test_seurat_schema_audit_false_fails(self):
        self.seuratrow["expression_matrix_materialized"] = "TRUE"
        self.save()
        with self.assertRaisesRegex(AuditError, "Seurat schema"):
            audit(self.root)

    def test_manifest_tamper_fails(self):
        self.acq["processed_asset_count"] = 2
        self.save()
        with self.assertRaisesRegex(AuditError, "count disagrees"):
            audit(self.root)


if __name__ == "__main__":
    unittest.main()
