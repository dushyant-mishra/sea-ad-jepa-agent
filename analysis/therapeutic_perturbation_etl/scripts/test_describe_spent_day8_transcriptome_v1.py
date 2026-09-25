import csv,gzip,hashlib,io,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from describe_spent_day8_transcriptome_v1 import load,assess
def fixture(rows):
    o=io.StringIO(newline="");w=csv.writer(o);w.writerow(["Gene","name","Log2FC","FDR"]);w.writerows(rows)
    raw=o.getvalue().encode();gz=gzip.compress(raw,mtime=0)
    return gz,hashlib.sha256(gz).hexdigest(),hashlib.sha256(raw).hexdigest()
class Day8Descriptor(unittest.TestCase):
    def test_own_perturbed_gene_excluded_both_targets_pairwise(self):
        gz,h,u=fixture([["A","A",100,"0"],["B","A",30,"0"],["G","A",1,"0.01"],
                        ["B","B",100,"0"],["A","B",50,"0"],["G","B",-1,"0.01"]])
        profiles,src=load(gz,h,u);x=assess(profiles,src)
        self.assertEqual(x["targets"],2)
        for row in x["per_target"]:self.assertEqual(row["genes_measured_excluding_target"],2)
        pair=x["pairwise_target_response"][0]
        self.assertEqual(pair["shared_assayed_off_target_genes"],1)
        self.assertAlmostEqual(pair["signed_cosine_all_common_off_target_genes"],-1)
        self.assertFalse(x["prediction_metric_selected"])
        self.assertFalse(x["independent_confirmation"])
    def test_source_and_fdr_tamper_rejected(self):
        gz,h,u=fixture([["G","A",1,"0.01"]])
        with self.assertRaisesRegex(ValueError,"compressed"):load(gz+b"x",h,u)
        with self.assertRaisesRegex(ValueError,"uncompressed"):load(gz,h,"0"*64)
        for fdr in ("nan","1.2","bad"):
            a,x,y=fixture([["G","A",1,fdr]])
            with self.assertRaises(ValueError):load(a,x,y)
    def test_duplicate_identity_and_blank_target_stops(self):
        for rows in [[["G","A",1,"0.01"],["G","A",2,"0.01"]],[["G","",1,"0.01"]]]:
            a,x,y=fixture(rows)
            with self.assertRaisesRegex(ValueError,"identity"):load(a,x,y)
if __name__=="__main__":unittest.main()
