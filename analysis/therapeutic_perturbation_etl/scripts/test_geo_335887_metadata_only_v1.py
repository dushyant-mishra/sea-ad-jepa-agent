import gzip,io,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from geo_335887_metadata_only_v1 import parse_header_only,build_from_source
def fixture(corrupt=False):
    rows=["^SERIES = GSE335887","!Series_title = fake metadata","!Series_sample_id = GSM0001"]
    if corrupt:rows.append("!Series_sample_id = GSM9999")
    for i in range(1,9):
        rows.extend([f"^SAMPLE = GSM{i:04d}",f"!Sample_title = biological metadata {i}",
            "!Sample_source_name_ch1 = iTF-MG","!Sample_characteristics_ch1 = model: TF",
            "!sample_table_begin","ID\tLog2FC","SECRET_GENE\t99999","!sample_table_end"])
    return ("\n".join(rows)+"\n").encode()
class GeoFirewall(unittest.TestCase):
    def test_expression_table_never_exposed(self):
        r=parse_header_only(fixture())
        self.assertEqual(r["sample_count"],8)
        self.assertFalse(r["sample_expression_values_inspected"])
        self.assertEqual(r["sample_expression_table_lines_skipped"],16)
        self.assertNotIn("SECRET_GENE",str(r));self.assertNotIn("99999",str(r))
    def test_series_sample_mismatch_stops(self):
        with self.assertRaisesRegex(ValueError,"Series/sample"):
            parse_header_only(fixture(True))
    def test_missing_source_stops(self):
        with self.assertRaisesRegex(ValueError,"sample census"):
            parse_header_only(b"^SERIES = GSE335887\n^SAMPLE = GSM1\n!Sample_title = x\n")
    def test_compressed_source_bound_and_output_scope(self):
        o=build_from_source(gzip.compress(fixture(),mtime=0))
        self.assertFalse(o["jepa_training_authorized"])
        self.assertEqual(o["schema"],"GSE335887_GEO_METADATA_ONLY_V1")
        self.assertEqual(len(o["soft_gzip_sha256"]),64)
if __name__=="__main__":unittest.main()
