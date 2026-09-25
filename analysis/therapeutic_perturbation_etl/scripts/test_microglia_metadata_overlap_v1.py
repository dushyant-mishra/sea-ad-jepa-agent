"""Fail-closed tests: no numeric outcome ever enters the metadata receipt."""
import csv,gzip,hashlib,io,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from microglia_metadata_overlap_v1 import scan_identifiers,compare_screen_metadata
def fixture(rows,header=None):
    buf=io.StringIO(newline="");w=csv.writer(buf)
    w.writerow(header or ["Gene","Log2FC","FDR","name","Log2CPM"]);w.writerows(rows)
    csvbytes=buf.getvalue().encode();raw=gzip.compress(csvbytes)
    return raw,hashlib.sha256(raw).hexdigest(),hashlib.sha256(csvbytes).hexdigest()
class MetadataFirewall(unittest.TestCase):
    def test_numeric_canary_never_returned(self):
        raw,compressed,plain=fixture([["G1","SECRET_EFFECT","SECRET_FDR","T1","SECRET_EXPRESSION"],["G2","-100","0.001","T2","20"]])
        out=scan_identifiers(raw,compressed,plain)
        self.assertEqual(out["targets"],{"T1","T2"})
        self.assertEqual(out["features"],{"G1","G2"})
        self.assertNotIn("SECRET",str(out))
    def test_global_feature_presence_is_not_same_as_target_self_row(self):
        raw,compressed,plain=fixture([["T1","0","0.1","T2","2"],["G1","0","0.1","T1","3"],["T1","0","0.1","T1","3"]])
        j=scan_identifiers(raw,compressed,plain)
        self.assertIn("T1",j["features"])
        self.assertIn("T1",j["own_target_rows"])
        self.assertNotIn("T2",j["own_target_rows"])
        self.assertEqual(j["targets"],{"T1","T2"})
    def test_both_digests_and_size_change(self):
        raw,compressed,plain=fixture([["G1","0","0.1","T1","8"]])
        alternate,_,_=fixture([["G1","1","0.1","T1","8"]])
        with self.assertRaisesRegex(ValueError,"compressed source"):
            scan_identifiers(alternate,compressed,plain)
        with self.assertRaisesRegex(ValueError,"uncompressed source"):
            scan_identifiers(raw,compressed,"0"*64)
        with self.assertRaisesRegex(ValueError,"compressed source"):
            scan_identifiers(raw+b"x",compressed,plain)
    def test_missing_duplicate_and_malformed_identifiers(self):
        for rows,header in [([["G1","T1","T1"]],["Gene","name","name"]),([["","T1"]],["Gene","name"]),([["G1"]],["Gene","name"])]:
            raw,compressed,plain=fixture(rows,header)
            with self.assertRaises(ValueError):scan_identifiers(raw,compressed,plain)
    def test_cross_modality_is_never_gene_overlap(self):
        make=lambda mode,t,f:{"modality":mode,"targets":set(t),"features":set(f)}
        pairs=compare_screen_metadata({"a":make("RNA",["T1","T2"],["G1","G2"]),
          "b":make("RNA",["T2"],["G2"]),"c":make("PROTEIN",["T2"],["G2"])})
        self.assertEqual(len(pairs),3)
        self.assertEqual(next(p for p in pairs if p["screen_a"]=="a" and p["screen_b"]=="b")["shared_measured_feature_count"],1)
        self.assertTrue(all(p["shared_measured_feature_count"] is None for p in pairs if not p["same_outcome_modality"]))
        self.assertTrue(all(p["biological_preparation_independence"]=="NOT_VERIFIED" for p in pairs))
if __name__=="__main__":unittest.main()
