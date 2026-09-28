# JEPA V52 — Claude interrupted-work recovery and R2/R4 closeout

Date: 2026-09-28  
Governance: `TRAINING=OFF` · `TD60=BLOCKED` · no protected biological outcome opened

## Purpose

This successor SHA-pins the exact chat-recovered R2/R4 result archives, mirrors the exact recovered Claude R2 source archive required for reproducible testing, and closes one narrow test-coverage defect without rewriting any recovered historical file.

## Custody recovered

Three user-uploaded recovery archives were received and SHA-256 verified. The R2 source archive is mirrored into Git as base64 text because the successor regression executes it byte-for-byte; the result ZIP identities are SHA-pinned here without redundant binary mirroring:

- `out_stage75f-specificity.zip` — `be6614c58304a2b19c41b542f8379fb31e6adca39082d4982496344f9004c3b5`
- `out_seaad-spatial.zip` — `8dbe6faef5690207639b10b7818bedb743fbdf14b9dd5029d965b7d93c937420`
- `CLAUDE_R2_LOCAL_SCRIPTS.zip` — `337bd8823e006febc1f5103b00b48c7953e3a91e3fb257a4d02d90c04b4af571`

The exact recovered R2 producer is SHA-256 `6accb237a29718668146eb3dab5c54638c969363d71a40a95fbab3c88925ee1e` and the recovered V1 adversarial harness is `77ee49b6167b0181cc2bd46dcda91132ab22586ebaf7ed230d2958657a408ee7`.

## R2 execution status

The full Stage75F specificity run completed successfully; it does not need to be rerun.

- structural gate: PASS
- exact TF-label assignments enumerated: `3,628,800`
- direct TF-label exact p: `0.74769841`
- extended TF-label exact p: `0.846347`
- direct supply-preserving joint p (20,000 shuffles): `0.06464677`
- extended supply-preserving joint p (20,000 shuffles): `0.12014399`
- direct annotation-supply vs tier: Spearman rho `0.904431`, p `0.000325`
- extended annotation-supply vs tier: Spearman rho `0.764093`, p `0.010079`
- query-region mean pairwise Jaccard: `0.762838`
- enriched-motif mean pairwise Jaccard: `0.510163`

Interpretation: the R2 audit mechanics qualify, but the old Stage75F TF-specific hierarchy does not qualify as a validated TF/eRegulon hierarchy. The recovered report itself keeps `biological_regulatory_claim=NONE` and `validated_eregulon_network=false`.

Two narrow TF×scope hypotheses exceeded the annotation-supply null in the recovered tables and may remain exposed hypotheses; they do not rescue the global hierarchy.

## V1 mutation-harness defect and V2 successor

The recovered V1 adversarial harness contains five planted mutations. MUT-1 through MUT-4 exercise producer/helper behavior directly. MUT-5 independently calculates a constant permutation null rather than invoking the producer's actual exact TF-label permutation path. Therefore V1 does not by itself prove that the producer would detect a degenerate null.

Historical V1 bytes are preserved unchanged.

Successor `laneR2_mut5_producer_path_regression_v2.py` constructs a synthetic/technical fixture in which every batch enriches the full motif collection, then executes the recovered producer as a subprocess. Annotation rows remain structurally movable, while each TF has batch-invariant support, forcing every batch-label assignment to the same trace.

Observed V2 result:

- producer exit: 0
- structural gate: PASS
- exact permutations: 720
- direct null distinct values: 1
- extended null distinct values: 1
- direct `null_is_degenerate_constant`: true
- extended `null_is_degenerate_constant`: true
- producer identifiability degeneracy flag: true
- verdict: `PASS_PRODUCER_DEGENERACY_PATH_EXERCISED`

This closes the narrow MUT-5 producer-path coverage gap without altering the scientific R2 result.

## R4 spatial structural status

The recovered R4 JSON is internally coherent but its producer/logs were not present in the uploaded R4 archive. It is therefore retained as a recovered structural result, not a fully producer-custodied execution package.

Its scientific implication is unchanged: current SEA-AD spatial assets do not measure the complete three-program relational state. The homeostatic program is absent from all four panels, lipid/DAM coverage is absent in MTG/HIP/MEC and only partial in CaH Xenium, and several MERSCOPE/MERFISH assets show substantial microglial detection/segmentation asymmetry. Spatial is supporting evidence, not a primary full-state validation axis.

## Current decision state

- R2 20,000-shuffle run: **RECOVERED / COMPLETE**
- R2 producer: **RECOVERED**
- R2 V1 adversarial harness: **RECOVERED**
- R2 MUT-5 actual producer path: **V2 PASS**
- old Stage75F global TF hierarchy: **NOT QUALIFIED AS VALIDATED REGULATORY HIERARCHY**
- Stage75F artifacts/infrastructure: **RETAIN AS HISTORICAL / HYPOTHESIS-GENERATING**
- R4 spatial result: **RECOVERED STRUCTURAL RESULT; PRODUCER CUSTODY STILL OPEN**
- real regulatory biological outcome opening: **NOT AUTHORIZED BY THIS WORK**
- `TRAINING=OFF`
- `TD60=BLOCKED`

## Next scientific work

Stop spending compute on re-running R2. The load-bearing next problem is the RED positive discriminating signature from the V50 red-team. Work must remain synthetic/technical until a positive control survives prospective nuisance controls. The next design comparison should explicitly evaluate donor-stable cis modules, SCENIC+/eRegulon objects, chromVAR/motif activity, and direct peak/topic regulatory modules, with the identifying nuisance class and positive signature frozen before any scarce real biological outcome is opened.
