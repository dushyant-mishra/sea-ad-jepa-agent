import csv,hashlib,io,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import verify_gse335887_cross_geo_target_overlap_v1 as mod
def fixture(head,rows):
    s=io.StringIO(newline="");w=csv.writer(s);w.writerow(head);w.writerows(rows);return s.getvalue().encode()
def sample():
    return {
        "GSE178317":[{"target_gene":"GENE"+str(i)} for i in range(39)],
        "GSE293118":[{"target_class":"gene","target_id":"HG"+str(i)} for i in range(6)],
        "GSE311359":[{"guide_id":"BIN1","nominated_gene":""} for _ in range(3)]+
            [{"guide_id":"MAF_tss_g1","nominated_gene":"MAF"}],
        "GSE301119_CRISPRi":[{"crispr":"Perturbed","Gene_Targeted":"SPI1"},
                             {"crispr":"NTC","Gene_Targeted":"MAF"}],
        "GSE301119_CRISPRa":[{"crispr":"Perturbed","Gene_Targeted":"SPI1"}] }
class CrossGeoMetadataTests(unittest.TestCase):
    def test_direct_vs_nominated_not_equivalent(self):
        j=mod.derive(sample())
        self.assertEqual(j["GSE178317"]["shared_exact_labels"],[])
        self.assertEqual(j["GSE293118"]["shared_exact_labels"],[])
        self.assertEqual(j["GSE311359"]["shared_exact_labels"],["MAF"])
        self.assertEqual(j["GSE301119_CRISPRi"]["shared_exact_labels"],["SPI1"])
        self.assertEqual(j["GSE311359"]["BIN1_duplicate_guide_label_stop"],3)
        self.assertTrue(all(not v["same_biological_intervention_proved"] for v in j.values()))
    def test_changed_bin1_census_fails(self):
        j=sample();j["GSE311359"].pop()
        j["GSE311359"].append({"guide_id":"BIN1","nominated_gene":""})
        # The altered nominated target census is optional, but no phantom extra BIN1 is.
        with self.assertRaisesRegex(ValueError,"BIN1"):mod.derive(j)
    def test_same_size_content_tamper_and_malformed_rows(self):
        a=fixture(["target_gene","sgrna_name"],[["SPI1","sg1"]]);sha=mod.git_blob_digest(a)
        self.assertEqual(mod.parse_metadata(a,"x",sha)[0]["target_gene"],"SPI1")
        b=a.replace(b"SPI1",b"MAF1")
        with self.assertRaisesRegex(ValueError,"source blob"):mod.parse_metadata(b,"x",sha)
        dup=fixture(["target_gene","target_gene"],[["SPI1","SPI1"]])
        with self.assertRaisesRegex(ValueError,"headers"):mod.parse_metadata(dup,"x",mod.git_blob_digest(dup))
        malformed=fixture(["target_gene","sgRNA"],[["SPI1"]])
        with self.assertRaisesRegex(ValueError,"row"):mod.parse_metadata(malformed,"x",mod.git_blob_digest(malformed))
    def test_reference_root_bound(self):
        import unittest.mock as mock
        with mock.patch.object(mod,"REFERENCE_SET_SHA","0"*64):
            with self.assertRaisesRegex(ValueError,"set mutated"):mod.derive(sample())
if __name__=="__main__":unittest.main()
