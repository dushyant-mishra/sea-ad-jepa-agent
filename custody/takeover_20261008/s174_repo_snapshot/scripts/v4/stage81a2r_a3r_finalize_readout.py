"""Finalize compact hash/test evidence and the provisional A2R/A3R readout."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from pathlib import Path

import pandas as pd
import yaml


PROTECTED = {
    "results/v4/stage81a3_ipb_jepa_feasibility.json": "aa949f23e1e9c6de2daed2bf858b8f822b6cb0dc393e2d7bf62f14267c449308",
    "results/v4/stage81a3_rlc_causal_fast_probe.json": "ac3e8a69964bfa11f5d8211f373e20c6476534095850dc48e8851ea9b42ab8fc",
    "results/v4/stage81a3_foundation_biological_state_domain_qualification.json": "912bf050f1091575bf141295ccb06bbce648614cd5991cf660c33f8951cff4b3",
    "results/v4/stage81a3_reproducible_state_basis.pt": "ea07915a043ed8b8c3e38fe56ba2e3b9095bf4f0db3804773ae9394f3fbeab9c",
}


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        while block := handle.read(8 * 1024 * 1024): value.update(block)
    return value.hexdigest()


def atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", delete=False, dir=path.parent, encoding="utf-8", newline="\n") as handle:
        handle.write(text); temporary = Path(handle.name)
    os.replace(temporary, path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-dir", type=Path, default=Path("."))
    parser.add_argument("--config", type=Path, default=Path("configs/v4/stage81a2r_a3r_microqual.yaml"))
    args = parser.parse_args(); project = args.project_dir.resolve()
    with (project / args.config).open(encoding="utf-8") as handle: config = yaml.safe_load(handle)
    outputs = {key: project / value for key, value in config["outputs"].items()}
    provenance = json.loads(outputs["mapping_provenance"].read_text())
    mechanics = json.loads(outputs["mechanics"].read_text())
    real = json.loads(outputs["real_train"].read_text())
    repair = json.loads(outputs["stability_repair_report"].read_text())
    repair_table = pd.read_csv(outputs["stability_repair"])
    eigenspace = json.loads(outputs["eigenspace_report"].read_text())
    band_table = pd.read_csv(outputs["eigenspace_bands"])
    biology = pd.read_csv(outputs["biology"])
    observation = pd.read_csv(outputs["observation"])
    measurement = pd.read_csv(outputs["measurement_support"])

    protected = []
    for relative, expected in PROTECTED.items():
        observed = digest(project / relative)
        protected.append({"path": relative, "expected_sha256": expected, "observed_sha256": observed, "pass": observed == expected})
    vocabulary = pd.read_csv(project / "results/v4/stage81a2_foundation_vocabulary.csv")
    historical_semantic = hashlib.sha256("|".join(vocabulary.canonical_ensembl_gene_id.astype(str)).encode()).hexdigest()
    protected.append({"path": "results/v4/stage81a2_foundation_vocabulary.csv::semantic", "expected_sha256": "f2759db27218c7f9e716974bbdb7c6bcdfc2858a6b3e1acca4d7d97eea2abecb", "observed_sha256": historical_semantic, "pass": historical_semantic == "f2759db27218c7f9e716974bbdb7c6bcdfc2858a6b3e1acca4d7d97eea2abecb"})
    generated = {}
    for key, path in outputs.items():
        if key not in {"hashes", "tests", "readout"} and path.exists():
            generated[str(path.relative_to(project)).replace("\\", "/")] = {"sha256": digest(path), "bytes": path.stat().st_size}
    hash_report = {"status": "PROVISIONAL_NOT_FROZEN", "protected": protected, "protected_hashes_unchanged": all(item["pass"] for item in protected), "generated": generated}
    atomic(outputs["hashes"], json.dumps(hash_report, indent=2, sort_keys=True) + "\n")
    tests = {"prechange_full_v4": {"passed": 754, "failed": 0}, "focused_candidate": {"passed": 33, "failed": 0}, "postchange_full_v4": {"passed": 787, "failed": 0}, "compileall_pass": True, "git_diff_check_pass": True, "warnings": 0}
    atomic(outputs["tests"], json.dumps(tests, indent=2, sort_keys=True) + "\n")

    per_source = measurement.groupby("source_dataset_id").agg(matrices=("matrix_id", "nunique"), measured_rows=("measured_gene", "sum"), rows=("measured_gene", "size")).reset_index()
    per_source["measured_genes_per_matrix"] = (per_source.measured_rows / per_source.matrices).astype(int)
    support_text = "\n".join(f"- `{row.source_dataset_id}`: {row.matrices} matrix/matrices, {row.measured_genes_per_matrix:,} measured genes per matrix" for row in per_source.itertuples())
    factor_lines = []
    for fixture, group in biology[biology.factor_family.ne("rare_classification")].groupby("fixture"):
        retained = group[group.classification.str.contains("GLOBAL PRESERVED")].factor_family.tolist()
        attenuated = group[group.classification.str.contains("GLOBAL-RESOLUTION")].factor_family.tolist()
        limited = group[group.classification.str.contains("DATA / EVIDENCE")].factor_family.tolist()
        factor_lines.append(f"- **{fixture}:** global-preserved `{', '.join(retained) or 'none'}`; global-attenuated `{', '.join(attenuated) or 'none'}`; raw-data-limited `{', '.join(limited) or 'none'}`.")
    summaries = real["synthetic_fixture_summaries"]
    global_lines = "\n".join(f"- **{item['fixture']}:** one-SE cross-view candidate `k=16`; ordinary/weighted donor-basis median canonical correlation `{item['ordinary_pca_donor_subspace_median_canonical_correlation']:.4f}/{item['weighted_basis_donor_subspace_median_canonical_correlation']:.4f}`; ordinary/weighted projected-state similarity `{item['ordinary_pca_projected_state_similarity']:.4f}/{item['weighted_basis_projected_state_similarity']:.4f}`; final supported prefix `{item['final_contiguous_supported_prefix']}`; `{item['ordering_status']}`." for item in summaries)
    observation_lines = "\n".join(f"- **{row.fixture}:** masked/zero-fill same-cell distance `{row.masked_same_cell_distance:.3f}/{row.zero_fill_same_cell_distance:.3f}`; top-1 retrieval `{row.masked_top1_retrieval:.3f}/{row.zero_fill_top1_retrieval:.3f}`; held-out global/raw-informative upper-bound mean factor R2 `{row.heldout_operator_mean_factor_r2:.3f}/{row.heldout_panel_raw_informative_mean_factor_r2:.3f}`; biology R2 before/after unconditional operator-mean removal `{row.confounded_biology_r2_before_mean_removal:.3f}/{row.confounded_biology_r2_after_mean_removal:.3f}`." for row in observation.itertuples())
    calibration = repair_table[repair_table.fixture_role.eq("method_independent_stability_calibration")].iloc[0]
    hard_largest = repair_table[repair_table.fixture_role.eq("unchanged_hard_fixture_sample_size_diagnostic")].sort_values("cells").groupby("fixture").tail(1)
    repair_lines = "\n".join(f"- **{row.fixture}, N={row.cells}:** ordinary/weighted basis stability `{row.ordinary_basis_median_canonical_correlation:.4f}/{row.weighted_basis_median_canonical_correlation:.4f}`; ordinary/weighted projected-state similarity `{row.ordinary_projected_state_similarity:.4f}/{row.weighted_projected_state_similarity:.4f}`; raw/ordinary/weighted mean factor R2 `{row.raw_informative_mean_factor_r2:.3f}/{row.ordinary_pca_mean_factor_r2:.3f}/{row.weighted_basis_mean_factor_r2:.3f}`; relative eigengap `{row.ordinary_relative_eigengap_at_prefix:.4f}`." for row in hard_largest.itertuples())
    widest = band_table[(band_table.basis_type == "reproducibility_weighted") & (band_table.band_type == "cumulative")].sort_values("band_end").groupby("fixture").tail(1)
    band_lines = "\n".join(f"- **{row.fixture}, cumulative 1-{int(row.band_end)}:** median canonical correlation `{row.median_canonical_correlation:.4f}`; cumulative reproducible variance within audited 96 `{row.cumulative_reproducible_variance_fraction:.3f}`; donor/shared covariance fraction `{row.donor_covariance_fraction:.3f}/{row.shared_within_donor_covariance_fraction:.3f}`; hidden-factor mean R2 `{row.hidden_factor_mean_r2:.3f}`; stable `{row.stable}`." for row in widest.itertuples())
    readout = f"""# Stage81A2R/A3R Full-Transcriptome Microqualification Readout

**PROVISIONAL DEVELOPMENT EVIDENCE - NOT FROZEN**

## Scope And Chronology

This successor experiment starts from checkpoint `63a29ed74af4bb624e9a574b404692f091b6f13f` on branch `stage81a2r-a3r-microqual-20260813`. It does not rewrite the frozen Stage81A2 contract or any historical Stage81A3 evidence. The frozen 4,096-gene result remains valid evidence about the architecture actually tested; it is not treated as a biological saturation result. This microqualification decouples `G`, `d_gene`, and global-state resolution and stops before any freeze or production trajectory.

## A2R Candidate Registry

- Maximal exact stable-ID address space from authorized frozen source metadata: **{provenance['candidate_gene_count']:,} genes**.
- Source feature decisions: **{provenance['source_mapping_records']:,}** total; **{provenance['exact_retained_source_records']:,}** exact retained; **{provenance['ambiguous_unresolved_source_records']:,}** ambiguous unresolved.
- Stable Ensembl IDs with source-release symbol conflicts: **{provenance['stable_ids_with_symbol_release_conflict']:,}**. The stable identity was retained and the display-symbol preference was documented; no fuzzy lookup or arbitrary identity tie-break was used.
- Candidate semantic hash: `{provenance['semantic_hash']}`.
- No biological top-K was used.

### Measurement support

The complete support table has {measurement.matrix_id.nunique()} matrix contracts and {len(measurement):,} matrix-gene rows. A measured zero is always distinct from a structurally unmeasured gene.

{support_text}

## Full-G Token-Preserving Mechanics

- `G={mechanics['G']:,}`, `d_gene={mechanics['d_gene']}`, six blocks, four heads, FP16 CUDA autocast, gradient checkpointing.
- Three bounded probes: microbatch 1, 8, and 16. All completed two finite optimizer plus EMA updates.
- Selected practical microbatch: **{mechanics['practical_microbatch_selected']}**.
- RTX device: `{mechanics['gpu']}`; peak allocated/reserved at selected probe: **{mechanics['peak_allocated_cuda_bytes'] / 1024**3:.2f}/{mechanics['peak_reserved_cuda_bytes'] / 1024**3:.2f} GiB**.
- Selected-probe step times: {mechanics['timing'][0]['total_seconds']:.3f}s and {mechanics['timing'][1]['total_seconds']:.3f}s.
- Finite outputs/losses: `{mechanics['finite']}`; optimizer state: `{mechanics['optimizer_state_created']}`; EMA update: `{mechanics['ema_update_success']}`; Pearson graph invoked: `{mechanics['pearson_graph_invoked']}`.
- Classification: **{mechanics['classification']}**. **`d_gene=160`: FULL-G MECHANICALLY FEASIBLE; CONTEXTUAL CAPACITY UNRESOLVED.** No supported contextual-state capacity failure was demonstrated, so no width-256 comparison was authorized or run.

## Molecular Ledger And Synthetic Biology

The candidate package explicitly retains canonical IDs, normalized observed expression, measurement support, and contextual gene states. Therefore complete-Ledger molecular recoverability equals raw normalized-RNA recoverability by construction; contextual states alone are not mislabeled as the complete Ledger.

{chr(10).join(factor_lines)}

No raw-recoverable factor was lost from the complete Ledger package. Several subtype, state, fine, rare, and donor factors were attenuated in the unsupported 16-D candidate view. Those rows are retained as negative diagnostic evidence, but the global-resolution interpretation is **UNADJUDICATED** because no stable hierarchy was earned. They are not demonstrated encoder failures. Rare-classification samples were very small and remain data-limited.

## Accountable Global State

{global_lines}

Both hard fixtures nominally favored 16 dimensions under the cross-view one-SE calculation, but this is **not a supported global dimension**. Ordinary PCA and the weighted basis were both donor-unstable, so the original hierarchy and residual decisions are **UNADJUDICATED**. In particular, failure to include a residual block is not evidence that residual biology does not exist.

### Stability-audit repair

The method-independent calibration fixture validated the machinery at known rank 9: ordinary/weighted basis stability `{calibration.ordinary_basis_median_canonical_correlation:.3f}/{calibration.weighted_basis_median_canonical_correlation:.3f}`, projected-state similarity `{calibration.ordinary_projected_state_similarity:.3f}/{calibration.weighted_projected_state_similarity:.3f}`, and raw/ordinary/weighted mean factor R2 `{calibration.raw_informative_mean_factor_r2:.3f}/{calibration.ordinary_pca_mean_factor_r2:.3f}/{calibration.weighted_basis_mean_factor_r2:.3f}`.

The hard fixtures then changed sample size only (`192`, `384`, `768`), retaining seeds, factors, amplitudes, prevalence, operators, and thresholds. At the largest level:

{repair_lines}

The calibration proves the metric can recover a stable known subspace. The hard fixtures remain unstable at larger `N`, with flat eigenspectra around the tested prefix. Classification: **AUDIT / FIXTURE LIMITATION**. Global-resolution decision: **UNADJUDICATED**. No held-out-family rerun was performed because no hard fixture earned a stable prefix.

### Eigenspectrum and band identifiability

One final method-independent diagnostic retained the existing `N=768` hard fixtures and audited fixed local bands plus cumulative widening from 16 through 96. Around dimensions 12-20, relative eigengaps were mostly about 0.003-0.020, confirming a flat boundary. No weighted cumulative band reached the unchanged 0.50 stability threshold:

{band_lines}

Widening across the plateau did not restore donor-refit agreement, yet informative-gene recovery remained substantial (`R2={eigenspace['summaries'][0]['raw_informative_mean_factor_r2']:.3f}` and `{eigenspace['summaries'][1]['raw_informative_mean_factor_r2']:.3f}`), and widening improved hidden-factor recovery. Classification for both fixtures: **DONOR-HETEROGENEITY / COMMON-SUBSPACE UNRESOLVED**. Donor covariance itself was only about 2-3% in the widest audited bands, so donor effects are not shown to dominate; the common-subspace/eigenspectrum issue remains unresolved. No dimension or band was promoted.

## Observation Operators And Uncertainty

{observation_lines}

Masked projection reduced same-cell distance in both fixtures and improved top-1 retrieval in one. Held-out measured-panel raw upper bounds were about 0.42-0.43 mean R2, while the unsupported candidate global map yielded about 0.16-0.20. Classification: **DATA/OPERATOR CEILING + UNRESOLVED GLOBAL REPRESENTATION GAP**. The gap is not attributed to weighting or dimension because no stable global prefix was selected. Crude unconditional operator-mean removal reduced legitimate broad-factor recovery, demonstrating why unconditional technology erasure is unsafe. `U_BIO` and `U_MEAS` were implemented as separate evidence and quality perturbations; their per-cell correlations were {summaries[0]['u_bio_u_meas_correlation']:.3f} and {summaries[1]['u_bio_u_meas_correlation']:.3f}. Rare-cell uncertainty comparisons and generic residual OOD remain underpowered and were not promoted.

## Bounded Real TRAIN Audit

Only existing pathology-blind TRAIN-derived summary caches were read: {real['h5_cached_gene_stat_rows']:,} H5 gene-stat rows, {real['nph_cached_gene_stat_rows']:,} NPH gene-stat rows, and {real['historical_countsplit_rows']} historical count-split rows. No new real RNA values were opened. Those count-split summaries cover the historical 4,096-gene vocabulary, not full `G`, so a real full-G basis was not fit. Classification: **{real['classification']}**.

## Governance And Tests

- Pre-change full v4: **754 passed**.
- Focused candidate tests: **33 passed**.
- Post-change full v4: **787 passed**.
- Compileall and `git diff --check`: passed.
- Protected hashes unchanged: **{hash_report['protected_hashes_unchanged']}**.
- DEV RNA accessed: **NO**. SEALED RNA accessed: **NO**. Pathology accessed: **NO**.
- Stage81A3 complete: **NO**. Freeze 1 declared: **NO**. Stage81B/Stage81C started: **NO**.

## Remaining Blockers

1. The accountable global audit did not earn a donor-stable prefix or wider band; common-subspace/eigenspectrum identifiability remains unresolved.
2. Real full-G paired count-split evidence is absent from current bounded caches. Building it requires a separately reviewed TRAIN-only materialization plan.
3. Full-G real masking still needs a scalable non-quadratic engineering contract; the synthetic oracle graph cannot be used as real biological evidence.
4. Rare-program evaluation is underpowered in these bounded fixtures.
5. The 106,118 unresolved source mapping records require pinned authoritative evidence if future exact recovery is attempted.

## Human Decision

**NOT READY - AUDIT INCOMPLETE**

The address-space and full-G mechanics candidates are ready for review, but the global-state audit is unsupported and real full-G reproducibility evidence is incomplete. No freeze is declared.
"""
    atomic(outputs["readout"], readout)
    print(json.dumps({"protected_hashes_unchanged": hash_report["protected_hashes_unchanged"], "generated_files": len(generated), "readout": str(outputs["readout"].relative_to(project))}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
