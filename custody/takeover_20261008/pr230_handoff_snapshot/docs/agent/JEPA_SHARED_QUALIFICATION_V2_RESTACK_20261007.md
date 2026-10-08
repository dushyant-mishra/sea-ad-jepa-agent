# Shared qualification V2 clean restack — 2026-10-07

Base runtime SHA: `9d00684e08ba34ef8d7b04e478b9c380cd36d537`

Donor shared-interface SHA: `71bf55dda89fa2099933160eeee734ab2167324d`

Restack branch: `reconcile/shared-qualification-v2-on-canonical-runtime-20261007`

The donor branch was **not** rebased or merged wholesale because it carried older copies of V5 runtime files. Instead, the restack transplanted only:

- `src/sea_ad_jepa/qualification/**`;
- `tests/qualification/**`;
- `tests/integration/test_shared_interface_v5_runtime_binding_v1.py`;
- `tests/integration/test_shared_interface_v5_ema_runtime_binding_v2_red.py`;
- `.github/workflows/shared-qualification-interface-v1.yml`.

Compare `9d00684e...` → initial restack `421daf4e...` is exactly one commit and 29 added files; no `src/sea_ad_jepa/v5/*` file changed.

Purpose of this restack:

1. validate `BoundRuntimeMutationProofV2` against the final canonical runtime rather than an older stacked copy;
2. keep `BoundRuntimeMutationProofV1` diagnostic-only;
3. keep executed q-safety proof separate from runtime mutation proof;
4. preserve the rich-teacher/partial-student non-authority boundary;
5. preserve the source-row/value coupling invariant;
6. prepare the joined V77 + shared-interface + runtime `ZERO_UPDATE` audit.

No training, Stage A, real-RNA, TEST, Morabito, 500K, Stage 4, target selection, uncertainty selection, or production EMA-timescale authority is granted by this restack.
