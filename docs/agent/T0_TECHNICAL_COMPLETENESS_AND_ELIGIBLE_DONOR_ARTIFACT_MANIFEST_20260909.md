# T0 technical completeness and eligible donors — artifact manifest and hash report

The technical-completeness production run over the real 20,804-row population,
and the eligible-donor authority derived from it. Both executed from committed
code and both replayed from disk.

## Why the artifacts are referenced rather than committed

`outputs/` is gitignored deliberately. Committing a package member as tracked
text lets the platform line-ending filter rewrite its bytes on checkout, which
changes its SHA-256 and therefore breaks the package root the member is bound
by. That failure already happened once in this lane: a frozen availability
package committed as tracked text produced `a4424482…` on a fresh checkout
instead of `e49c4e93…`.

So the artifacts are named here by exact path, size and SHA-256, with the
package root, and a reviewer reproduces them by running the committed runners.

## Reproducing

    python scripts/v4/t0_technical_completeness_production_run_v1.py \
        --outdir outputs/t0_technical_completeness_20260909 \
        --store "<phase2>/expression_level4" \
        --membership "<accepted membership csv>" \
        --population-pkg outputs/t0_b2_production_20260909 \
        --feature-split "<T0_MTG_FEATURE_ROLE_SPLIT_V2.csv>"

    python scripts/v4/t0_technical_completeness_replay_v1.py \
        --pkgdir outputs/t0_technical_completeness_20260909 \
        --store "<phase2>/expression_level4" \
        --membership "<accepted membership csv>" \
        --population-pkg outputs/t0_b2_production_20260909

    # the stronger form: recomputes every donor summary from the substrate
    #   ... as above, plus
    #   --feature-split "<T0_MTG_FEATURE_ROLE_SPLIT_V2.csv>" --rederive

    python scripts/v4/t0_eligible_donor_production_run_v1.py \
        --outdir outputs/t0_eligible_donor_20260909 \
        --at8-pkg outputs/t0_at8_availability_20260908 \
        --tc-pkg outputs/t0_technical_completeness_20260909 \
        --age-sex-pkg outputs/t0_age_sex_20260908 \
        --population-pkg outputs/t0_b2_production_20260909

    python scripts/v4/t0_eligible_donor_replay_v1.py \
        --pkgdir outputs/t0_eligible_donor_20260909 \
        --at8-pkg outputs/t0_at8_availability_20260908 \
        --tc-pkg outputs/t0_technical_completeness_20260909 \
        --age-sex-pkg outputs/t0_age_sex_20260908 \
        --population-pkg outputs/t0_b2_production_20260909

## Code identities

    TC runner            d881d86c5b11e2294fefa6f30fdb2b8df6bf8b3d351ba727d0a8197a32185aac
    TC authority module  64cea54a67c5ab9e3c81bb7779a52653205c2c36b98645b7a3d7b4b0ec82fb49
    ED runner            871bc817294193ec1f0e6157315ba21902aee5c5db983a3d46bec2f8ee77bbf8
    ED authority module  b25353593fada7ce13b4d7e6641273a131fc3133c1c8776f344a01bd893283bc

**Read this label carefully, because the lane has been getting it wrong.** These
are the plain SHA-256 of each file's LF-normalized content. They are *not* Git
blob digests: a Git blob digest frames the content as `b"blob <len>\0" + content`
and gives a different value. Measured on the TC authority module:

    recorded in the package  64cea54a67c5ab9e3c81bb7779a52653205c2c36b98645b7a3d7b4b0ec82fb49
    sha256 of LF content     64cea54a67c5ab9e3c81bb7779a52653205c2c36b98645b7a3d7b4b0ec82fb49   <- match
    sha256 of blob framing   6045f84cd1ea7f642f2b91b15756be7e3bb9bdd97fd53224f88f1d04b6f81c4d
    git hash-object          0e8c701b5213a36fc7983b0c6890c93514eb2e9d

The eligible-donor package states this method accurately. The
technical-completeness, B2 population raw-source, AT8 availability and age/sex
packages all record the same LF-content SHA-256 but *label* it
`GIT_BLOB_BYTES__NOT_WORKTREE_BYTES`, which is false. See the finding in the
pre-real-T0 handoff; it is reported rather than silently re-stamped because
correcting it changes those packages' roots.

## Technical completeness — package

    outputs/t0_technical_completeness_20260909/

    T0_TECHNICAL_COMPLETENESS_MANIFEST.csv               241  aad840e94053cc6650ccc5e309346eed6e1136033b20a6564e76054281094d61
    T0_TECHNICAL_COMPLETENESS_METADATA.json             2144  a6b387be0f4ab6d5af67d8208fa2e973e4b6a90acb5e536748642856d9916954
    T0_TECHNICAL_COMPLETENESS_REGISTRY.csv              2350  c898b378e0008ebdeb50f53843aea33fa6dbc8462aa7a32ee5c72564f5e6da11
    T0_TECHNICAL_COMPLETENESS_PACKAGE_ROOT_SHA256.txt     65  5e79b70ddd17cd20dd79fd984da944a1ca3b1937e10daff9a28881327f051c17
    T0_TECHNICAL_COMPLETENESS_RUN_SUMMARY.json          1940  c32fa098d543e0580a53848df9c0b2c72c4982fe24eb4454e08eab7492ffa4a0

Roots:

    completeness root      360381dc7625386a58c1aa0b262de3e55e9835bc32808f86b663d944ec453470
    parent contract root   9d4e818e20077c42c5500b4df35c385dd1a43cb53375da3a7b4d738257ff5ba5
    package root           0164bccc76ad7ed9385de01fd0ab885dd80770afad0b94ee189e9084ee3cfe99
    projection root        ef6ccdde0e0268cce819b4e543d7d542120811fa3762225964f78f9172f370e7

Parents, all reproduced by the replay from the frozen inputs:

    population closure     ec350b8d9a30a8a08573f055b9a0c103d0f6805014998ac9975d94585421d397
    logical row authority  64ea880ff6cf19aca48e0f2e77edfa6d37fc4f5e20022011131c496173896fc3
    physical read plan     cc75cef0ebb9a05e6699546e18ae45b3555f488dc2e46db4c845370c5be23519
    population raw-source  0b3e44897f0a5af1951677af95110e16d46f9a285fe227c31e34f45137b98f1b
    B2 authority package   98eac4a68df7960e79739d236cf0febacdec52a33de76144b146dc29a5a64436

As measured:

    donors                     46
    cells consumed             20,804
    technically complete       46 of 46
    projection positions       35,076
    counts payload reads       3,126
    counts payload cache hits  17,678
    elapsed                    2,374.9 s

    cells      min 67            median 387            max 964
    Q_DEPTH    min 8.19262711    median 8.62742084     max 8.9972022
    Q_DETECT   min 0.0578090262  median 0.0752486785   max 0.096597957

`production_run_status` is
`DERIVED_OVER_THE_REAL_POPULATION_FROM_AUTHENTICATED_B2_PARENTS`, decided by
measured coverage rather than by a caller flag, and the retired terminal
`SYNTHETIC_ONLY__PRODUCTION_B2_NOT_RUN` is absent.

### The cost of the walk order, measured

The derivation walks `logical["rows"]` in frozen membership order, which is
almost perfectly interleaved with respect to the counts blocks: 19,953
contiguous runs across 20,804 rows, so essentially every consecutive row lives
in a different block. Against the 1,246 op31 counts blocks totalling 7.35 GB:

    walk order / cache        block loads   bytes read
    no cache                       19,953    114.84 GB
    LRU(48), what ran               3,126     18.35 GB
    block-major locality            1,246      7.35 GB

The run's own counter recorded 3,126 payload reads, matching the model exactly.

`build_physical_read_plan` exists precisely to supply block locality and is not
used for the walk, so the run pays 2.5x the I/O and CPU it needs to. This is an
efficiency observation, not a correctness defect: per-row work is
order-independent, rows are keyed by `logical_index`, and the donor reduction
uses `math.fsum`, which is exactly rounded and therefore depends only on the
multiset of per-cell values and not on their order. A block-major walk would
produce identical roots. Nothing was changed on this point.

## Eligible donors — package

    outputs/t0_eligible_donor_20260909/

    T0_ELIGIBLE_DONOR_MANIFEST.csv                       225  eab2ab9c68ff106630ef949bf9f844367bf2fc1b555147831399dc6ec2ddcc92
    T0_ELIGIBLE_DONOR_METADATA.json                     2241  38bb2b46c143d179bfb6242ef71a9e0b6f3ed55dff134e7d8682771d0f116e81
    T0_ELIGIBLE_DONOR_REGISTRY.csv                      5257  7bad8722f048f4125c5fceb9fd3a1fa00c1249d7853125a7f692a73ce73f650a
    T0_ELIGIBLE_DONOR_PACKAGE_ROOT_SHA256.txt             65  007ed31e525d01f00f6669d2ac59c9ce00b2f1f7b5049a60ee24ebfef7c18604
    T0_ELIGIBLE_DONOR_RUN_SUMMARY.json                  3047  86f9fe38b7c714a91f333de919c933254916057fcde02d5ed1d0bffd02277f43

Roots:

    eligible donor root    a5470b9f5389e0fa72b3ca51832c67d7419ed6447a85d6d979884b9fe1444f85
    donor role root        799261f54de158f4c24c33a51a674611fe4e5e68509fcbbca681216470fe10bd
    parent contract root   be92b2ac2b347f0da45690e264d1b224584cfb56131ac3df61a01480ad196ae8
    package root           af4b71413917cde7dd6b35686b3f8410e94ee323d436a2f4e125ff91b06980fd

Parents:

    at8_availability_package_root_sha256              3f74fa833bc1838a50d92bf3f6bdb55e6eafdb10b489fbfff142a4240466fc5a
    technical_completeness_root_sha256                360381dc7625386a58c1aa0b262de3e55e9835bc32808f86b663d944ec453470
    technical_completeness_package_root_sha256        0164bccc76ad7ed9385de01fd0ab885dd80770afad0b94ee189e9084ee3cfe99
    age_sex_package_root_sha256                      8212191a03f09d669a383be6a541b5ce3493b32c13608a76f197a88fa18ddf9b
    population_raw_source_root_sha256                0b3e44897f0a5af1951677af95110e16d46f9a285fe227c31e34f45137b98f1b
    b2_authority_package_root_sha256                 98eac4a68df7960e79739d236cf0febacdec52a33de76144b146dc29a5a64436

As measured:

    candidate donors      46      (from the proven B2 population, not a caller list)
    eligible donors       46
    CONFIRMATION          18
    DISCOVERY             28
    INELIGIBLE             0

Parent donor coverage, so the projection is visible rather than implied:

    at8_available        84 covered -> 46 used
    technical_complete   46 covered -> 46 used
    age_present          46 covered -> 46 used
    sex_present          46 covered -> 46 used

Every one of the four conjuncts is True for all 46 candidates, so eligibility
turned entirely on `technical_complete`, and that came out complete for all 46.

An earlier build of this package recorded a 40-character Git SHA-1 under
`derivation_code_sha256`, and a later one carried the false Git-blob label. Both
were superseded before this manifest; the packages are kept outside `outputs/`
rather than deleted. The decision roots are identical across all three builds —
only the package root moved — because the eligibility and role content never
changed, only the metadata provenance fields.

## Tail measurability, which is a separate question from completeness

    donors below the frozen 80-cell tail floor:  H20.33.037, 67 cells, DISCOVERY
    CONFIRMATION   n = 18,  tail-measurable 18
    DISCOVERY      n = 28,  tail-measurable 27

The frozen `tail_allowed_n` is `[17, 18]`, so the confirmation tail analysis is
executable at n = 18.

Note that H20.33.037 is `technical_complete = True` despite falling below the
80-cell floor. That is correct and deliberate: technical completeness is a
threshold-free definedness and computability predicate, and the 80-cell floor is
tail measurability only. The two were frozen as separate things and this run
shows them behaving as separate things.
