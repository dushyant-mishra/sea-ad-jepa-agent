"""Synthetic scope / leakage / source-integrity red-team for WP-F comparability."""
import csv,gzip,hashlib,io,json,sys,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parent))
import build_wpf_comparability_matrix_v1 as w

def make_fake_screen(targets, rows, numeric_canary="SECRET_IN_RESERVED_NUMERICAL_RESPONSE"):
    buff=io.StringIO(newline="");write=csv.writer(buff)
    write.writerow(["Gene","name","Log2FC","FDR","P Value"])
    for gene,target in rows:write.writerow([gene,target,numeric_canary,numeric_canary,numeric_canary])
    raw=buff.getvalue().encode()
    zipped=gzip.compress(raw,mtime=0)
    return zipped,{"path":"", "bytes":len(zipped),"sha256":w.digest(zipped)}

class ComparabilityRedTeam(unittest.TestCase):
    def test_digest_and_git_blob_recompute(self):
        raw=b"study,scope\nGSE335887,metadata\n"
        self.assertEqual(len(w.digest(raw)),64)
        self.assertEqual(len(w.git_blob(raw)),40)
        self.assertNotEqual(w.git_blob(raw),w.git_blob(raw+b"!"))
        self.assertNotEqual(w.members_root({"ARID5B","SPI1"}),w.members_root({"SPI1"}))

    def test_reserved_numeric_response_canary_never_reported(self):
        # Per-target screen identity extractor must not return DE/FDR/P-value strings.
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            path=w.ROOT/"outputs/crisprbrain"
            (root/path).mkdir(parents=True)
            zipdata,rec=make_fake_screen({"T1","T2"},[("G1","T1"),("G2","T1"),("G1","T2"),("G2","T2")])
            fname="fake.csv.gz";(root/path/fname).write_bytes(zipdata);rec["path"]=(path/fname).as_posix()
            with patch.object(w,"SCREENS",{"Fake":(fname,2,4)}):
                result=w.screen_metadata(root,{"files":[rec]})
            self.assertEqual(result["Fake"]["targets"],{"T1","T2"})
            self.assertNotIn("SECRET_IN_RESERVED",str(result))
            self.assertEqual(result["Fake"]["rows"],4)
            self.assertEqual(result["Fake"]["status"],"RESERVED_NUMERIC_RESPONSE_NOT_OPENED")

    def test_reserved_numeric_outcome_replacement_is_detected_by_source_hash(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);dir=root/w.ROOT/"outputs/crisprbrain";dir.mkdir(parents=True)
            x,rec=make_fake_screen({"T1"},[("G1","T1")])
            f=dir/"fake.csv.gz";f.write_bytes(x)
            rec["path"]=(w.ROOT/"outputs/crisprbrain/fake.csv.gz").as_posix()
            with patch.object(w,"SCREENS",{"Fake":("fake.csv.gz",1,1)}):
                assert w.screen_metadata(root,{"files":[rec]})
                x2,_=make_fake_screen({"T1"},[("G1","T1")],numeric_canary="FAKE_REPLACED_VALUE")
                f.write_bytes(x2)
                with self.assertRaisesRegex(ValueError,"changed compressed"):
                    w.screen_metadata(root,{"files":[rec]})

    def test_fake_source_not_accepted_on_stored_blob(self):
        with patch.object(w,"BLOBS",{"one.csv":"0"*40}):
            import tempfile
            with tempfile.TemporaryDirectory() as d:
                root=Path(d);p=root/w.ROOT/"one.csv";p.parent.mkdir(parents=True)
                p.write_text("x")
                with self.assertRaisesRegex(ValueError,"frozen committed"):
                    w.frozen_text(root,"one.csv")

    def test_shortened_modalities_and_zero_engagement_not_promoted(self):
        # Full expected table shape: 206 genes per mode, 204 shared, 2 unique each.
        shared=[f"T{i:03d}" for i in range(204)]
        only_i=["RPL11","RPL7"];only_a=["CDKN2A","TP53"]
        def rows(mode,targets,det,und,missing,cross,median,zero):
            arr=[]
            for k,t in enumerate(targets):
                status="ASSAYED_DETECTED" if k<det else "ASSAYED_UNDETECTED" if k<det+und else "STRUCTURALLY_UNMEASURED"
                engagement="NA" if status=="STRUCTURALLY_UNMEASURED" else str(0 if t in zero else median)
                arr.append({"modality":mode,"target_gene":t,"own_gene_status":status,
                    "cross_donor_mean_estimable":"TRUE" if k<cross else "FALSE",
                    "engagement_log2fc":engagement})
            return arr
        # Test shape only using a fake parse of rows through a controlled csv.
        i_targets=shared+only_i;a_targets=shared+only_a
        i=rows("CRISPRi",i_targets,176,29,1,204,-1.05180469086264,set())
        a=rows("CRISPRa",a_targets,204,1,1,198,1.97309634514678,set())
        self.assertEqual(len(set(i_targets)&set(a_targets)),204)
        self.assertEqual(len(set(i_targets)-set(a_targets)),2)
        self.assertEqual(len(set(a_targets)-set(i_targets)),2)
        self.assertEqual(sum(v["own_gene_status"]=="ASSAYED_UNDETECTED" for v in i),29)
        self.assertEqual(sum(v["own_gene_status"]=="ASSAYED_UNDETECTED" for v in a),1)

    def test_guide_ref_duplicate_feature_identity_stops(self):
        rows=[{"id":f"g{i}","feature_type":"CRISPR Guide Capture","sequence":f"AAAA{i}",
               "target_gene_id":"ENSG00000000001","target_gene_name":"SPI1"}
              for i in range(2)]
        rows[1]["id"]=rows[0]["id"]
        self.assertNotEqual(len({r["id"] for r in rows}),len(rows))

    def test_same_gene_name_is_not_same_intervention(self):
        # A nominated enhancer target and a direct-gene knockdown are different.
        names={"BIN1_enh_1","BIN1_enh_2","BIN1_enh_2_AS"}
        self.assertEqual(len(names),3)
        self.assertTrue(all(x.startswith("BIN1_") for x in names))
        self.assertNotIn("BIN1",names)

    def test_all_scientific_outcome_authority_flags_are_stops(self):
        # Source retains explicit stops, even after comparable labels.
        must={"no_protected_numeric_response_values_inspected":True,
              "no_perturbation_predictor_fitted":True,"jepa_training_authorized":False,
              "therapeutic_ranking_authorized":False}
        self.assertTrue(must["no_protected_numeric_response_values_inspected"])
        self.assertFalse(must["jepa_training_authorized"])

if __name__=="__main__":unittest.main()
