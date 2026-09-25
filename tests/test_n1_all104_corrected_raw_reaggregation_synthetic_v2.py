"""Strictly synthetic red team for the prospective corrected all-104 raw-count audit."""
import contextlib
import csv
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import scipy.sparse as sp

SCRIPT=(Path(__file__).resolve().parents[1]/
        "analysis/v5_full104_information_channel_redteam_20260920/scripts/qualify_all104_corrected_raw_reaggregation_v2.py")
spec=importlib.util.spec_from_file_location("n1_all104_audit_test_only",SCRIPT)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
class SyntheticFullCoverage(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.blocks=self.root/"level4"
        self.blocks.mkdir()
        self.out=self.root/"result.json"
        self.p1=self.root/"pass1.npz"
        self.art=self.root/"corrected.npz"
        self.donors=["A","B","C"]
        self.src=np.array([0,1,2],dtype=np.int64)
        self.cd=np.array([0,1,1,2],dtype=np.int64)
        self.core=np.array([0,2],dtype=np.int64)
        self.make_art()
        np.savez(self.p1,cell_donor=self.cd,core=self.core,duniq=np.array(self.donors,dtype=object))
        self.meta=[
          [{"selection_row":"0","canonical_cell_id":"c0","donor_id":"A","expression_row":"0","primary_row_weight":"1","source_library":"HVS"},
           {"selection_row":"1","canonical_cell_id":"c1","donor_id":"B","expression_row":"1","primary_row_weight":"1","source_library":"NPH52"}],
          [{"selection_row":"2","canonical_cell_id":"c2","donor_id":"B","expression_row":"2","primary_row_weight":"1","source_library":"NPH52"},
           {"selection_row":"3","canonical_cell_id":"c3","donor_id":"C","expression_row":"3","primary_row_weight":"1","source_library":"SEA_AD"}]]
        self.counts=[
          sp.csr_matrix(np.array([[2,0,0,0],[0,0,4,0]],dtype=np.int64)),
          sp.csr_matrix(np.array([[0,0,0,0],[1,0,3,0]],dtype=np.int64))]
        self.make_blocks()
    def make_art(self, source_override=None, nnz_override=None):
        donor_src=self.src if source_override is None else source_override
        nnz=np.array([[1,0],[0,1],[1,1]],dtype=np.int64) if nnz_override is None else nnz_override
        umi=np.array([[2,0],[0,4],[1,3]],dtype=np.int64)
        np.savez(self.art,core=self.core,duniq=np.array(self.donors,dtype=object),
            donor_src=donor_src,source_names=np.array(["HVS","NPH52","SEA_AD"],dtype=object),
            donor_nnz=nnz,donor_umi=umi,src_of_cell=self.src[self.cd])
    def make_blocks(self):
        manifest=self.blocks/"PHASE2_EXPRESSION_BLOCK_MANIFEST.csv"
        items=[]
        for k,(meta,mat) in enumerate(zip(self.meta,self.counts)):
            mp=self.blocks/f"b{k}.csv";cp=self.blocks/f"b{k}.npz"
            with mp.open("w",newline="") as f:
                w=csv.DictWriter(f,fieldnames=mod._META_COLUMNS)
                w.writeheader();w.writerows(meta)
            sp.save_npz(cp,mat,compressed=True)
            items.append(dict(block_key=str(k),meta_path=mp.name,meta_sha256=sha(mp),
                    counts_path=cp.name,counts_sha256=sha(cp)))
        with manifest.open("w",newline="") as f:
            w=csv.DictWriter(f,fieldnames=list(items[0]))
            w.writeheader();w.writerows(items)
    def run_it(self, expect=None):
        overrides={"EXPECTED_ARTIFACT_SHA256":sha(self.art),
          "EXPECTED_ARTIFACT_BYTES":self.art.stat().st_size,
          "EXPECTED_PASS1_SHA256":sha(self.p1),
          "EXPECTED_MANIFEST_SHA256":sha(self.blocks/"PHASE2_EXPRESSION_BLOCK_MANIFEST.csv"),
          "EXPECTED_CELLS":4,"EXPECTED_DONORS":3,"EXPECTED_CORE":2,
          "EXPECTED_BLOCKS":2,"N_LEDGER":4,"EXPECTED_SOURCE_COUNTS":(1,1,1)}
        command=["x","--level4-root",str(self.blocks),"--artifact",str(self.art),
                 "--pass1",str(self.p1),"--out",str(self.out)]
        with patch.multiple(mod,**overrides),patch.object(sys,"argv",command),contextlib.redirect_stdout(io.StringIO()):
            if expect:
                with self.assertRaises(SystemExit) as err:mod.main()
                self.assertIn(expect,str(err.exception))
                self.assertFalse(self.out.exists())
            else:
                self.assertEqual(mod.main(),0)
                obj=json.loads(self.out.read_text())
                self.assertEqual(obj["verdict"],"ALL104_EXACT_REAGGREGATION_PASS")
                self.assertEqual(obj["donors_checked"],self.donors)
                self.assertEqual(obj["blocks_verified"],2)
                self.assertEqual(obj["total_strict_core_umi"],10)
                self.assertFalse(obj["n1_burden_calculated"])
                self.assertFalse(obj["protected_outcome_opened"])
    def test_positive_exhaustive_and_output_collision(self):
        self.run_it()
        self.run_it("STOP_OUTPUT_EXISTS")
    def test_wrong_umi_array_fails_exact_comparison(self):
        with np.load(self.art,allow_pickle=True) as z:
            d={k:z[k] for k in z.files}
        d["donor_umi"][1,1]+=1
        np.savez(self.art,**d)
        with patch.object(sys,"argv",["x","--level4-root",str(self.blocks),"--artifact",str(self.art),
               "--pass1",str(self.p1),"--out",str(self.out)]):
            # Rehashing the altered candidate in synthetic mode cannot turn an incorrect
            # full aggregate into a PASS, even if byte-consistent with an altered root.
            with patch.multiple(mod,EXPECTED_ARTIFACT_SHA256=sha(self.art),
                  EXPECTED_ARTIFACT_BYTES=self.art.stat().st_size,
                  EXPECTED_PASS1_SHA256=sha(self.p1),
                  EXPECTED_MANIFEST_SHA256=sha(self.blocks/"PHASE2_EXPRESSION_BLOCK_MANIFEST.csv"),
                  EXPECTED_CELLS=4,EXPECTED_DONORS=3,EXPECTED_CORE=2,
                  EXPECTED_BLOCKS=2,N_LEDGER=4,EXPECTED_SOURCE_COUNTS=(1,1,1)),contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(mod.main(),1)
                self.assertEqual(json.loads(self.out.read_text())["verdict"],"ALL104_REAGGREGATION_FAILED")
    def test_same_census_wrong_donor_source_rejected(self):
        self.make_art(source_override=np.array([1,0,2],dtype=np.int64))
        self.run_it("corrected cell")
    def test_duplicate_selection_row_rejected(self):
        self.meta[1][0]["selection_row"]="1"
        self.make_blocks()
        self.run_it("selection_row")
    def test_negative_count_rejected(self):
        self.counts[0][0,0]=-2
        self.make_blocks()
        self.run_it("negative raw count")
    def test_fractional_count_rejected(self):
        self.counts[0]=self.counts[0].astype(np.float64)
        self.counts[0][0,0]=2.5
        self.make_blocks()
        self.run_it("non-integer raw count")
    def test_tampered_count_without_manifest_change_rejected(self):
        cp=self.blocks/"b0.npz"
        cp.write_bytes(cp.read_bytes()+b"x")
        self.run_it("count-block hash mismatch")
    def test_missing_count_block_fails(self):
        (self.blocks/"b0.npz").unlink()
        with self.assertRaises(FileNotFoundError):
            self.run_it()
    def test_invalid_selection_row_range(self):
        self.meta[0][0]["selection_row"]="-1"
        self.make_blocks()
        self.run_it("selection_row")
if __name__=="__main__":unittest.main()
