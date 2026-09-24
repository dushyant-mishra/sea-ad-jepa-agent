"""Adversarial committed-byte manifest tests; temporary synthetic bytes only."""
import pathlib
import sys
import pytest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/
    "analysis/therapeutic_perturbation_etl/scripts"))
from verify_committed_outputs_full_sha256_v1 import inventory, IntegrityStop, ROOT

def setup(tmp_path):
    folder=tmp_path/ROOT/"gse178317"
    folder.mkdir(parents=True)
    (folder/"one.npz").write_bytes(b"abc")
    return {"gse178317/one.npz":(3,"ba7816bf8f01cfea")}

def test_exact_census_and_full_digest(tmp_path):
    known=setup(tmp_path)
    result=inventory(tmp_path,expected=known,require_git=False)
    assert len(result["files"])==1
    assert result["files"][0]["sha256"]=="ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    assert result["source_git_blob_verified"] is False

def test_unlisted_binary_must_fail(tmp_path):
    known=setup(tmp_path)
    (tmp_path/ROOT/"gse178317"/"extra.gz").write_bytes(b"x")
    with pytest.raises(IntegrityStop,match="extra"):
        inventory(tmp_path,expected=known,require_git=False)

def test_missing_binary_must_fail(tmp_path):
    known=setup(tmp_path)
    (tmp_path/ROOT/"gse178317"/"one.npz").unlink()
    with pytest.raises(IntegrityStop,match="missing"):
        inventory(tmp_path,expected=known,require_git=False)

def test_same_size_mutation_must_fail(tmp_path):
    known=setup(tmp_path)
    (tmp_path/ROOT/"gse178317"/"one.npz").write_bytes(b"abd")
    with pytest.raises(IntegrityStop,match="digest"):
        inventory(tmp_path,expected=known,require_git=False)

def test_wrong_expected_size_fails(tmp_path):
    known=setup(tmp_path)
    known["gse178317/one.npz"]=(4,"ba7816bf8f01cfea")
    with pytest.raises(IntegrityStop,match="size"):
        inventory(tmp_path,expected=known,require_git=False)

def test_symlink_rejected(tmp_path):
    known=setup(tmp_path)
    p=tmp_path/ROOT/"gse178317"/"one.npz"
    p.unlink()
    q=tmp_path/"outside"
    q.write_bytes(b"abc")
    p.symlink_to(q)
    with pytest.raises(IntegrityStop,match="symlink"):
        inventory(tmp_path,expected=known,require_git=False)

def test_truncated_hash_not_accepted_as_complete(tmp_path):
    known=setup(tmp_path)
    known["gse178317/one.npz"]=(3,"ba7816bf")
    with pytest.raises(IntegrityStop,match="prefix"):
        inventory(tmp_path,expected=known,require_git=False)
