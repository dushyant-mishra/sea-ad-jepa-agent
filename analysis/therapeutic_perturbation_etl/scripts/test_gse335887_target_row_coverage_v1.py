import csv,gzip,hashlib,io,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from gse335887_target_row_coverage_v1 import derive,scan_pair_rows
def fake(rows):
    s=io.StringIO(newline="");w=csv.writer(s)
    w.writerow(["Gene","Log2FC","FDR","name","QC"])
    w.writerows(rows)
    raw=s.getvalue().encode();gzip_data=gzip.compress(raw,mtime=0)
    return gzip_data,hashlib.sha256(gzip_data).hexdigest(),hashlib.sha256(raw).hexdigest()
class PerTargetPublishedRowSupport(unittest.TestCase):
    def test_per_target_missing_not_zero_and_hgnc_filter(self):
        a={"T1":{"T1","G1","G2"},"T2":{"T2","G3"}}
        b={"T1":{"G1","G2"},"T2":{"T2","G3"}}
        x=derive(a,b,{"G1","G2"},expected_targets=2,expected_common=4,expected_primary=2)
        self.assertEqual(x["targets"],2)
        self.assertEqual(x["shared_screenwide_published_gene_label_count"],4)
        t={p["perturbed_target"]:p for p in x["per_target"]}
        self.assertEqual(t["T1"]["both_published_de_row_count"],2)
        self.assertFalse(t["T1"]["iMG_published_self_row"])
        self.assertEqual(t["T1"]["both_primary_HGNC_published_de_rows"],2)
        self.assertEqual(t["T1"]["missing_row_interpretation"],"UNRESOLVED_PROVIDER_FILTERING_VS_RAW_ASSAY__NEVER_ZERO_FILL")
        self.assertTrue(x["raw_assay_gene_detection_NOT_VERIFIED"])
        self.assertFalse(x["jepa_training_authorized"])
    def test_robust_digest_and_duplicate_row(self):
        rows=[["G1","SECRET_VALUE","SECRET_FDR","T1","SECRET_QC"],["G2","-7","0","T2","20"]]
        a,h,g=fake(rows)
        s,n=scan_pair_rows(a,h,g)
        self.assertEqual(n,2)
        self.assertEqual(s["T1"],{"G1"})
        self.assertNotIn("SECRET",str(s))
        with self.assertRaisesRegex(ValueError,"compressed"):scan_pair_rows(a+b"garbage",h,g)
        with self.assertRaisesRegex(ValueError,"decompressed"):scan_pair_rows(a,h,"0"*64)
        x,y,z=fake(rows+rows[:1])
        with self.assertRaisesRegex(ValueError,"duplicate"):scan_pair_rows(x,y,z)
    def test_target_and_feature_geometry(self):
        a={"T1":{"G1"},"T2":{"G2"}}
        with self.assertRaisesRegex(ValueError,"target"):derive(a,{"T1":{"G1"}},expected_targets=2,expected_common=1)
        with self.assertRaisesRegex(ValueError,"intersection"):derive(a,a,expected_targets=2,expected_common=99)
        with self.assertRaisesRegex(ValueError,"primary"):derive(a,a,{"G1"},expected_targets=2,expected_common=2,expected_primary=2)
if __name__=="__main__":unittest.main()
