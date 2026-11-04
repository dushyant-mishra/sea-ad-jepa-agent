# Exact-source model audit before synthetic JEPA rehearsal — 2026-11-04

**Purpose:** Stop accidental use of older V4-only or current-main unguarded EMA/update mechanics when preparing the owner-authorized expanded synthetic development experiment. This is a source audit and non-authorizing model-readiness track, not a new model or target scientific qualification.

## Source-of-truth decision

Inspected original 535-PR latest-head census, PR #219/222/224/228/234 (V5 runtime line), #351/#444/#525 (post-TD target architecture and EMA policy), #537 (separate proposed GPU-only 4K Stage81A3 matched synthetic experiment), #547 (actual verified 2048-address FIT-only development dataset), canonical audit #322 and active handoff #460. Compared **actual Git blob identities**, not PR numbers alone.

| Actual software function | Exact correct source | Git blob SHA-1 | Later-head conclusion |
|---|---|---|---|
| Molecular encoder for V5 reference with keyed dropout / packed evidence | `src/sea_ad_jepa/v5/keyed_dropout_prototype_v2.py`: `KeyedIPBEncoderV2Reference` | `0fd06ae0891625924761ef097b20ba6e11495cb3` | Same blob at #224, later #228, #234, #525, and checked current main. **Inactive/scalar-Philox reference**, not production GPU kernel. |
| Gene identity/value tokens | `src/sea_ad_jepa/v4/gene_tokenizer.py` | `0fd283136323a49b5554f2fb33d0c65ee31be576` | V5 encoder imports this; matching at #224/main and previous source. |
| Predictor, block states and loss | `src/sea_ad_jepa/v4/ipb_jepa.py`: `BlockPredictor`, `gather_block_states`, `block_jepa_loss` | `3bd9d601a6779818a45c437cc21fd4a64749eb6e` | Same at #224, #228, #234, #525 and current main. V4 file name reflects unchanged low-level mechanics, **not** a stale replacement of V5 actor. |
| V5 measurement-aware packing/matched update objective | `src/sea_ad_jepa/v5/data_first_geometry.py` | `93b08f49f9d92b5c158e1a53fd5331b964f0e13f` | Same at main and #224; actual source support, not artificial right from model. |
| V5 numerical replay consumer | `src/sea_ad_jepa/v5/inactive_update_reference.py` | `ab266faa31ac7d3e51acf695a7deff1702368cde` | Same at #224/#228/#234/#525; **main older blob `3dc61b629c1d4723e7df058f72c1497c4b4c6c20` still contains direct optimizer/EMA mutation. Do not use it**. |
| V5 sole guarded optimizer-step and EMA mutation | `src/sea_ad_jepa/v5/inactive_guarded_update_v1.py` | `59647eb0122dfd98068844f68b6d48c2c33d67ca` | Same at #224/#228/#234/#525; absent on checked main. Uses `PrefreezeOptimizerGuardV1`; cannot authorize multi-update production training. |
| V5 native presentation EMA momentum | `src/sea_ad_jepa/v5/ema_presentation_v1.py` | `6f4442e25a6f891b9548b11403154233f616d842` | Same #224/#228/#234/#525, absent main. No current production half-life selected; constant EMA .996 from V4/#537 is historical, not current production policy. |
| V5 physical EMA continuation | `src/sea_ad_jepa/v5/ema_persisted_continuation_v2.py` | `865f6991dd5822a37aa223604799eefcf0eddb9f` | Same at #224/#228/#234/#525, absent main; not a substitute for training grant. |
| Downstream target family/architecture, NOT a new encoder | #525 `scripts/v5/jepa_post_td_harness_contract_v1.py`, tournament controller, presentation EMA | `76341dbe6e2ef505dfb84a4a69c6505c28c899b6`, `224ec83b0fc0d5d1f98a4d3655562635cb700b41`, `30b250495f123aaf3d8e6b17f2bd78655d82668c` | Current later scientific/architecture source: C1/C2/C3 coexist, C5 specialist, C6=C1+C3, C4=C1+C2+C3 with separate qualified C6 comparator. Uses presentation EMA. #525 latest independent Macha review pending; caller PASS strings are not external qualifications. **No fake PASS created here.** |
| GPU historical JEPA-only proposed experiment | #537 `stage81a3_ipb_jepa_only_postrepair_rerun_20261104.py` | PR head `7e8ff44120fd7acda9046d0f509fab504b4f73f3` | Later-date GPU script reuses historical 4K V4 IPB/constant .996 and its original planted 8192×4096 worlds. It is an *unexecuted proposal*, NOT newer selected V5 encoder/EMA and not a reason to duplicate 500 updates. |

## Resolution

The newest verified **V5 reference mechanics** use `KeyedIPBEncoderV2Reference` + the existing unchanged `BlockPredictor` + independently guarded V5 update + presentation-normalized EMA. The later #228/#234/#525 heads carry **identical source blobs** for that actor/runtime; no verified later replacement is found in the inspected project-wide PR census and newer named source lanes. They do have additional **separate scientific policy / rights** changes and must not be conflated with model mechanics.

**Source pin for this new development track:** PR #224 exact head `9d00684e08ba34ef8d7b04e478b9c380cd36d537`, rather than source from PR #547's older #328 ancestry. The actual synthetic observations are passed as an **external, SHA-bound artifact from PR #547**, never grafting the older generator branch into the model runtime. No production trainer activation; first permitted step is exact artifact/source preflight and **u0 forward/loss with zero optimizer/EMA steps**.

**No-C-pass boundary:** PR547's measured 2048-address FIT does not prove any of six C1–C6 targets; original spent TD57B/TD59/#314 and historical R5/Stage81B results remain complete and unchanged. A successful u0 means topology/rights/numerical mechanics can run, not that biology is learned. Separate signed/verified producer, Macha independent #547/#525/current V5 review, Task4 #541 HOLD, and owner training decision remain open. Do not run GPU or train by calling a diagnostic wrapper repeatedly.

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
