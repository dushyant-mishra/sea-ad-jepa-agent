"""Planted failures against the Phase-IV freeze/binding execution path.

Scope
-----
PR #153 already carries 17 failure-injection tests for the *training-step*
execution path - gradient reports, optimizer step chronology, Adam moments,
EMA/cursor ordering and incomplete checkpoints - and the six inline gradient
negative controls on ``review/v27-authority-root-inventory-20260925`` already
prove a damaged update stops before the optimizer and the EMA. None of that is
reimplemented here.

What was NOT covered anywhere is the path that actually broke: the Phase-IV
bound-input binding and the execution-contract builder that stands on it. These
adversaries attack that path, including the one repair the lane is forbidden to
make - editing the frozen digest so the workflow goes green.

Two rules are enforced for every adversary
------------------------------------------
1. **Name the exact refusal point.** Each case declares the message fragment it
   must refuse with. A test that only asserts "it raised" would pass even if an
   unrelated gate fired first, which is precisely the masking defect that turned
   two of the five original failures into collateral.
2. **Never assume an exception rolled anything back.** Every case records the
   observable state before and after - the contract artifact the builder would
   emit, the frozen records on disk, the planner bytes - and requires it
   unchanged. An exception is evidence that control left the function, not
   evidence that nothing was written.

On the state the brief asks about: this path has no optimizer, teacher, EMA or
schedule cursor, because TRAINING=OFF and none of it runs training. Rather than
assert that from the design, each case checks that no optimizer, EMA, cursor or
checkpoint artifact was created, so the claim is measured rather than assumed.

Nothing here opens an Audit-B N1 burden outcome, a terminal masking result,
D_shared, G5, pathology or DEV/SEALED data, and nothing authorizes training.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

SCHEMA = "V5_LANE_C_FREEZE_EXECUTION_ADVERSARIES_V1"

REPO_ROOT = Path(__file__).resolve().parents[3]

SAMPLE_REL = (
    "analysis/v5_full104_information_channel_redteam_20260920/evidence/phase_iv/"
    "AUDIT_B_FROZEN_TARGET_SAMPLE.json"
)
SUCCESSOR_REL = (
    "analysis/v5_full104_information_channel_redteam_20260920/evidence/phase_iv/"
    "AUDIT_B_BOUND_INPUT_SUCCESSOR_V2.json"
)
RECEIPT_REL = (
    "analysis/v5_lane_c_planner_freeze_repair_20260926/evidence/"
    "PLANNER_DEFAULT_PATH_EQUIVALENCE_V1.json"
)
PLANNER_REL = "src/sea_ad_jepa/v5/full104_masking_streaming_executor_v1.py"
FROZEN_PLANNER_COPY_REL = (
    "analysis/v5_lane_c_planner_freeze_repair_20260926/evidence/"
    "frozen_planner_source__143645be.pysrc"
)
BUILDER_REL = "scripts/agent/build_full104_audit_b_execution_contract_v1_20260921.py"
ESTIMATOR_REL = "src/sea_ad_jepa/v5/audit_b_production_burden_v1.py"

#: Artifacts whose bytes must be identical before and after every refusal.
WATCHED = (SAMPLE_REL, SUCCESSOR_REL, RECEIPT_REL, PLANNER_REL, FROZEN_PLANNER_COPY_REL)

#: Names that would indicate training-side state was created by a refused run.
TRAINING_STATE_GLOBS = (
    "*optimizer*",
    "*ema*",
    "*cursor*",
    "*checkpoint*",
    "*.ckpt",
    "*.pt",
    "COMMIT.json",
)


def sha256_file(path: Path) -> str | None:
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def snapshot(root: Path, out_path: Path) -> dict[str, Any]:
    return {
        "watched": {rel: sha256_file(root / rel) for rel in WATCHED},
        "contract_artifact_exists": out_path.exists(),
        "contract_artifact_sha256": sha256_file(out_path),
        "training_state_artifacts": sorted(
            str(p.relative_to(out_path.parent))
            for pattern in TRAINING_STATE_GLOBS
            for p in out_path.parent.glob(pattern)
        ),
    }


# --------------------------------------------------------------------------- #
# Fixtures for the builder
# --------------------------------------------------------------------------- #

HEAVY_SHA = "f77dff47df71e2b97895f6e850db4d2a2ebdab441d195dedf91f582b4d53b5ae"
FULL104_SHA = "66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29"
REGISTRY_SHA = "7d61ed7bb649d129496c45cdf49adbb8b85faf7330803803287a2ec93631e4fd"


def write_heavy(path: Path, *, schema: str) -> None:
    path.write_text(
        json.dumps(
            {
                "schema": schema,
                "verdict": "HEAVY_ARTIFACT_QUALIFIED_FOR_REUSE",
                "artifact_sha256": HEAVY_SHA,
                "artifact_sha_matches_bound": True,
                "block_manifest_sha256": FULL104_SHA,
                "rows_traversed": 4_553_407,
                "donors": 104,
                "core_addresses": 17_186,
                "three_route_total_agreement": True,
                "all_104_donor_library_totals_agree": True,
                "per_cell_source_vector_agrees": True,
                "terminal_masking_outcomes_inspected": False,
                "training_authorized": False,
            }
        ),
        encoding="utf-8",
    )


def write_rng(path: Path, *, schema: str) -> None:
    from sea_ad_jepa.v5.masking_rng_replay_authority_v3 import (
        MaskingRngReplayAuthorityV3,
    )

    authority = MaskingRngReplayAuthorityV3(
        authority_id="LANE_C_ADVERSARY_RNG_V3",
        full104_substrate_sha256=FULL104_SHA,
        canonical_registry_sha256=REGISTRY_SHA,
        outer_split_receipt_sha256="1" * 64,
        qualification_parameters_authority_sha256="2" * 64,
        burden_ladder_authority_sha256="3" * 64,
    )
    path.write_text(
        json.dumps(
            {
                "schema": schema,
                **authority.__dict__,
                "global_seed": authority.global_seed,
                "authority_sha256": authority.canonical_digest(),
                "target_panel_dependency": "NONE__PANEL_SELECTION_MUST_NOT_REROLL_MASKS",
                "terminal_outcomes_inspected_before_freeze": False,
                "training_authorized": False,
            }
        ),
        encoding="utf-8",
    )


def run_builder(
    workdir: Path,
    *,
    repo: Path,
    sample: Path | None = None,
    heavy_schema: str = "V5_FULL104_HEAVY_SUFFICIENT_STATISTICS_QUALIFICATION_V2",
    rng_schema: str = "V5_MASKING_RNG_REPLAY_AUTHORITY_V3",
) -> tuple[subprocess.CompletedProcess, Path]:
    workdir.mkdir(parents=True, exist_ok=True)
    heavy = workdir / "heavy.json"
    rng = workdir / "rng.json"
    out = workdir / "contract.json"
    write_heavy(heavy, schema=heavy_schema)
    write_rng(rng, schema=rng_schema)
    proc = subprocess.run(
        [
            sys.executable,
            str(repo / BUILDER_REL),
            "--sample-freeze",
            str(sample if sample is not None else repo / SAMPLE_REL),
            "--heavy-qualification-receipt",
            str(heavy),
            "--rng-authority",
            str(rng),
            "--burden-estimator-source",
            str(repo / ESTIMATOR_REL),
            "--out",
            str(out),
        ],
        cwd=repo,
        capture_output=True,
        text=True,
        timeout=300,
    )
    return proc, out


# --------------------------------------------------------------------------- #
# Adversaries
# --------------------------------------------------------------------------- #


def _mirror_repo(tmp: Path, repo: Path) -> Path:
    """A writable mirror of only the files an adversary needs to corrupt."""
    mirror = tmp / "mirror"
    for rel in (
        SAMPLE_REL,
        SUCCESSOR_REL,
        RECEIPT_REL,
        PLANNER_REL,
        FROZEN_PLANNER_COPY_REL,
    ):
        dest = mirror / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(repo / rel, dest)
    # the remaining bound inputs must exist for the binding walk to reach the
    # role under attack
    frozen = json.loads((repo / SAMPLE_REL).read_text(encoding="utf-8"))
    for rec in frozen["bound_inputs"].values():
        dest = mirror / rec["path"]
        if not dest.exists():
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(repo / rec["path"], dest)
    return mirror


def adv_silent_hash_bump(tmp: Path, repo: Path) -> dict[str, Any]:
    """THE prohibited repair: edit the frozen record so the digest matches.

    This is the adversary the whole lane exists to refuse. Rewriting the
    recorded planner digest makes the bound-input walk trivially pass, so the
    only thing standing between a false green and a real one is that the freeze
    digest is itself pinned in code.
    """
    from sea_ad_jepa.v5.audit_b_execution_preflight_v1 import (
        verify_phase_iv_sample_freeze,
    )

    mirror = _mirror_repo(tmp, repo)
    frozen = json.loads((mirror / SAMPLE_REL).read_text(encoding="utf-8"))
    frozen["bound_inputs"]["planner_source"]["sha256"] = sha256_file(
        repo / PLANNER_REL
    )
    (mirror / SAMPLE_REL).write_text(json.dumps(frozen, indent=2), encoding="utf-8")
    try:
        verify_phase_iv_sample_freeze(mirror / SAMPLE_REL, repo_root=mirror)
    except ValueError as exc:
        return {"refused": True, "point": str(exc)}
    return {"refused": False, "point": None}


def adv_hash_bump_with_recomputed_internal_digest(
    tmp: Path, repo: Path
) -> dict[str, Any]:
    """The more careful forgery: bump the digest AND repair the freeze digest.

    An attacker who notices the internal digest check will recompute it. The
    pinned PHASE_IV_SAMPLE_FREEZE_DIGEST constant is what stops them.
    """
    from sea_ad_jepa.v5.audit_b_execution_preflight_v1 import (
        _canonical_freeze_digest,
        verify_phase_iv_sample_freeze,
    )

    mirror = _mirror_repo(tmp, repo)
    frozen = json.loads((mirror / SAMPLE_REL).read_text(encoding="utf-8"))
    frozen["bound_inputs"]["planner_source"]["sha256"] = sha256_file(
        repo / PLANNER_REL
    )
    frozen["freeze_digest"] = _canonical_freeze_digest(frozen)
    (mirror / SAMPLE_REL).write_text(json.dumps(frozen, indent=2), encoding="utf-8")
    try:
        verify_phase_iv_sample_freeze(mirror / SAMPLE_REL, repo_root=mirror)
    except ValueError as exc:
        return {"refused": True, "point": str(exc)}
    return {"refused": False, "point": None}


def adv_planner_moves_again_after_the_successor(tmp: Path, repo: Path) -> dict[str, Any]:
    """A waiver must expire the moment the file it names moves again."""
    from sea_ad_jepa.v5.audit_b_bound_input_successor_v2 import load_successor
    from sea_ad_jepa.v5.audit_b_execution_preflight_v1 import (
        verify_phase_iv_sample_freeze,
    )

    mirror = _mirror_repo(tmp, repo)
    successor = load_successor(mirror / SUCCESSOR_REL, repo_root=mirror)
    planner = mirror / PLANNER_REL
    planner.write_text(
        planner.read_text(encoding="utf-8") + "\n# a later, unreviewed edit\n",
        encoding="utf-8",
    )
    try:
        verify_phase_iv_sample_freeze(
            mirror / SAMPLE_REL, repo_root=mirror, successor=successor
        )
    except ValueError as exc:
        return {"refused": True, "point": str(exc)}
    return {"refused": False, "point": None}


def adv_successor_waives_an_untouched_role(tmp: Path, repo: Path) -> dict[str, Any]:
    """A waiver written ahead of time, to be cashed in later, must be rejected."""
    from sea_ad_jepa.v5.audit_b_bound_input_successor_v2 import (
        assert_no_uncovered_supersessions,
        load_successor,
    )

    mirror = _mirror_repo(tmp, repo)
    successor = load_successor(mirror / SUCCESSOR_REL, repo_root=mirror)
    try:
        # planner_source has not drifted in this scenario
        assert_no_uncovered_supersessions(successor=successor, drifted_roles={})
    except ValueError as exc:
        return {"refused": True, "point": str(exc)}
    return {"refused": False, "point": None}


def adv_builder_refuses_on_drift_without_successor(
    tmp: Path, repo: Path
) -> dict[str, Any]:
    """End-to-end: the builder must refuse a drifted binding it cannot resolve."""
    mirror = _mirror_repo(tmp, repo)
    (mirror / SUCCESSOR_REL).unlink()
    # run the real builder against the mirror so the successor is genuinely absent
    proc = subprocess.run(
        [
            sys.executable,
            str(repo / BUILDER_REL),
            "--sample-freeze",
            str(mirror / SAMPLE_REL),
            "--heavy-qualification-receipt",
            str(tmp / "heavy.json"),
            "--rng-authority",
            str(tmp / "rng.json"),
            "--burden-estimator-source",
            str(repo / ESTIMATOR_REL),
            "--out",
            str(tmp / "contract.json"),
            "--repo-root",
            str(mirror),
        ],
        cwd=repo,
        capture_output=True,
        text=True,
        timeout=300,
    )
    return {
        "refused": proc.returncode != 0,
        "point": (proc.stdout + proc.stderr).strip().splitlines()[-1]
        if (proc.stdout + proc.stderr).strip()
        else "",
    }


def adv_downstream_refusal_is_not_masked_heavy(tmp: Path, repo: Path) -> dict[str, Any]:
    """A bad heavy receipt must refuse with ITS OWN reason, not an upstream one.

    Two of the five original failures were exactly this defect in reverse: the
    planner-drift refusal fired first and hid the refusal the test was checking
    for. Gate masking makes a suite report the wrong cause, so each gate's
    specific refusal must stay reachable.
    """
    proc, _ = run_builder(
        tmp / "heavy_v1",
        repo=repo,
        heavy_schema="V5_FULL104_HEAVY_SUFFICIENT_STATISTICS_QUALIFICATION_V1",
    )
    return {
        "refused": proc.returncode != 0,
        "point": (proc.stdout + proc.stderr).strip().splitlines()[-1]
        if (proc.stdout + proc.stderr).strip()
        else "",
    }


def adv_downstream_refusal_is_not_masked_rng(tmp: Path, repo: Path) -> dict[str, Any]:
    proc, _ = run_builder(
        tmp / "rng_v2",
        repo=repo,
        rng_schema="V5_MASKING_RNG_REPLAY_AUTHORITY_V2",
    )
    return {
        "refused": proc.returncode != 0,
        "point": (proc.stdout + proc.stderr).strip().splitlines()[-1]
        if (proc.stdout + proc.stderr).strip()
        else "",
    }


def adv_tampered_sample_membership(tmp: Path, repo: Path) -> dict[str, Any]:
    """Moving one target must break the freeze digest."""
    payload = json.loads((repo / SAMPLE_REL).read_text(encoding="utf-8"))
    payload["samples"]["N1"]["targets"][0] += 1
    bad = tmp / "tampered_sample.json"
    bad.parent.mkdir(parents=True, exist_ok=True)
    bad.write_text(json.dumps(payload), encoding="utf-8")
    proc, _ = run_builder(tmp / "tampered", repo=repo, sample=bad)
    return {
        "refused": proc.returncode != 0,
        "point": (proc.stdout + proc.stderr).strip().splitlines()[-1]
        if (proc.stdout + proc.stderr).strip()
        else "",
    }


#: name -> (callable, required refusal fragment)
ADVERSARIES: tuple[tuple[str, Callable[[Path, Path], dict[str, Any]], str], ...] = (
    (
        "silent_hash_bump_of_the_frozen_record",
        adv_silent_hash_bump,
        "Phase-IV sample freeze internal digest mismatch",
    ),
    (
        "hash_bump_with_recomputed_internal_digest",
        adv_hash_bump_with_recomputed_internal_digest,
        "runtime uses a different Phase-IV sample freeze",
    ),
    (
        "planner_moves_again_after_the_successor",
        adv_planner_moves_again_after_the_successor,
        "but the checkout contains",
    ),
    (
        "successor_waives_an_untouched_role",
        adv_successor_waives_an_untouched_role,
        "may not pre-authorize a future change",
    ),
    (
        "builder_refuses_drift_without_a_successor",
        adv_builder_refuses_on_drift_without_successor,
        "bound input drift for planner_source",
    ),
    (
        "downstream_heavy_v1_refusal_is_reachable",
        adv_downstream_refusal_is_not_masked_heavy,
        "qualification V2 is required",
    ),
    (
        "downstream_rng_v2_refusal_is_reachable",
        adv_downstream_refusal_is_not_masked_rng,
        "RNG authority V3 is required",
    ),
    (
        "tampered_sample_membership",
        adv_tampered_sample_membership,
        "digest",
    ),
)


def positive_control(tmp: Path, repo: Path) -> dict[str, Any]:
    """The builder must still SUCCEED on good inputs.

    Without this the refusals above prove nothing: a builder that refused
    everything unconditionally would satisfy every adversary and be useless.
    """
    proc, out = run_builder(tmp / "positive", repo=repo)
    payload = json.loads(out.read_text(encoding="utf-8")) if out.is_file() else {}
    return {
        "returncode": proc.returncode,
        "artifact_written": out.is_file(),
        "execution_authorized": payload.get("execution_authorized"),
        "precision_scope_id": payload.get("precision_scope_id"),
        "phase_iv_sample_freeze_digest": payload.get("phase_iv_sample_freeze_digest"),
        "stderr_tail": proc.stderr.strip()[-200:],
    }


def run_all(workdir: str | Path, *, repo: str | Path = REPO_ROOT) -> dict[str, Any]:
    root = Path(repo).resolve()
    base = Path(workdir)
    base.mkdir(parents=True, exist_ok=True)

    control = positive_control(base / "control", root)

    cases: list[dict[str, Any]] = []
    for name, fn, fragment in ADVERSARIES:
        case_dir = base / name
        case_dir.mkdir(parents=True, exist_ok=True)
        out_path = case_dir / "contract.json"
        # the builder-driven cases need their inputs before the snapshot
        write_heavy(
            case_dir / "heavy.json",
            schema="V5_FULL104_HEAVY_SUFFICIENT_STATISTICS_QUALIFICATION_V2",
        )
        write_rng(case_dir / "rng.json", schema="V5_MASKING_RNG_REPLAY_AUTHORITY_V3")
        before = snapshot(root, out_path)
        outcome = fn(case_dir, root)
        after = snapshot(root, out_path)
        cases.append(
            {
                "adversary": name,
                "refused": bool(outcome["refused"]),
                "refusal_point": outcome["point"],
                "expected_refusal_fragment": fragment,
                "refusal_point_matches": bool(
                    outcome["point"] and fragment in str(outcome["point"])
                ),
                "watched_artifacts_unchanged": before["watched"] == after["watched"],
                "contract_artifact_created": after["contract_artifact_exists"],
                "training_state_artifacts_created": after["training_state_artifacts"],
                "state_delta": {
                    rel: {"before": before["watched"][rel], "after": after["watched"][rel]}
                    for rel in WATCHED
                    if before["watched"][rel] != after["watched"][rel]
                },
            }
        )

    return {
        "schema": SCHEMA,
        "evidence_class": "SYNTHETIC_PLANTED_FAILURES__REAL_REPO_ARTIFACTS_READ_ONLY",
        "training_state_present_in_this_path": False,
        "training_state_check": (
            "no optimizer, EMA, schedule-cursor or checkpoint artifact may be created "
            "by any refused run; measured, not assumed"
        ),
        "pr153_training_step_adversaries": "ALREADY_COVERED__NOT_REIMPLEMENTED",
        "v27_inline_gradient_negative_controls": "PRESERVED__NOT_REIMPLEMENTED",
        "terminal_masking_outcomes_inspected": False,
        "training_authorized": False,
        "positive_control": control,
        "cases": cases,
        "all_refused_at_the_expected_point": all(
            c["refused"] and c["refusal_point_matches"] for c in cases
        ),
        "no_state_changed_on_any_refusal": all(
            c["watched_artifacts_unchanged"]
            and not c["contract_artifact_created"]
            and not c["training_state_artifacts_created"]
            for c in cases
        ),
    }


def main(argv: list[str] | None = None) -> int:
    import tempfile

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    parser.add_argument("--workdir", default=None)
    args = parser.parse_args(argv)

    if args.workdir:
        report = run_all(args.workdir)
    else:
        with tempfile.TemporaryDirectory() as tmp:
            report = run_all(tmp)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(report, indent=2, sort_keys=True) + "\n")

    ok = (
        report["all_refused_at_the_expected_point"]
        and report["no_state_changed_on_any_refusal"]
        and report["positive_control"]["returncode"] == 0
        and report["positive_control"]["artifact_written"] is True
    )
    for case in report["cases"]:
        print(
            f"{'REFUSED ' if case['refused'] else 'ACCEPTED'} "
            f"{'at expected point' if case['refusal_point_matches'] else 'AT WRONG POINT'} "
            f"| state_unchanged={case['watched_artifacts_unchanged']} "
            f"| no_artifact={not case['contract_artifact_created']} "
            f"| {case['adversary']}"
        )
    print(
        "positive control: returncode="
        f"{report['positive_control']['returncode']} "
        f"artifact={report['positive_control']['artifact_written']}"
    )
    print("ALL ADVERSARIES REFUSED AND NO STATE CHANGED" if ok else "ADVERSARY SUITE FAILED")
    return 0 if ok else 1


if __name__ == "__main__":  # pragma: no cover - CLI
    raise SystemExit(main())
