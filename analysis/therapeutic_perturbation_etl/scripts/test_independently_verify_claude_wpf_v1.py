import csv,hashlib,io,json,sys,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parent))
import independently_verify_claude_wpf_v1 as v
class IndependentWpfAuditTests(unittest.TestCase):
    def test_git_blob_measures_actual_bytes(self):
        d=b"target_gene\nCSF1R\n"
        self.assertEqual(len(v.blob(d)),40)
        self.assertNotEqual(v.blob(d),v.blob(d.replace(b"CSF1R",b"CSF2RA")))
    def test_data_roots_are_literal_and_pinned(self):
        self.assertEqual(v.ORIGINAL_BLOBS["day8_development_engagement"][1],
                         "3dc8e48767e8f3e2b013c75ae145bfd802995d0b")
        self.assertEqual(len(v.ORIGINAL_BLOBS),4)
        self.assertEqual(len(v.FEATURE_REFS),2)
        self.assertEqual(v.FIVE,("CSF1R","CSF2RA","CSF2RB","TGFBR1","TGFBR2"))
    def test_csv_rejects_empty(self):
        with self.assertRaisesRegex(ValueError,"empty"):v.rows(b"")
        a=v.rows(b"target_gene,own_gene_status\nCSF1R,ASSAYED_DETECTED\n")
        self.assertEqual(a[0]["target_gene"],"CSF1R")
    def test_wrong_original_bytes_cannot_be_read(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            path=root/v.ROOT/"reference/GSE178317_sgrna_library_suppl_table5.csv"
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_bytes(b"target_gene\nCSF1R\n")
            with self.assertRaisesRegex(ValueError,"byte authority"):
                v.read(root,"day8_library")
if __name__=="__main__":unittest.main()
