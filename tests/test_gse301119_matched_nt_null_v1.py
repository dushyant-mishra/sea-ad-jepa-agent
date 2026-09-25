"""CPU-only synthetic positive and adversarial tests. No real outcomes inspected."""
from __future__ import annotations
import csv
import importlib.util
import json
from pathlib import Path
import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "analysis/therapeutic_perturbation_etl/scripts/gse301119_matched_nt_null_v1.py"
spec = importlib.util.spec_from_file_location("ntnull", SCRIPT)
nt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(nt)


def fake_export(tmp, insufficient=False, missing_sentinel=False):
    root = tmp / "neutral"
    root.mkdir()
    manifest = {"schema": "GSE301119_NEUTRAL_ARRAY_EXPORT_V1", "exports": {}}
    names = list(nt.SENTINELS)
    if missing_sentinel:
        names.remove("MT1G")
    names += [f"G{i:03d}" for i in range(145)]
    for mod in nt.MODALITIES:
        meta, cols = [], []
        for donor in nt.DONORS:
            for i in range(22):
                meta.append({"guide_donor": f"{mod}_nt{i}_{donor}", "donor": donor,
                             "crispr": "NT", "Gene_Targeted": "", "n_cells": "10"})
                row = np.full(len(names), 10, dtype="<i4")
                # Sparse state-related sentinel: just 1/22 NT groups express it.
                row[0] = 1000 if i == 0 else 0
                cols.append(row)
            for target in ("T1", "T2"):
                for guide in range(2):
                    meta.append({"guide_donor": f"{mod}_{target}{guide}_{donor}",
                                 "donor": donor, "crispr": "Perturbed",
                                 "Gene_Targeted": target,
                                 "n_cells": "1" if insufficient else "10"})
                    row = np.full(len(names), 10, dtype="<i4")
                    row[0] = 0  # no CLU-specific treatment effect by construction
                    if target == "T1":
                        row[-1] = 100
                    cols.append(row)
        counts = np.asarray(cols, dtype="<i4").T.copy(order="F")
        bp = root / f"{mod}_counts_int32.bin"
        counts.flatten(order="F").tofile(bp)
        (root / f"{mod}_shape.txt").write_text(
            f"{counts.shape[0]}\n{counts.shape[1]}\n")
        (root / f"{mod}_features.txt").write_text("\n".join(names) + "\n")
        with open(root / f"{mod}_gd_meta.csv", "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(meta[0]))
            writer.writeheader()
            writer.writerows(meta)
        manifest["exports"][mod] = {
            "source_rds_sha256_after_export": nt.EXPECTED_RDS[mod],
            "counts_bin_sha256": nt.sha256(bp),
            "dim": list(counts.shape)}
    v1 = root / "NEUTRAL_EXPORT_RECEIPT_V1.json"
    v1.write_text(json.dumps(manifest))
    certification = {
        "schema": "GSE301119_NEUTRAL_IDENTITY_CERTIFICATION_V2",
        "v1_export_receipt_sha256": nt.sha256(v1),
        "protected_outcome_opened": False,
        "training_authorized": False,
        "therapeutic_ranking": False,
        "file_validation": {},
    }
    for mod in nt.MODALITIES:
        certification["file_validation"][mod] = {
            "source_rds_sha256": nt.EXPECTED_RDS[mod],
            "equality": "ALL_FOUR_NEUTRAL_EXPORT_FILES_RECONSTRUCTED_BYTE_IDENTICAL_FROM_ORIGINAL_RDS",
            "exported_file_sha256": {
                "counts_bin": nt.sha256(root / f"{mod}_counts_int32.bin"),
                "shape": nt.sha256(root / f"{mod}_shape.txt"),
                "features": nt.sha256(root / f"{mod}_features.txt"),
                "gd_meta": nt.sha256(root / f"{mod}_gd_meta.csv"),
            },
        }
    # Synthetic-only attestation: actual physical V2 MUST be emitted by R script.
    (root / "NEUTRAL_EXPORT_IDENTITY_CERTIFICATION_V2.json").write_text(
        json.dumps(certification))
    return root, manifest


def _cert(root):
    return json.loads((root / "NEUTRAL_EXPORT_IDENTITY_CERTIFICATION_V2.json").read_text())


def test_positive_control_complete_both_modalities(tmp_path):
    root, receipt = fake_export(tmp_path)
    report = nt.audit_modality(root, "CRISPRi", receipt, 16, 1.5,
                               np.random.default_rng(nt.SEED), _cert(root))
    for d in nt.DONORS:
        for target in ("T1", "T2"):
            got = report["donors"][d]["targets"][target]
            assert got["status"] == "MATCHED_DESCRIPTIVE_NULL_ONLY"
            assert got["matched_null_draws"] >= 8
            assert got["depth_only_null_draws"] >= 8
            assert got["cells"] == 20 and got["guides"] == 2
            assert got["null_max_abs_fc_median"] > 0
            assert got["depth_only_max_abs_fc_median"] >= 0
            assert got["depth_only_expected_raw_total"] == got["unit_raw_depth"]
    assert report["missing_sentinel_genes"] == []


def test_exposes_existing_flat_gene_sign_fixture_failure():
    old_nt = [100, 100, 100]
    old_target = [400, 25, 100]
    e = nt.effects(old_target, old_nt)
    assert e[0] > 0 and e[1] < 0
    assert -0.81 < e[2] < -0.80  # unchanged raw gene shifts by composition


def test_true_identical_profiles_are_zero():
    assert np.max(np.abs(nt.effects([40, 20, 80], [400, 200, 800]))) < 1e-12


def test_depth_only_binomial_thinning_preserves_composition_in_expectation():
    full = np.array([100000, 50000, 25000], dtype=np.int64)
    rng = np.random.default_rng(99)
    vals = []
    for _ in range(200):
        thin = nt.depth_only_null(full, 17500, rng)
        assert thin is not None
        vals.append(thin / thin.sum())
    got = np.mean(vals, axis=0)
    want = full / full.sum()
    assert np.max(np.abs(got - want)) < 0.005


def test_depth_only_null_rejects_impossible_or_zero_target_depth():
    rng = np.random.default_rng(2)
    full = np.array([20, 30, 50], dtype=np.int64)
    assert nt.depth_only_null(full, 0, rng) is None
    assert nt.depth_only_null(full, 100, rng) is None
    assert nt.depth_only_null(full, 150, rng) is None


def test_median_centred_sensitivity_recovers_flat_when_positivity_holds():
    a = np.ones(150, dtype=int) * 100
    b = a.copy()
    b[0] = 400
    b[1] = 25
    median_e, shared = nt.median_ratio_sensitivity(b, a)
    assert shared == 150
    assert abs(median_e[2]) < 1e-12  # contrast with logCPM flat-gene bias


def test_not_enough_shared_detected_genes_is_missing_not_zero():
    x = np.zeros(150, dtype=int)
    x[:20] = 10
    y = x.copy()
    v, shared = nt.median_ratio_sensitivity(x, y)
    assert shared == 20 and np.isnan(v).all()


def test_pseudo_target_never_overlaps_its_reference():
    rng = np.random.default_rng(17)
    nt_ids = np.arange(30)
    subset, cells = nt.matched_subset(nt_ids, np.ones(30, dtype=int)*10,
                                       3, 30, rng)
    assert len(subset) == 3 and cells == 30
    remaining = set(nt_ids) - set(subset)
    assert len(remaining) == 27 and set(subset).isdisjoint(remaining)


def test_wrong_cell_count_is_not_silently_matched():
    a, b = nt.matched_subset(np.arange(6), np.full(6, 100),
                              2, 20, np.random.default_rng(1))
    assert a is None and b is None


def test_wrong_source_digest_stops(tmp_path):
    root, receipt = fake_export(tmp_path)
    receipt["exports"]["CRISPRi"]["source_rds_sha256_after_export"] = "0"*64
    with pytest.raises(ValueError, match="SOURCE_RDS_DIGEST"):
        nt.load_modality(root, "CRISPRi", receipt, _cert(root))


def test_tampered_count_byte_stops(tmp_path):
    root, receipt = fake_export(tmp_path)
    bp = root / "CRISPRi_counts_int32.bin"
    with open(bp, "r+b") as f:
        f.seek(0)
        f.write(b"\\x01\\x00\\x00\\x00")
    with pytest.raises(ValueError, match="NEUTRAL_IDENTITY_FILE_DIGEST_counts_bin"):
        nt.load_modality(root, "CRISPRi", receipt, _cert(root))


def test_duplicate_guide_identity_stops(tmp_path):
    root, receipt = fake_export(tmp_path)
    p = root / "CRISPRi_gd_meta.csv"
    lines = p.read_text().splitlines()
    fields = list(csv.DictReader(lines))
    fields[1]["guide_donor"] = fields[0]["guide_donor"]
    with open(p, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(fields[0]))
        w.writeheader(); w.writerows(fields)
    # The v2 source-derived digest detects changed metadata before structural
    # duplicate validation. Rehash here only to exercise the independent
    # structural duplicate check against a synthetic test certificate.
    cert = _cert(root)
    cert["file_validation"]["CRISPRi"]["exported_file_sha256"]["gd_meta"] = nt.sha256(p)
    with pytest.raises(ValueError, match="DUPLICATE_GUIDE"):
        nt.load_modality(root, "CRISPRi", receipt, cert)


def test_undersupported_target_fails_closed(tmp_path):
    root, receipt = fake_export(tmp_path, insufficient=True)
    got = nt.audit_modality(root, "CRISPRa", receipt, 16, 1.5,
                             np.random.default_rng(nt.SEED), _cert(root))
    assert all(row["status"] == "NOT_ESTIMABLE_TARGET_CELL_SUPPORT"
               for d in nt.DONORS for row in got["donors"][d]["targets"].values())


def test_missing_sentinel_is_reported(tmp_path):
    root, receipt = fake_export(tmp_path, missing_sentinel=True)
    got = nt.audit_modality(root, "CRISPRi", receipt, 16, 1.5,
                             np.random.default_rng(nt.SEED), _cert(root))
    assert got["missing_sentinel_genes"] == ["MT1G"]


def test_cli_fails_on_occupied_output_and_never_overwrites(tmp_path):
    root, _ = fake_export(tmp_path)
    occupied = tmp_path / "prior"; occupied.mkdir()
    (occupied / "old.txt").write_text("preserve")
    with pytest.raises(SystemExit, match="STOP_OUTPUT_EXISTS"):
        nt.main(["--neutral-dir", str(root), "--out-dir", str(occupied),
                 "--identity-cert", str(root / "NEUTRAL_EXPORT_IDENTITY_CERTIFICATION_V2.json"),
                 "--draws", "16"])
    assert (occupied / "old.txt").read_text() == "preserve"


def test_cli_writes_small_development_only_receipt(tmp_path):
    root, _ = fake_export(tmp_path)
    out = tmp_path / "fresh"
    nt.main(["--neutral-dir", str(root), "--out-dir", str(out),
             "--identity-cert", str(root / "NEUTRAL_EXPORT_IDENTITY_CERTIFICATION_V2.json"),
             "--draws", "16"])
    p = out / "GSE301119_MATCHED_NT_DESCRIPTIVE_NULL_V1.json"
    report = json.loads(p.read_text())
    assert set(report["modalities"]) == set(nt.MODALITIES)
    assert report["status"] == "DEVELOPMENT_ONLY_NO_SCIENTIFIC_QUALIFICATION"
    assert report["training_authorized"] is False
    assert report["protected_outcome_opened"] is False
    assert p.stat().st_size < 250_000


def test_metadata_donor_swap_without_count_change_fails_source_binding(tmp_path):
    root, receipt = fake_export(tmp_path)
    meta_path = root / "CRISPRi_gd_meta.csv"
    rows = list(csv.DictReader(meta_path.open(newline="")))
    # Different donor identity; no count-bin change and no duplicate keys.
    rows[0]["donor"] = "D2"
    with meta_path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)
    assert nt.sha256(root / "CRISPRi_counts_int32.bin") == receipt["exports"]["CRISPRi"]["counts_bin_sha256"]
    with pytest.raises(ValueError, match="NEUTRAL_IDENTITY_FILE_DIGEST_gd_meta"):
        nt.load_modality(root, "CRISPRi", receipt, _cert(root))


def test_feature_order_swap_without_count_change_fails_source_binding(tmp_path):
    root, receipt = fake_export(tmp_path)
    p = root / "CRISPRi_features.txt"
    feats = p.read_text().splitlines()
    feats[0], feats[1] = feats[1], feats[0]
    p.write_text("\n".join(feats) + "\n")
    with pytest.raises(ValueError, match="NEUTRAL_IDENTITY_FILE_DIGEST_features"):
        nt.load_modality(root, "CRISPRi", receipt, _cert(root))


def test_source_certification_missing_stops_cli(tmp_path):
    root, _ = fake_export(tmp_path)
    path = root / "NEUTRAL_EXPORT_IDENTITY_CERTIFICATION_V2.json"
    path.unlink()
    with pytest.raises(SystemExit, match="STOP_MISSING_RDS_BACKED_NEUTRAL_IDENTITY_CERT"):
        nt.main(["--neutral-dir", str(root), "--out-dir", str(tmp_path/"out"),
                 "--identity-cert", str(path), "--draws", "16"])
    assert not (tmp_path/"out").exists()


def test_certification_wrong_source_digest_stops(tmp_path):
    root, receipt = fake_export(tmp_path)
    cert = _cert(root)
    cert["file_validation"]["CRISPRi"]["source_rds_sha256"] = "0"*64
    with pytest.raises(ValueError, match="STOP_NEUTRAL_IDENTITY_CERT_SOURCE_UNBOUND"):
        nt.load_modality(root, "CRISPRi", receipt, cert)


def test_cli_receipt_records_v2_identity_certificate_digest(tmp_path):
    root, _ = fake_export(tmp_path)
    p = root / "NEUTRAL_EXPORT_IDENTITY_CERTIFICATION_V2.json"
    out = tmp_path / "newout"
    nt.main(["--neutral-dir", str(root), "--out-dir", str(out),
             "--identity-cert", str(p), "--draws", "16"])
    receipt = json.loads((out / "GSE301119_MATCHED_NT_DESCRIPTIVE_NULL_V1.json").read_text())
    assert receipt["neutral_identity_certification_v2_sha256"] == nt.sha256(p)
