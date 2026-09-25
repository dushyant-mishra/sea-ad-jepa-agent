"""Metadata-only adversaries against authenticated real committed target/guide tables."""
import contextlib,csv,gzip,hashlib,importlib.util,io,json,shutil,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"analysis/therapeutic_perturbation_etl/scripts/build_cross_study_comparability_matrix_v2.py"
spec=importlib.util.spec_from_file_location("comparability_test_only",SCRIPT)
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
BASE=ROOT/"analysis/therapeutic_perturbation_etl"
SOURCES={
 "gse335887_ref":BASE/"reference/gse335887/GSE335887_itf_feature_reference.csv.gz",
 "gse178317_lib":BASE/"reference/GSE178317_sgrna_library_suppl_table5.csv",
 "gse301119_crispri":BASE/"evidence/gse301119_rawpb_v1/CRISPRi_guide_donor_meta.csv",
 "gse301119_crispra":BASE/"evidence/gse301119_rawpb_v1/CRISPRa_guide_donor_meta.csv",
 "gse311359_identity":BASE/"evidence/gse311359/GSE311359_perturbation_identity.csv",
 "gse293118_identity":BASE/"evidence/gse293118/GSE293118_perturbation_identity.csv",
}
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
class ComparabilityMetadataRedTeam(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.work=Path(self.tmp.name)
        self.files={}
        for key,src in SOURCES.items():
            path=self.work/src.name
            shutil.copyfile(src,path)
            self.files[key]=str(path)
        self.expected=dict(mod.PINNED_METADATA_SHA256)
    def load(self):
        with patch.object(mod,"PINNED_METADATA_SHA256",self.expected):
            mod.authenticate_metadata(self.files)
            return mod.load_targets(self.files)
    def reapprove_mutated_source_test_only(self,key):
        # Synthetic negative test: emulate a producer rehashing its own changed
        # source. The semantic guards must reject even when digests are resealed.
        self.expected[key]=digest(Path(self.files[key]))
    def edit_csv(self,key,modify):
        p=Path(self.files[key])
        with p.open(newline="",encoding="utf-8") as f:
            r=csv.DictReader(f);head=r.fieldnames;rows=list(r)
        modify(rows)
        with p.open("w",newline="",encoding="utf-8") as f:
            w=csv.DictWriter(f,fieldnames=head);w.writeheader();w.writerows(rows)
    def edit_guides(self,modify):
        key="gse335887_ref";p=Path(self.files[key])
        with gzip.open(p,"rt",newline="",encoding="utf-8") as f:
            r=csv.DictReader(f);head=r.fieldnames;rows=list(r)
        guides=[r for r in rows if r["feature_type"]=="CRISPR Guide Capture"]
        self.assertEqual(len(guides),65)
        modify(guides)
        with gzip.open(p,"wt",newline="",encoding="utf-8") as f:
            w=csv.DictWriter(f,fieldnames=head);w.writeheader();w.writerows(rows)
        self.reapprove_mutated_source_test_only(key)
    def test_real_source_positive_all_expected_censuses(self):
        self.load()
        d=self.load()
        self.assertEqual(len(d["GSE335887"]),30)
        self.assertEqual(len(d["GSE293118"]),6)
        self.assertEqual(len(d["GSE301119"]),208)
        self.assertEqual(len(d["_gse301119_per_modality"]["CRISPRi"] & d["_gse301119_per_modality"]["CRISPRa"]),204)
        self.assertEqual(d["GSE178317"]&d["GSE301119"],{"CSF1R","CSF2RA","CSF2RB","TGFBR1","TGFBR2"})
        self.assertEqual(d["GSE335887"]&d["GSE178317"],set())
    def test_same_size_change_with_self_resealed_sidecar_still_rejected(self):
        key="gse178317_lib";p=Path(self.files[key]);data=p.read_bytes()
        changed=data.replace(b"AARS,",b"AXRS,",1)
        self.assertEqual(len(changed),len(data));self.assertNotEqual(changed,data)
        p.write_bytes(changed)
        Path(str(p)+".sha256").write_text(digest(p))
        with self.assertRaisesRegex(ValueError,"STOP_AUTHENTICATED_METADATA_SHA_MISMATCH"):self.load()
    def test_duplicate_guide_id_rejected_after_synthetic_rehash(self):
        def dup(gs):gs[1]["id"]=gs[0]["id"]
        self.edit_guides(dup)
        with self.assertRaisesRegex(ValueError,"STOP_GSE335887_GUIDE_REFERENCE_INTEGRITY"):self.load()
    def test_missing_ntc_rejected_after_synthetic_rehash(self):
        def no_ntc(gs):
            v=next(x for x in gs if x["target_gene_name"]=="Non-Targeting")
            v["target_gene_name"]="MISSING_NTC"
        self.edit_guides(no_ntc)
        with self.assertRaisesRegex(ValueError,"STOP_GSE335887_GUIDE_REFERENCE_INTEGRITY"):self.load()
    def test_target_ensembl_collision_rejected(self):
        def collide(gs):
            t=list(dict.fromkeys(x["target_gene_name"] for x in gs if x["target_gene_name"]!="Non-Targeting"))
            a=next(x for x in gs if x["target_gene_name"]==t[0])
            for x in gs:
                if x["target_gene_name"]==t[1]:x["target_gene_id"]=a["target_gene_id"]
        self.edit_guides(collide)
        with self.assertRaisesRegex(ValueError,"STOP_GSE335887_TARGET_ENSG_COLLISION"):self.load()
    def test_donor_guide_join_mismatch_rejected(self):
        key="gse301119_crispri"
        def bad(rows):rows[0]["guide_donor"]="NOT_A_REAL_JOIN||D2"
        self.edit_csv(key,bad);self.reapprove_mutated_source_test_only(key)
        with self.assertRaisesRegex(ValueError,"STOP_GSE301119_GUIDE_DONOR_JOIN"):self.load()
    def test_duplicate_guide_donor_rejected(self):
        key="gse301119_crispri"
        self.edit_csv(key,lambda rows:rows.append(dict(rows[0])))
        self.reapprove_mutated_source_test_only(key)
        with self.assertRaisesRegex(ValueError,"STOP_GSE301119_DUPLICATE_GUIDE_DONOR"):self.load()
    def test_missing_donor_matched_controls_rejected(self):
        key="gse301119_crispra"
        self.edit_csv(key,lambda rows:rows.__setitem__(slice(None),[r for r in rows if not (r["crispr"]=="NT" and r["donor"]=="D2")]))
        self.reapprove_mutated_source_test_only(key)
        with self.assertRaisesRegex(ValueError,"STOP_GSE301119_MISSING_DONOR_MATCHED_CONTROL"):self.load()
    def test_reconciled_exposure_never_promotes_training(self):
        j=json.loads((BASE/"evidence/STUDY_SCIENTIFIC_READINESS_ASSERTIONS_VNEXT.json").read_text())
        self.assertFalse(j["_reconciliation"]["training_authorized"])
        self.assertFalse(j["_reconciliation"]["code_test_authority"])
        self.assertIn("EFFECTS_EXECUTED",j["GSE240609"]["outcome_exposure"])
        self.assertEqual(j["GSE311359"]["etl_status"],"STOP_PENDING_PHYSICAL_ID_KEYED_V2_REBUILD")
        self.assertIn("CODE_UNTESTED",j["GSE301119"]["code_validation_status"])
if __name__=="__main__":unittest.main()
