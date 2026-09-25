import csv,io,hashlib,os,tarfile,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import gse254205_physical_source_preflight_v1 as m
def make_fixture(tmp):
    folder=tmp/"counts";folder.mkdir();archives=[]
    output=io.StringIO(newline="")
    w=csv.writer(output)
    w.writerow(["sample_id","condition","replicate","amyloid","compound","file","file_sha256","total_counts","genes_detected"])
    for cond in ("NT","AB","AB_GNE"):
        for i in range(1,4):
            sid=f"{cond}_rep{i}";name=f"{sid}ReadsPerGene.out.tab"
            content=f"Gene\tCounts\nENSG00000000001\t{i}\n".encode()
            (folder/name).write_bytes(content)
            w.writerow([sid,cond,f"rep{i}",str(cond!="NT"),"GNE-317" if cond=="AB_GNE" else "",
                        name,hashlib.sha256(content).hexdigest(),i,1])
            archives.append((name,content))
    package=tmp/"source.tar.gz"
    with tarfile.open(package,"w:gz") as tar:
        for name,content in archives:
            i=tarfile.TarInfo("star/counts/"+name);i.size=len(content)
            tar.addfile(i,io.BytesIO(content))
    return folder,package,output.getvalue().encode()
class SourcePreflight(unittest.TestCase):
    def setUp(self):
        self.dir=tempfile.TemporaryDirectory()
        self.root=Path(self.dir.name)
        self.folder,self.tar,self.raw=make_fixture(self.root)
        self.blob=m.git_blob(self.raw)
        self.archsha=m.sha_bytes(self.tar.read_bytes())
        self.patchers=[patch.object(m,"SOURCE_GIT_BLOB_ID",self.blob),
                       patch.object(m,"ARCHIVE_SHA256",self.archsha),
                       patch.object(m,"ARCHIVE_BYTES",self.tar.stat().st_size)]
        for p in self.patchers:p.start()
    def tearDown(self):
        for p in self.patchers:p.stop()
        self.dir.cleanup()
    def test_synthetic_valid_but_never_physical_evidence(self):
        meta=m.parse_frozen_inventory(self.raw)
        out=m.validate_inputs(meta,self.folder,self.tar)
        self.assertEqual(len(out["verified_samples"]),9)
        self.assertTrue(out["archive_member_bytes_equal_extracted_source_bytes"])
        self.assertFalse(out["jepa_training_authorized"])
        self.assertTrue(out["no_differential_expression_values_inspected"])
    def test_frozen_source_metadata_tamper(self):
        raw=self.raw.replace(b"NT_rep1",b"NT_rep9",1)
        with self.assertRaisesRegex(ValueError,"source inventory blob"):m.parse_frozen_inventory(raw)
    def test_design_semantic_mismatch_even_with_rehashed_metadata(self):
        lines=self.raw.decode().splitlines()
        lines[1]=lines[1].replace(",False,",",True,",1)
        altered=("\n".join(lines)+"\n").encode()
        with patch.object(m,"SOURCE_GIT_BLOB_ID",m.git_blob(altered)):
            with self.assertRaisesRegex(ValueError,"treatment mismatch"):m.parse_frozen_inventory(altered)
    def test_same_length_extracted_source_tamper(self):
        meta=m.parse_frozen_inventory(self.raw)
        victim=self.folder/"NT_rep1ReadsPerGene.out.tab"
        data=victim.read_bytes();victim.write_bytes(data.replace(b"\t1\n",b"\t2\n"))
        self.assertEqual(len(victim.read_bytes()),len(data))
        with self.assertRaisesRegex(ValueError,"source changed"):m.validate_inputs(meta,self.folder,self.tar)
    def test_wrong_source_archive_even_if_input_files_match(self):
        meta=m.parse_frozen_inventory(self.raw)
        with patch.object(m,"ARCHIVE_SHA256","0"*64):
            with self.assertRaisesRegex(ValueError,"parent archive"):m.validate_inputs(meta,self.folder,self.tar)
    def test_archive_member_replaced_even_if_rehashed(self):
        meta=m.parse_frozen_inventory(self.raw)
        alt=self.root/"alt.tar.gz"
        with tarfile.open(alt,"w:gz") as tar:
            for name in sorted(meta):
                contents=(self.folder/name).read_bytes()
                if name=="NT_rep1ReadsPerGene.out.tab":contents=contents.replace(b"\t1\n",b"\t2\n")
                x=tarfile.TarInfo("star/counts/"+name);x.size=len(contents);tar.addfile(x,io.BytesIO(contents))
        with patch.object(m,"ARCHIVE_SHA256",m.sha_bytes(alt.read_bytes())),patch.object(m,"ARCHIVE_BYTES",alt.stat().st_size):
            with self.assertRaisesRegex(ValueError,"archive member"):m.validate_inputs(meta,self.folder,alt)
    def test_missing_and_extra_count_inputs(self):
        meta=m.parse_frozen_inventory(self.raw)
        victim=self.folder/"NT_rep1ReadsPerGene.out.tab";data=victim.read_bytes();victim.unlink()
        with self.assertRaisesRegex(ValueError,"missing/extra"):m.validate_inputs(meta,self.folder,self.tar)
        victim.write_bytes(data)
        (self.folder/"EXTRA_rep1ReadsPerGene.out.tab").write_bytes(b"bad")
        with self.assertRaisesRegex(ValueError,"missing/extra"):m.validate_inputs(meta,self.folder,self.tar)
if __name__=="__main__":unittest.main()
