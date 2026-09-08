# Target Discovery forensic ledger — TD23 through TD29A

Status: `FALSIFICATION_ONLY__NO_TARGET_AUTHORITY`

This ledger supersedes any conversational interpretation of the affected pilot iterations.

## Mandatory row-addressing correction

The 50,000-row discovery matrix is stacked:
- rows 0–24,999 = `A_NATURAL_MIXTURE`
- rows 25,000–49,999 = `B_COVERAGE_DISCOVERY`

Inside the freeze CSV, `sample_row` resets to 0–24,999 for **both** samples.

Therefore a B-sample analysis must address expression by the global freeze-file row, not by B's reset `sample_row`.

### TD23 forensic result

Independent reconstruction using eight 256-gene panels on the 17,186 all-operator scalar addresses:

- correct global B-row addressing: median absolute HVS↔SEA_AD donor-pseudobulk dependency correlation = **0.0062546**
- deliberately aliased B `sample_row` addressing: median correlation = **0.3906061**
- GABA alias median = **0.407808**
- glutamatergic alias median = **0.328214**

This reproduces the magnitude of the prior TD19 positive result.

Decision:

`TD19_POSITIVE_DEPENDENCY_RESULT_INVALIDATED_BY_ROW_ALIAS_FORENSIC_MATCH`

TD19 SHA:
- `e413fee49ee73247f4daaf58c5a786ab0f9ccc0a6c1bcd686c14aa49bc95ca30`

TD23 hashes:
- script `88f1a7dbd0c0ad16617c4d8b71ab343e6ee2eb1e73a5647cf7f44b22242e6ea2`
- detailed CSV `4764aaffd0f42f7508cbbc13c6059d41608650d22ea0a8e4e9f9bf481131470c`
- summary CSV `cdcdfefc5de31704f0ef8eb9ff527bbdf6d0af93fe5e54fe037d0bd5aa431b4d`

## Dependency target after correction

Correctly indexed evidence is negative:

- TD21 raw and nuisance-residualized donor-pseudobulk dependency: cross-source correlations near zero.
- TD21B measurement-reliability strata, including top-10%/top-25% reliable genes: near zero.
- TD22 equal-donor within-donor Pearson dependency: near zero cross-source despite nonzero within-source donor reliability.
- TD22B within-donor Spearman dependency: near zero cross-source.

Key hashes:
- TD21 decision `895043fcb059068afd811ab9299bc8af8d1dd765ebc1b34c826d77225db92e71`
- TD21B summary `78de9d711f303db9bbde37e71ebd84b76322c1a89157344a0b8d2e1b3df0d72c`
- TD22 summary `fa86bae4fe03e7e6384f21750c2b2255579bcf3aa3b97d44b47e92d8fba242d8`
- TD22B summary `ad0e0a65a92a74e0446f108e1b893c3ac274e0441b4b2b478cb1aba95c9173ea`

Current classification:

`NO_REPLICATING_SAME_GENE_DEPENDENCY_GEOMETRY_ESTABLISHED_IN_50K_PILOT`

This does not prove impossibility on the 4.553M full population, but it removes TD19 as positive evidence.

## TD24 corrected depth pseudo-state attack

Correct global B rows + exact source_library + exact 8! matching included in randomized pseudo-state null.

Fixed depth-bin state geometry:
- glutamatergic median r = **0.161609**
- GABAergic median r = **-0.026289**

Optimized graph matching becomes large (~0.65–0.80) but does **not** exceed the same search performed on randomized pseudo-states.

Interpretation: depth ordering is not sufficient to explain the corrected annotated relational scaffold; graph matching itself has a large optimism floor.

Hashes:
- script `7e88b27b32aaa532e95d6bda1cb6ccb5dce41d7e61d5f4e53530db2b56d19d6c`
- detailed `5771f6e9cf39693af4de83ffc7d769a64d9f24a1dc805eb21476fb7b844a88ec`
- summary `d906e5c349651add9bcfea3b5086415d9d1a073675708fd7832b7771da6f4b72`

## TD25 corrected annotated relational scaffold

Independent correct-row regeneration.

Outcome-blind state inclusion rule: native class exists in HVS and SEA_AD with >=20 B-sample donors in each source. This yields 19 states.

Donor-balanced centroids; 17,186 common-scalar space; four independent 512-gene panels.

Raw median graph correlation:
- all 19: **0.851923**
- glutamatergic only: **0.937286**
- GABAergic only: **0.787551**

After per-state depth/detection residualization:
- all 19: **0.803842**
- glutamatergic only: **0.920890**
- GABAergic only: **0.735251**

This is validation evidence only because native/broad annotations define the state correspondence.

Hashes:
- script `6b0ed5fc7cc57d6e3400c752d2b693a91ceb08aa3f8a6381b609f756c06bf2f4`
- detailed `4bb128f53e4b7bbcf9f5c2548523e434eba8cd8a606d336ba74d137eb644a43e`
- selection `00a2853ec263c8c3649c8a7d2ca80a1784873d8d0352e00178f479256ac7895b`
- summary `315f3bbbb21cb82037d69248758602e5818886482719b12197634c690d380765`

Classification:

`CORRECTED_ANNOTATED_RELATIONAL_SCAFFOLD_REPRODUCES__VALIDATION_ONLY`

## Label-free discovery failures

### TD28 cell-level label-free states

Rejected:
- many states have 1–8 cells or 1–3 donors;
- donor-block stability output is empty;
- depth pseudo-states often match as well as/better than discovered states;
- only HVS↔SEA_AD clears random p95 across all panels and does not consistently clear depth.

Hashes:
- cross summary `71364da73745330c651287d67c47ff109c214879563f1b7267a967b044d9b0cb`
- state recurrence `79fd880213e9e86841ad1f27d7a434d4f2955a51955fd79feb9c13b724490522`
- empty donor-block file SHA `01ba4719c80b6fe911b091a7c05124b64eeece964e09c058ef8f9805daca546b`

### TD29A donor×operator label-free states

Also rejected.

Even after changing the discovery unit to donor×operator pseudobulks:
- several fitted states remain one pair / one donor / one operator;
- HVS donor-half match 0.8505, null max 0.9700
- NPH52 donor-half match 0.9463, null max 0.9739
- SEA_AD donor-half match 0.8544, null max 0.9102
- HVS↔NPH52 cross match 0.8181, null max 0.9410
- HVS↔SEA_AD cross match 0.7409, null max 0.9607
- NPH52↔SEA_AD cross match 0.8885, null max 0.9601

No comparison beats all null rediscoveries.

TD29A hashes:
- script `ad81057dd57ae00019c3d2fba56df17a0fb0ad7bdcb3ec6ea4234dd89152ae5f`
- cross `846c8fb5f3135d7fe877d0d9bd537ed345732afff9cb669511b4823c77543185`
- donor-half `dc006c50e72c33bf67983631ad8b137218b4eddb9c5db9a8ba4c50d0a11bd2c2`
- recurrence `154dab5e0c14cfc5d36f902bc06d910028059659fe188faff1a26df1ceea9819`

Classification:

`NO_VALID_LABEL_FREE_RELATIONAL_TARGET_ESTABLISHED_BY_GENERIC_CLUSTERING`

## Row-binding status for older B-sample pilots

Any pre-TD23 B-sample expression analysis whose exact row-addressing implementation is no longer available is `ROW_BINDING_UNVERIFIED` until independently regenerated or proven from source.

Do not use such an artifact for promotion.

Current overall terminal:

`NO_VALID_TARGET_ESTABLISHED_YET__ANNOTATED_RELATIONAL_SCAFFOLD_REPLICATES_BUT_LABEL_FREE_TRAINABLE_OBJECT_NOT_QUALIFIED`
