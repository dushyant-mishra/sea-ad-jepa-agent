# JEPA V2C isolated student runtime — scoped Docker fixture V1

**Purpose:** provide *new* OS/container enforcement absent from the existing #514 standalone verifier and #515 D1→V2C producer. **Not** a second verifier, a source issuer, a model trainer or an independent Macha security verdict.

## Architecture and trust separation

The host-side producer, originally developed on PR #515 and conservatively amended on draft PR #538, constructs a previously redacted D1 student view and a *self-supplied, currently unauthenticated* expected policy. It runs **outside** the container. `build_context_v1.py` verifies the **exact V9 candidate Git blob** (`3470ad2ad17f7cea72b9238f7b7f675a27614b70`), preserving the original #514 Git blob (`46b813fcbf598e12a2a9f209ca254d01aaeba784`) in historical source custody and copies only its standalone stdlib verifier, this project's bounded JSON entrypoint and Dockerfile into a new isolated context. The image is built **from this four-file context, not from the repository**. No #502 validator, teacher module, D1 producer, data archive, private registry, source credentials or full Git repository are copied into the final image. This does not prove no host-side leakage occurred *before* redaction or authenticate the supplied policy.

The Docker fixture uses `--read-only --network none --cap-drop ALL --security-opt no-new-privileges --pids-limit 1 --memory 256m --user 65534:65534` with a small restricted `/tmp` tmpfs; the Python runtime uses `-I -S -B`. The stdin protocol contains **only** `student_view` and `expected_policy`, size-limited to 1 MiB; the output is a non-authorizing V2C consistency receipt or constant refusal. It does not expose exception details or open network connections.

**Fail-closed entry (Macha review proposal, PR #523; requires independent GPT review).** The packaged files are root-owned, so the runtime user cannot rewrite its verifier even if `--read-only` is omitted. The default entrypoint gives the constant refusal unless the documented restrictions are observable from inside the container:
- UID/GID 65534;
- no capabilities and `NoNewPrivs`;
- a seccomp filter;
- loopback only;
- a single visible PID;
- a read-only root;
- no mounts outside the engine's own paths and the `/tmp` tmpfs;
- `pids.max = 1`;
- memory of at most 256 MiB.

This guards only against an omitted or weakened flag on the default entrypoint. It is **not an attestation**:
- An `--entrypoint` override or a hostile Docker operator bypasses it.
- Docker Desktop's outer filter hides `seccomp=unconfined`.
- `--ipc host` is not detected.
- The receipt still says nothing about where it was computed.

## CI and attack evidence

`python -m unittest discover -s tests/v5/td_unified -p 'test_student_v2c_container_runtime_v1.py' -v` runs on Linux CI with Docker. Nine tests probe the exact candidate-pinned blob, a minimal image context, fixture receipt equivalence, package/import denial, filesystem write denial and no host secret paths, PID-limited child creation, outbound network denial, effective Docker flags, constant denial behavior and isolated `sys.path`. CI prints its **actual** image identity. No protected source data are used.

The Docker base `python:3.11-slim-bookworm` is a mutable tag, **not a digest-pinned base**. CI proves the documented commands executed on its runner, not bit-for-bit base reproducibility. The author run is *not* an independent penetration test of container breakout, side channels, privileged Docker daemon attacks, host mount misconfiguration, Linux kernel flaws, or user-controlled Docker flags. The default seccomp and namespace behavior is inherited from the CI Docker engine, not independently audited. There is no claim about Windows/WSL or GPU deployment isolation.

## Explicit remaining blockers

1. Independent Macha security verdicts on exact unchanged #514 and #515 source, followed by an independent review of this new deployment fixture.
2. Actual production/WSL isolation decision, base-image digest pinning, container engine and privilege model acceptance, and privilege separation between issuer, producer, student, and host orchestration.
3. Authenticated source-rights issuer, source feature/alias closure, donor/specimen and depositor QC proof, q-independent selection and upstream masking.
4. Complete cumulative Task4/5, Task6 unit registration, Task7 authenticated target bundle, Task8 rights-bound student consumer and separate training authorization. Current `TARGET=NONE` remains.

**Standing:** `TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`.

**Progress custody:** preserve original #514/#515 reviewer heads; publish this implementation/CI on its own PR, append exact evidence to audit #322, and update active handoff #460, with source-pinned chronology on each significant change.
