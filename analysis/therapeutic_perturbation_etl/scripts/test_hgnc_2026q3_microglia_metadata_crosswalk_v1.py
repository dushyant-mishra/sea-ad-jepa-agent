import hashlib,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from hgnc_2026q3_microglia_metadata_crosswalk_v1 import source_rows,map_features
def fake():
    lines=["hgnc_id\tsymbol\tstatus\tensembl_gene_id"]
    lines.extend(f"HGNC:{i}\tGENE{i}\tApproved\tENSG{i:011d}" for i in range(1,1002))
    return ("\n".join(lines)+"\n").encode()
class MetadataCrosswalk(unittest.TestCase):
    def test_primary_approved_and_no_alias_inference(self):
        approved,ambiguous,n=source_rows(fake())
        self.assertEqual(n,1001)
        self.assertIn("GENE1",approved)
        self.assertNotIn("ALIAS_FOR_GENE1",approved)
        self.assertEqual(ambiguous,set())
    def test_ambiguous_approved_symbol_fails_closed(self):
        source=fake()+b"HGNC:9999\tGENE1\tApproved\tENSG99999999999\n"
        approved,ambiguous,n=source_rows(source)
        self.assertNotIn("GENE1",approved);self.assertIn("GENE1",ambiguous)
    def test_canonical_collision_excluded_not_collapsed(self):
        gene=lambda names,targets:{"features":set(names),"targets":set(targets)}
        a=gene(["G1","G2","G3","UNKNOWN"],["T1","T2"])
        b=gene(["G1","G2","G3","UNKNOWN"],["T1","T2"])
        approved={k:{"ensembl":v,"hgnc_id":"HGNC:1"} for k,v in
                  {"G1":"ENSG00000000001","G2":"ENSG00000000001","G3":"ENSG00000000003","T1":"ENSG00000000004"}.items()}
        out=map_features(a,b,approved,set())
        self.assertEqual(out["exact_primary_targets_mapped"],1)
        self.assertEqual(out["target_names_not_mapped"],["T2"])
        self.assertEqual(out["exact_primary_feature_labels_mapped_collision_free"],1)
        self.assertEqual(len(out["ensembl_collisions"]),1)
        self.assertEqual(out["labels_absent_from_primary_release"],["UNKNOWN"])
        self.assertFalse(out["aliases_auto_mapped"])
        self.assertFalse(out["unresolved_features_treated_as_zero"])
if __name__=="__main__":unittest.main()
