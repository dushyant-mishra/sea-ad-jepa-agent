import copy,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from freeze_verified_microglia_hgnc_v1 import (
    PARENT_SHA,EXPECTED_SOURCE_SHAS,freeze_verified_report,
)
def receipt():
    x=lambda k:{"ensembl":f"ENSG{k:011d}","hgnc_id":f"HGNC:{k}"}
    return {"schema":"HGNC_2026Q3_MICROGLIA_31TARGET_METADATA_CROSSWALK_V1",
        "HGNC_download_sha256":PARENT_SHA,"HGNC_download_bytes":16913890,
        "response_values_inspected":False,"training_authorized":False,
        "screens":{k:dict(v) for k,v in EXPECTED_SOURCE_SHAS.items()},
        "crosswalk":{"collision_free_shared_feature_map":{"G1":x(1),"G2":x(2)},
                     "target_primary_map":{"G1":x(1),"T2":x(3)},
                     "labels_absent_from_primary_release":["UNKNOWN"],
                     "labels_ambiguous_primary":[],"ensembl_collisions":{},
                     "exact_primary_feature_labels_mapped_collision_free":2,
                     "exact_primary_targets_mapped":2,
                     "common_target_count":2,"common_literal_feature_count":3}}
class FreezeContractTests(unittest.TestCase):
    def test_freezes_existing_contract_and_retains_exclusion(self):
        x=freeze_verified_report(receipt(),require_real_census=False)
        self.assertEqual(x["annotated_symbol_count"],3)
        self.assertEqual(x["unresolved_shared_feature_labels"],["UNKNOWN"])
        self.assertFalse(x["full104_alignment_authorized"])
        self.assertFalse(x["assay_detection_masks_verified"])
        self.assertEqual(len(x["frozen_annotation_contract_sha256"]),64)
        self.assertEqual(x["frozen_annotation_body"]["entries"][0]["mapping_status"],"PRIMARY_ID")
    def test_wrong_source_and_forced_outcomes_fail(self):
        for edit in [("HGNC_download_sha256","0"*64),
                     ("HGNC_download_bytes",1),
                     ("response_values_inspected",True),
                     ("training_authorized",True)]:
            r=receipt();r[edit[0]]=edit[1]
            with self.assertRaises(ValueError):freeze_verified_report(r,require_real_census=False)
        r=receipt();r["screens"]["day12_iTF_CROP_RNA"]["source_compressed_sha256"]="1"*64
        with self.assertRaises(ValueError):freeze_verified_report(r,require_real_census=False)
        r=receipt();r["screens"]["day12_iTF_CROP_RNA"]["source_uncompressed_sha256"]="2"*64
        with self.assertRaises(ValueError):freeze_verified_report(r,require_real_census=False)
    def test_malformed_missing_or_duplicate_canonical_fail(self):
        r=receipt();r["crosswalk"]["collision_free_shared_feature_map"]["G2"]["ensembl"]="ENSG00000000001"
        with self.assertRaises(ValueError):freeze_verified_report(r,require_real_census=False)
        r=receipt();r["crosswalk"]["labels_absent_from_primary_release"]=[]
        with self.assertRaises(ValueError):freeze_verified_report(r,require_real_census=False)
        r=receipt();r["crosswalk"]["target_primary_map"]["G1"]["ensembl"]="ENSG00000000003"
        with self.assertRaises(ValueError):freeze_verified_report(r,require_real_census=False)
    def test_no_fake_production_geometry(self):
        with self.assertRaises(ValueError):freeze_verified_report(receipt(),require_real_census=True)
if __name__=="__main__":unittest.main()
