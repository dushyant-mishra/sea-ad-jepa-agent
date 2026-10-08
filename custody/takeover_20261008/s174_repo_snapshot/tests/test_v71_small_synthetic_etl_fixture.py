import importlib.util, json, shutil
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
B=ROOT/"scripts/v64/build_v71_small_synthetic_etl_fixture.py"
V=ROOT/"scripts/v64/validate_v71_small_synthetic_etl_fixture.py"

def load(path,name):
    s=importlib.util.spec_from_file_location(name,path); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m

def fixture(tmp_path):
    b=load(B,"b"); b.build(tmp_path/"challenge"); return tmp_path/"challenge"

def test_clean_fixture_passes(tmp_path):
    root=fixture(tmp_path); assert load(V,"v").validate(root)==[]

def test_truth_is_physically_separate(tmp_path):
    root=fixture(tmp_path)
    assert (root/"hidden_truth/TRUTH.json").exists()
    assert not any("truth" in p.name.lower() for p in (root/"observable_raw").iterdir())

def test_duplicate_barcode_fails(tmp_path):
    root=fixture(tmp_path); p=root/"observable_raw/multiome_like_matrix.npz"
    z=np.load(p,allow_pickle=False)
    d={k:z[k] for k in z.files}; d["barcodes"]=d["barcodes"].copy(); d["barcodes"][1]=d["barcodes"][0]
    np.savez_compressed(p,**d)
    e=load(V,"v").validate(root)
    assert "DUPLICATE_BARCODE" in e

def test_transpose_like_shape_corruption_fails(tmp_path):
    root=fixture(tmp_path); p=root/"observable_raw/multiome_like_matrix.npz"
    z=np.load(p,allow_pickle=False); d={k:z[k] for k in z.files}
    d["matrix"]=d["matrix"].T
    np.savez_compressed(p,**d)
    assert "MATRIX_AXIS_SHAPE_MISMATCH" in load(V,"v").validate(root)

def test_metadata_barcode_reorder_fails(tmp_path):
    import gzip,csv
    root=fixture(tmp_path); p=root/"observable_raw/cell_metadata.csv.gz"
    with gzip.open(p,"rt",newline="") as f:
        rows=list(csv.reader(f))
    rows[1],rows[2]=rows[2],rows[1]
    with gzip.open(p,"wt",newline="") as f: csv.writer(f).writerows(rows)
    assert "METADATA_BARCODE_ORDER_OR_ID_MISMATCH" in load(V,"v").validate(root)

def test_truth_file_in_observable_root_fails(tmp_path):
    root=fixture(tmp_path)
    shutil.copy(root/"hidden_truth/TRUTH.json",root/"observable_raw/TRUTH_LEAK.json")
    assert any(x.startswith("TRUTH_FIREWALL_PATH") for x in load(V,"v").validate(root))

def test_digest_mismatch_fails(tmp_path):
    root=fixture(tmp_path); p=root/"observable_raw/OBSERVABLES.json"
    obj=json.loads(p.read_text()); obj["n_cells"]+=1; p.write_text(json.dumps(obj))
    assert any(x.startswith("DIGEST_MISMATCH:OBSERVABLES.json") for x in load(V,"v").validate(root))
