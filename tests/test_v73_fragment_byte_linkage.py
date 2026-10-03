from pathlib import Path
import importlib.util
import json


ROOT = Path(__file__).resolve().parents[1]
TRUTH = ROOT / "scripts/v64/build_v73_sharded_master_truth.py"
MULTI = ROOT / "scripts/v64/build_v73_paired_multiome_sharded_observer.py"
FRAG = ROOT / "scripts/v64/build_v73_synthetic_fragments.py"
VERIFY = ROOT / "scripts/v64/validate_v73_fragment_byte_linkage.py"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def build_world(tmp_path):
    T = load(TRUTH, "v73_frag_truth")
    M = load(MULTI, "v73_frag_multi")
    G = load(FRAG, "v73_frag_build")
    root = tmp_path / "world"
    T.build(root, n_cells=72, shard_size=24, seed=7302)
    M.observe(root, seed=7302)
    G.build(root)
    return root


def test_independent_fragment_byte_linkage_passes(tmp_path):
    V = load(VERIFY, "v73_frag_verify_pass")
    root = build_world(tmp_path)
    out = V.validate(root)
    assert out["status"] == "PASS"
    assert out["qualified"] is True
    assert out["compressed_sha256_recomputed_from_bytes"] is True
    assert out["barcode_multiplicity_reconciled_to_multiome"] is True
    assert out["duplicate_barcode_guard_runs_before_mapping"] is True


def test_same_size_same_records_different_compressed_bytes_fail_digest(tmp_path):
    V = load(VERIFY, "v73_frag_verify_digest")
    root = build_world(tmp_path)
    base = root / "observable_raw/PAIRED_MULTIOME_fragments"
    manifest = json.loads((base / "SYNTHETIC_FRAGMENT_MANIFEST.json").read_text())
    target = base / manifest["shards"][0]["file"]
    before = target.read_bytes()
    assert before[:2] == b"\x1f\x8b"
    mutated = bytearray(before)
    # GZIP MTIME occupies bytes 4..7. Changing it preserves length and decompressed records.
    mutated[4] ^= 0x01
    target.write_bytes(mutated)
    assert target.stat().st_size == len(before)
    out = V.validate(root)
    assert out["status"] == "FAIL_CLOSED"
    assert out["failure_code"] == "COMPRESSED_SHA256_MISMATCH"


def test_copied_digest_assertion_cannot_replace_recomputed_bytes(tmp_path):
    V = load(VERIFY, "v73_frag_verify_copied")
    root = build_world(tmp_path)
    base = root / "observable_raw/PAIRED_MULTIOME_fragments"
    manifest_path = base / "SYNTHETIC_FRAGMENT_MANIFEST.json"
    manifest = json.loads(manifest_path.read_text())
    target = base / manifest["shards"][0]["file"]
    data = bytearray(target.read_bytes())
    data[4] ^= 0x01
    target.write_bytes(data)
    # Leave the manifest's copied assertion untouched. A field-equality-only check would pass;
    # the independent byte digest must fail.
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    out = V.validate(root)
    assert out["failure_code"] == "COMPRESSED_SHA256_MISMATCH"


def test_barcode_multiplicity_reconciliation_detects_wrong_counts_even_with_new_digest(tmp_path):
    V = load(VERIFY, "v73_frag_verify_counts")
    root = build_world(tmp_path)
    base = root / "observable_raw/PAIRED_MULTIOME_fragments"
    manifest_path = base / "SYNTHETIC_FRAGMENT_MANIFEST.json"
    manifest = json.loads(manifest_path.read_text())
    target = base / manifest["shards"][0]["file"]

    import gzip, hashlib, io
    with gzip.open(target, "rt") as fh:
        lines = fh.readlines()
    fields = lines[0].rstrip("\n").split("\t")
    fields[4] = str(int(fields[4]) + 1)
    lines[0] = "\t".join(fields) + "\n"
    raw = open(target, "wb")
    gz = gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0)
    text = io.TextIOWrapper(gz, encoding="utf-8", newline="\n")
    text.writelines(lines)
    text.close()
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    manifest["shards"][0]["sha256"] = digest
    manifest["shards"][0]["multiplicity"] += 1
    manifest["total_multiplicity"] += 1
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")

    out = V.validate(root)
    assert out["status"] == "FAIL_CLOSED"
    assert out["failure_code"] == "BARCODE_MULTIPLICITY_MISMATCH"


def test_cli_contract_always_writes_failure_receipt(tmp_path):
    V = load(VERIFY, "v73_frag_verify_receipt")
    root = build_world(tmp_path)
    base = root / "observable_raw/PAIRED_MULTIOME_fragments"
    manifest = json.loads((base / "SYNTHETIC_FRAGMENT_MANIFEST.json").read_text())
    (base / manifest["shards"][0]["file"]).unlink()
    out = V.validate(root)
    receipt = tmp_path / "receipt.json"
    receipt.write_text(json.dumps(out, indent=2) + "\n")
    reread = json.loads(receipt.read_text())
    assert reread["status"] == "FAIL_CLOSED"
    assert reread["failure_code"] == "FRAGMENT_SHARD_MISSING"
