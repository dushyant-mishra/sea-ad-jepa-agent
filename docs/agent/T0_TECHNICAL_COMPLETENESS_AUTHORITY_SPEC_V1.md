# T0 Technical Completeness Authority Specification V1

Status: **EXTERNAL INTERFACE FREEZE — 2026-09-08**

Exact recovered summaries from accepted `t0_confirmation_raw_v1.py`:

Per accepted broad-IMMUNE cell:
- `qdepth_cell = log1p(source_library)`
- `qdetect_cell = count_nonzero(A) / 35076`

where A is the complete 35,076-address B1 projection for that cell.

Per donor:
- `Q_DEPTH = mean(qdepth_cell)`
- `Q_DETECT = mean(qdetect_cell)`

Q_DETECT uses all 35,076 scalar-measured addresses, not only the 28,061 SCORING addresses.

Required parent bindings include accepted membership, B1 feature/projection roots, B2 substrate roots, IMMUNE support-count root, and exact accepted Q-formula implementation identity.

Only after all parent authorities pass globally:

`technical_complete(d)=True`

iff the owner-frozen threshold-free definedness/computability conjuncts hold, including lawful accepted cells, computable finite Q_DEPTH, and computable finite Q_DETECT in [0,1].

No magnitude cutoff on Q_DEPTH, Q_DETECT, or donor cell count is permitted.

Authority/provenance failures are global STOPs and never donor-level technical incompleteness.

Output one row per candidate donor:
- donor_id
- cells
- Q_DEPTH
- Q_DETECT
- technical_complete

Expected candidate coverage: 46 donors. `real_execution_ready=False`.
