# Independent V29 historical-lineage and teacher-fidelity protocol red-team

Date: 2026-09-27

Scope: independent audit only. No training, no protected outcomes, no modification of Claude's active branch. This branch starts from `027866e8`.

## Finding A — the historical 50k discovery expression artifact inherits the same HVS/SEA-AD column-index defect

The exact historical discovery expression artifact used by the tiny tournament is SHA-256:

`4c50f1de2446b07bbf3199bba80ebc89749c8104cb7668664ed705dbfc579d92`

The local `FOUNDATION_DISCOVERY_EXPRESSION_AUDIT.json` records that exact SHA as its output. The repository materializer `scripts/v4/foundation_materialize_discovery_expression.py` constructs HVS/SEA-AD mappings from `stage81a2r_foundation_molecular_address_source_provenance_candidate.csv.gz`, then applies `source_to_address.get(int(c))` directly to h5ad sparse column indices `c`. That is the same positional assumption now proven wrong for HVS_COMMON and SEA_AD_COMMON: the provenance `source_feature_index` is the Ensembl-sorted family rank, while h5ad columns are in the file's own genomic ordering.

Therefore the exact 50k discovery archive is not merely "historical"; its HVS and SEA-AD gene labels are affected by the same semantic column scramble.

This is not inferred from filenames. The split archive physically available in the audit environment reconstructs to the exact NPZ SHA above.

## Finding B — R7 and R8 are directly affected, not merely adjacent to the defect

The R7 package imports `JEPA_TINY_TOURNAMENT_20260926.py`. The R8 probe requires `/tmp/jepa_tour_logexpr.npz` and `/tmp/jepa_tour_meta.csv`. Those are produced by `JEPA_TINY_TOURNAMENT_PREPARE_20260926.py`, which streams the exact 50k discovery NPZ above.

Reconstructing the historical selection from the exact freeze and per-operator metadata, without reading expression values, gives:

- selected cells: 1,561
- microglia-labelled cells: 361
- all selected source counts: 1,179 SEA-AD + 382 HVS
- microglia source counts: 233 SEA-AD + 128 HVS
- microglia operators: HVS operator 19 only, SEA-AD operator 25 only
- microglia donors: 23 HVS + 27 SEA-AD = 50

There are **zero NPH52 microglia** in the R7/R8 361-cell biological-program subset.

Both microglial source matrices are in the affected families. Hence the named-gene R7/R8 measurements (APOE, P2RY12, HLA-DRA programs, their partners, held-out RNA readouts, and housekeeping-gene target coordinates) are not valid biological measurements of those named genes as originally reported.

What survives from R7/R8 is limited to method/engineering observations that do not depend on the semantic identity of the scrambled columns: donor-split mechanics, abstention machinery, generic anti-leak tests, and similar structural checks. Their gene-specific biological conclusions must be rerun on decoded counts.

## Finding C — V44 is also affected

V44 explicitly binds its input to the same 50k NPZ SHA `4c50f1de...`. Its 2,600-cell historical tournament therefore consumes HVS/SEA-AD columns with scrambled semantic gene identity.

Consequences:

- the numerical PCA/ridge computations can still be reproducible;
- donor splitting and generic software mechanics can remain mechanically valid;
- named-gene exclusions and claims about biological gene panels are not trustworthy as written;
- held-out-RNA scores are scores on scrambled coordinates, not validated scores for the named biological genes represented by those coordinates;
- V44 cannot be used as evidence choosing a biological teacher architecture until replayed on decoded expression.

## Teacher-fidelity protocol red-team before outcome extraction

The freeze at `027866e8` is valuable because it precedes control extraction, but four ambiguities/defects should be repaired and re-frozen before compute.

### P0-1 — six cross-program tests, not nine

With three programs and "the other two programs" as readouts, the directed predictor→readout set contains 3 × 2 = **6** tests, not 9. The protocol should enumerate all six explicitly. If self-readouts are intended, that contradicts the stated no-self-prediction rule and must not be introduced silently.

### P0-2 — held-out donors make literal donor fixed-effect coefficients non-transferable

A ridge model fitted on training donors cannot apply learned dummy coefficients for donor identities that are absent from training. Therefore "donor × operator fixed effect" is not implementable literally under held-out-donor evaluation.

Use a transferable within-stratum construction instead, e.g. deterministic centering/residualization within donor×operator strata, with the exact rule frozen before outcomes. Do not fit evaluation-donor outcome effects on the training model.

### P0-3 — denominator authority is internally ambiguous

The target-state section still describes activity using the artifact/reference denominator, while the shared-denominator section requires a newly rebuilt denominator excluding every gene of both predictor and readout programs.

Only one definition can govern the result. Freeze the exact per-comparison denominator formula, including how unavailable genes are masked and exactly which control genes are excluded from the denominator, before extracting outcomes.

### P0-4 — program-level qualification rule is not defined

The current rule says a "program passes for a given readout." That is pair-level qualification. If later prose says a program itself is qualified, the protocol must predeclare whether:
- both cross-program readouts must pass,
- either one may pass, or
- only pair-specific claims are allowed.

The safest current interpretation is pair-specific only unless a program-level rule is frozen prospectively.

## Additional control note — ambient module

`MEG3` is not an obviously lineage-foreign neuronal-only marker in the same sense as SNAP25/SYT1/RBFOX3. If it remains in the ambient module, document the biological rationale prospectively. Otherwise remove it before outcome extraction and re-freeze the module. This is a design-quality concern, not evidence that the remaining ambient module is invalid.

## Current status

- Corrected 29-address FULL104 myeloid artifact: independently audited elsewhere at full scale.
- Historical R7/R8 named-gene science: **REQUIRES_DECODED_REPLAY**.
- V44 biological architecture evidence: **REQUIRES_DECODED_REPLAY**.
- Historical mechanics not dependent on semantic gene labels: retain only within their original narrow scope.
- Teacher-fidelity protocol: **RE-FREEZE_REQUIRED_BEFORE_CONTROL/OUTCOME EXTRACTION** for P0-1 through P0-4.
- Neural EMA teacher/student training: remains OFF.

