"""Physical controller-scoring orchestrator for V79 V2_CORE: custody, truth-open-last and write-once tests.

All end-to-end tests run on the synthetic universe in ``v79_v2_core_score_synthetic_universe``. No test
here reads real controller truth or real fit outputs. The orchestrator module is imported lazily so a
missing implementation fails each test instead of erroring at collection.
"""
from __future__ import annotations

import hashlib
import importlib
import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "v79"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_v79_v2_core_scoring as R  # noqa: E402
import v79_v2_core_score_authority as A  # noqa: E402
import v79_v2_core_score_evaluate as E  # noqa: E402
import v79_v2_core_score_synthetic_universe as UV  # noqa: E402
import v79_v2_core_score_truth as T  # noqa: E402

ORCHESTRATOR = "run_v79_v2_core_scoring_orchestrator"
FROZEN_NOT_DIAGNOSED = frozenset({
    "09bbe252aeb91c12eb996fbd60e5a420237ba4f317255278cdc6e4bfacf9daa6",
    "6ca5f0876ccdac9c86bf5b2f07a4413fdd9f8b824ec8ad45ae84090d657e2f43",
    "ede8a3a369d69133a85fa4a35a3bd24ca87e4a6c680599b671b9693efe7104a5",
})
BINDING_TO_CONSTANT = {
    "campaign_receipt_sha256": "CAMPAIGN_RECEIPT_SHA256", "custody_receipt_sha256": "CUSTODY_RECEIPT_SHA256",
    "result_ledger_sha256": "RESULT_LEDGER_SHA256", "result_file_count": "RESULT_FILE_COUNT",
    "root_manifest_sha256": "ROOT_MANIFEST_SHA256", "blinded_index_sha256": "BLINDED_INDEX_SHA256",
    "realization_audit_receipt_sha256": "REALIZATION_AUDIT_RECEIPT_SHA256", "realization_ledger_sha256": "REALIZATION_LEDGER_SHA256",
    "world_set_directory_digest": "WORLD_SET_DIRECTORY_DIGEST",
}


def _orchestrator():
    return importlib.import_module(ORCHESTRATOR)


@pytest.fixture(scope="module")
def pristine(tmp_path_factory):
    return UV.Universe.build(tmp_path_factory.mktemp("v79_scoring_universe") / "u")


@pytest.fixture
def universe(pristine, tmp_path, monkeypatch):
    u = pristine.copy_to(tmp_path / "u")
    u.patch(monkeypatch)
    return u


def _repatch(u, monkeypatch, *bindings):
    for key in bindings:
        monkeypatch.setattr(A, BINDING_TO_CONSTANT[key], u.bindings[key], raising=False)


@pytest.fixture
def truth_calls(monkeypatch):
    """Record every controller-truth loader call together with the barrier state at that moment."""
    calls = []

    def state():
        mod = sys.modules.get(ORCHESTRATOR)
        guard = getattr(mod, "TRUTH_GUARD", None) if mod else None
        return {"barrier_crossed": bool(getattr(guard, "barrier_crossed", False))}

    for owner, name in ((T, "load_truth_set"), (T, "load_truth_world"), (T.TruthWorld, "load")):
        original = getattr(owner, name)

        def spy(*args, __original=original, __name=name, **kwargs):
            calls.append((__name, state()))
            return __original(*args, **kwargs)

        monkeypatch.setattr(owner, name, spy)
    return calls


def _tree_hashes(base: Path, *, exclude: Path | None = None) -> dict[str, str]:
    out = {}
    for p in sorted(base.rglob("*")):
        if p.is_file() and (exclude is None or exclude not in p.parents):
            out[p.relative_to(base).as_posix()] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def _assert_refused_before_truth(u, truth_calls, *, match: str, **overrides):
    O = _orchestrator()
    with pytest.raises(O.OrchestratorRefused, match=match):
        O.run_qualification_scoring(**u.run_kwargs(**overrides))
    assert truth_calls == [], "controller truth loader was called before authentication completed"
    receipt = Path(overrides.get("output_dir", u.output_dir)) / O.OUTPUT_NAMES["receipt"]
    assert not receipt.exists()


def _rewrite_fit(u, fid: str, mutate) -> None:
    p = u.result_dir / f"fit_{fid}.json"
    rec = json.loads(p.read_text(encoding="utf-8")); mutate(rec); p.write_bytes(UV.canon(rec))


# ------------------------------------------------------------------ frozen production bindings

def test_frozen_production_bindings_are_exact_full_values():
    assert A.CAMPAIGN_RECEIPT_SHA256 == "a0065925789c58409a85ccbf72d24f5c7b1be142a4d17eddc434babdf0d0e340"
    assert A.CAMPAIGN_CODE_SHA == "a61437ba284e9e75b0557157ad68e56eacd8f8fe"
    assert A.CUSTODY_RECEIPT_SHA256 == "c5116d6273f82fd3b3c5450b6bb8d701e03ef7d17ba6ada98eb5ff5aec906b63"
    assert A.RESULT_LEDGER_SHA256 == "d467bb9b51336278ee46566173148a4f112eaa79cf578b8bbfae502cb4388b89"
    assert A.RESULT_FILE_COUNT == 2113
    assert A.CONTRACT_SHA256 == "57e19295be824dbbb023b60a57c5039dac1f9d74e66fefe1008fc27d30fdaf26"
    assert A.ROOT_MANIFEST_SHA256 == "84949723305dc2211ebcd451b64dd9adc8518f3580d2122f5600fcf4b38de0de"
    assert A.BLINDED_INDEX_SHA256 == "8ea3e0cb6637c97b3e940eac54476622bd4f790febb07abee2e8ccdeea751e40"
    assert A.REALIZATION_AUDIT_RECEIPT_SHA256 == "6bd05349516a969ac7e83fc991d03d6274335b22068f8c6577f5a9de11b3f9b3"
    assert A.REALIZATION_LEDGER_SHA256 == "4e65f213d2eeb2d66b8bd7a9031eeb47eadee5801a9bd0880bd3c78dae88cd65"
    assert A.WORLD_SET_DIRECTORY_DIGEST == "40458efea66e62f3f39cb773641d29c24b80505529baa65bdab31d3975a2a286"
    assert (A.REALIZED_FILE_COUNT, A.CONTROLLER_TRUTH_FILE_COUNT, A.COMMITTED_PACKAGE_FILE_COUNT, A.BLINDED_FIT_FILE_COUNT) == (498, 350, 366, 145)
    assert A.NOT_DIAGNOSED_FIT_IDS == FROZEN_NOT_DIAGNOSED


def test_frozen_realization_bindings_agree_with_committed_audit_receipt_and_ledger():
    """Reads only the committed hash receipt and the path/hash ledger; no controller-truth file is opened."""
    O = _orchestrator()
    rdir = ROOT / O.REALIZATION_REL
    raw = (rdir / "V79_V2_CORE_REALIZATION_AUDIT_FREEZE_RECEIPT_V1.json").read_bytes()
    assert hashlib.sha256(raw).hexdigest() == A.REALIZATION_AUDIT_RECEIPT_SHA256
    rec = json.loads(raw.decode("utf-8"))
    assert rec["complete_ledger_sha256"] == A.REALIZATION_LEDGER_SHA256
    assert rec["world_set_directory_digest"] == A.WORLD_SET_DIRECTORY_DIGEST
    assert (rec["total_file_count"], rec["committed_controller_truth_file_count"], rec["committed_package_file_count"]) == (498, 350, 366)
    ledger_raw = (rdir / rec["complete_ledger"]).read_bytes()
    assert hashlib.sha256(ledger_raw).hexdigest() == A.REALIZATION_LEDGER_SHA256
    rels = [line.split("\t")[0] for line in ledger_raw.decode("utf-8").splitlines()]
    assert sum(r.startswith("blinded_fit_inputs/") for r in rels) == 145
    assert O.CONTRACT_REL == "results/v79/v2_core_qualification/V79_V2_CORE_QUALIFICATION_CONTRACT_V2.json"


# ------------------------------------------------------------------ tightened existing custody checks

def _synthetic_campaign(tmp_path, *, code_sha, custody_sha):
    rows = [{"fit_id": f"{i:064x}", "path": f"fit_{i:064x}.json", "sha256": f"{i + 1:064x}"} for i in range(A.EXPECTED_FITS)]
    rec = {"schema": A.CAMPAIGN_SCHEMA, "code_sha": code_sha, "custody_receipt_sha256": custody_sha, "planned_fit_count": A.EXPECTED_FITS,
           "fit_records": rows, "qualification_fits_run": A.EXPECTED_FITS, "benchmark_run": False, "scoring_run": False,
           "truth_accessed": False, "training_authorized": False}
    p = tmp_path / "campaign.json"; raw = A._canon(rec); p.write_bytes(raw)
    return p, hashlib.sha256(raw).hexdigest()


def test_load_completed_campaign_requires_exact_frozen_code_head_and_custody(tmp_path, monkeypatch):
    p, sha = _synthetic_campaign(tmp_path, code_sha="a" * 40, custody_sha="b" * 64)
    monkeypatch.setattr(A, "CAMPAIGN_RECEIPT_SHA256", sha)
    monkeypatch.setattr(A, "CUSTODY_RECEIPT_SHA256", "b" * 64)
    monkeypatch.setattr(A, "CAMPAIGN_CODE_SHA", "c" * 40)
    with pytest.raises(A.ScoreAuthorityRefused, match="campaign code"):
        A.load_completed_campaign(p, expected_sha256=sha)
    monkeypatch.setattr(A, "CAMPAIGN_CODE_SHA", "a" * 40)
    monkeypatch.setattr(A, "CUSTODY_RECEIPT_SHA256", "d" * 64)
    with pytest.raises(A.ScoreAuthorityRefused, match="custody"):
        A.load_completed_campaign(p, expected_sha256=sha)
    monkeypatch.setattr(A, "CUSTODY_RECEIPT_SHA256", "b" * 64)
    assert A.load_completed_campaign(p, expected_sha256=sha)["code_sha"] == "a" * 40


def test_load_completed_campaign_refuses_any_receipt_but_the_frozen_one(tmp_path, monkeypatch):
    p, sha = _synthetic_campaign(tmp_path, code_sha="a" * 40, custody_sha="b" * 64)
    monkeypatch.setattr(A, "CAMPAIGN_CODE_SHA", "a" * 40); monkeypatch.setattr(A, "CUSTODY_RECEIPT_SHA256", "b" * 64)
    with pytest.raises(A.ScoreAuthorityRefused, match="frozen completed campaign"):
        A.load_completed_campaign(p, expected_sha256=sha)


def test_scoring_authorization_and_adjudication_require_the_frozen_campaign_receipt():
    other = "e" * 64
    auth = {"schema": A.AUTH_SCHEMA, "scoring_authorized": True, "qualification_campaign_controller_pass": True,
            "contract_sha256": A.CONTRACT_SHA256, "root_manifest_sha256": A.ROOT_MANIFEST_SHA256, "blinded_index_sha256": A.BLINDED_INDEX_SHA256,
            "realization_audit_receipt_sha256": A.REALIZATION_AUDIT_RECEIPT_SHA256, "campaign_receipt_sha256": other,
            "scorer_code_sha": "f" * 40, "real_train_posterior_authorized": False, "factorial_science_authorized": False, "training_authorized": False}
    with pytest.raises(A.ScoreAuthorityRefused, match="frozen"):
        A.validate_scoring_authorization(auth, campaign_receipt_sha256=other, scorer_code_sha="f" * 40)
    with pytest.raises(A.ScoreAuthorityRefused, match="frozen"):
        A.build_adjudication_receipt(scorer_code_sha="f" * 40, campaign_receipt_sha256=other, scoring_authorization_sha256="1" * 64,
                                     gate_table={}, descriptive_metrics={})


def test_scoring_run_receipt_v2_binds_every_input_identity_and_refuses_incomplete_outputs():
    outputs = {name: f"{i + 1:064x}" for i, name in enumerate(sorted(R.SCORING_OUTPUT_KEYS))}
    rec = R.scoring_run_receipt(scorer_code_sha="f" * 40, campaign_receipt_sha256=A.CAMPAIGN_RECEIPT_SHA256,
                                scoring_authorization_sha256="1" * 64, outputs=outputs, authentication_steps=["a", "b"])
    assert rec["schema"] == "V79_V2_CORE_QUALIFICATION_SCORING_RUN_RECEIPT_V2"
    for key, value in {"campaign_code_sha": A.CAMPAIGN_CODE_SHA, "custody_receipt_sha256": A.CUSTODY_RECEIPT_SHA256,
                       "result_ledger_sha256": A.RESULT_LEDGER_SHA256, "realization_ledger_sha256": A.REALIZATION_LEDGER_SHA256,
                       "world_set_directory_digest": A.WORLD_SET_DIRECTORY_DIGEST, "contract_sha256": A.CONTRACT_SHA256,
                       "root_manifest_sha256": A.ROOT_MANIFEST_SHA256, "blinded_index_sha256": A.BLINDED_INDEX_SHA256,
                       "realization_audit_receipt_sha256": A.REALIZATION_AUDIT_RECEIPT_SHA256}.items():
        assert rec["inputs"][key] == value
    assert rec["outputs"] == outputs
    assert rec["not_diagnosed_fit_ids"] == sorted(A.NOT_DIAGNOSED_FIT_IDS)
    assert (rec["qualification_scoring_run"], rec["real_train_posterior_authorized"], rec["factorial_science_authorized"], rec["training_authorized"]) == (True, False, False, False)
    partial = dict(outputs); partial.pop(sorted(partial)[0])
    with pytest.raises(R.ScoringRunRefused):
        R.scoring_run_receipt(scorer_code_sha="f" * 40, campaign_receipt_sha256=A.CAMPAIGN_RECEIPT_SHA256,
                              scoring_authorization_sha256="1" * 64, outputs=partial, authentication_steps=["a"])
    with pytest.raises(R.ScoringRunRefused):
        R.scoring_run_receipt(scorer_code_sha="f" * 40, campaign_receipt_sha256="e" * 64,
                              scoring_authorization_sha256="1" * 64, outputs=outputs, authentication_steps=["a"])


# ------------------------------------------------------------------ truth-open-last barrier (unit)

def test_truth_guard_blocks_reads_before_barrier_and_permits_hash_only(tmp_path):
    O = _orchestrator()
    truth = tmp_path / "controller_truth" / "aaaaaaaaaaaa"; truth.mkdir(parents=True)
    f = truth / "x.npy"
    with f.open("wb") as fh: np.save(fh, np.arange(3))
    expected = hashlib.sha256(f.read_bytes()).hexdigest()
    guard = O.TRUTH_GUARD
    guard.arm(protected=[tmp_path / "controller_truth"])
    try:
        with pytest.raises(O.TruthBarrierRefused):
            f.read_bytes()
        with pytest.raises(O.TruthBarrierRefused):
            np.load(f)
        assert O.hash_only_sha256(f) == expected
    finally:
        guard.disarm()
    assert np.load(f).tolist() == [0, 1, 2]


def test_truth_loader_refuses_until_every_authentication_step_is_recorded_in_order(tmp_path):
    O = _orchestrator()
    barrier = O.TruthBarrier()
    with pytest.raises(O.TruthBarrierRefused):
        O.load_truth_after_barrier(barrier, tmp_path, {})
    with pytest.raises(O.TruthBarrierRefused):
        barrier.cross()
    steps = list(O.REQUIRED_AUTHENTICATION_STEPS)
    with pytest.raises(O.TruthBarrierRefused):
        barrier.record(steps[1])
    for step in steps[:-1]:
        barrier.record(step)
    with pytest.raises(O.TruthBarrierRefused):
        barrier.cross()
    barrier.record(steps[-1]); barrier.cross()
    assert barrier.crossed and barrier.steps == steps


def test_internal_truth_read_during_authentication_is_blocked_by_the_executable_barrier(universe, truth_calls, monkeypatch):
    O = _orchestrator()
    import v79_v2_core_qualification_custody as C
    victim = next(p for p in sorted(universe.truth_root.rglob("*.npy")))
    original = C.load_qualification_custody

    def leaky(*args, **kwargs):
        np.load(victim)  # an authentication-phase bug that touches truth
        return original(*args, **kwargs)

    monkeypatch.setattr(C, "load_qualification_custody", leaky)
    with pytest.raises(O.TruthBarrierRefused):
        O.run_qualification_scoring(**universe.run_kwargs())
    assert not (universe.output_dir / O.OUTPUT_NAMES["receipt"]).exists()


# ------------------------------------------------------------------ failures before truth access

def test_campaign_receipt_mismatch_fails_before_truth_access(universe, truth_calls):
    p = universe.result_dir / UV.CAMPAIGN_RECEIPT_NAME
    p.write_bytes(p.read_bytes() + b" ")
    _assert_refused_before_truth(universe, truth_calls, match="campaign_receipt")


@pytest.mark.parametrize("damage", ["ledger_line", "extra_result_file", "draw_file_bytes", "missing_draw_file"])
def test_result_ledger_mismatch_fails_before_truth_access(universe, truth_calls, damage):
    if damage == "ledger_line":
        raw = universe.result_ledger_path.read_bytes(); universe.result_ledger_path.write_bytes(raw.replace(b" *result/", b"  *result/", 1))
    elif damage == "extra_result_file":
        (universe.result_dir / "stray.json").write_bytes(b"{}\n")
    else:
        draw = next(p for p in sorted(universe.result_dir.glob("donor_effect_draws_*.npz")))
        if damage == "draw_file_bytes": draw.write_bytes(draw.read_bytes() + b"\0")
        else: draw.unlink()
    _assert_refused_before_truth(universe, truth_calls, match="result_ledger")


def test_campaign_code_sha_mismatch_fails_before_truth_access(universe, truth_calls, monkeypatch):
    universe.reseal_campaign(code_sha="9" * 40)
    _repatch(universe, monkeypatch, "campaign_receipt_sha256", "result_ledger_sha256", "result_file_count")
    _assert_refused_before_truth(universe, truth_calls, match="campaign code")


def test_custody_prepared_for_another_executor_head_fails_before_truth_access(universe, truth_calls, monkeypatch):
    universe.bindings["custody_executor_code_head"] = "9" * 40
    universe.reseal_custody()
    _repatch(universe, monkeypatch, "custody_receipt_sha256", "campaign_receipt_sha256", "result_ledger_sha256", "result_file_count")
    _assert_refused_before_truth(universe, truth_calls, match="custody")


def test_authorization_bound_to_another_scorer_head_fails_before_truth_access(universe, truth_calls):
    _assert_refused_before_truth(universe, truth_calls, match="authorization", scorer_code_sha="8" * 40)


def test_authorization_bytes_mismatch_fails_before_truth_access(universe, truth_calls):
    _assert_refused_before_truth(universe, truth_calls, match="authorization", authorization_sha256="7" * 64)


def test_cli_binds_the_authorization_to_the_clean_checked_out_head(universe, truth_calls, monkeypatch):
    O = _orchestrator()
    argv = ["--repo-root", str(ROOT), "--campaign-result-dir", str(universe.result_dir), "--result-ledger", str(universe.result_ledger_path),
            "--custody-dir", str(universe.custody_dir), "--realization-dir", str(universe.realization_dir),
            "--authorization", str(universe.scoring_auth_path), "--authorization-sha256", universe.bindings["scoring_authorization_sha256"],
            "--output-dir", str(universe.output_dir)]
    monkeypatch.setattr(O, "_require_clean", lambda root: None)
    monkeypatch.setattr(O, "_git_head", lambda root: "8" * 40)
    with pytest.raises(O.OrchestratorRefused, match="authorization"):
        O.main(argv)

    def dirty(root):
        raise O.OrchestratorRefused("REFUSED V2_CORE scoring orchestrator at scorer_code: repository working tree is not clean")

    monkeypatch.setattr(O, "_require_clean", dirty)
    with pytest.raises(O.OrchestratorRefused, match="not clean"):
        O.main(argv)
    assert truth_calls == []


@pytest.mark.parametrize("damage", ["self_consistent_world_change", "extra_world", "missing_world", "resealed_realization_receipt", "root_manifest_bytes"])
def test_truth_set_must_match_the_frozen_realization_authority(universe, truth_calls, damage):
    oid = universe.world_by_name["Q03_WEAK_SOURCE"]; wdir = universe.truth_root / oid
    if damage == "self_consistent_world_change":
        # The per-world manifest is updated so the world validates against itself; only the realization ledger can refuse it.
        rel = "truth/detection/intercept.npy"
        with (wdir / rel).open("wb") as fh: np.save(fh, np.full(44, 3.0))
        m = json.loads((wdir / "manifest.json").read_text(encoding="utf-8"))
        m["generated_outputs"][rel] = hashlib.sha256((wdir / rel).read_bytes()).hexdigest()
        (wdir / "manifest.json").write_bytes(UV.canon(m))
        assert all(hashlib.sha256((wdir / r).read_bytes()).hexdigest() == h for r, h in m["generated_outputs"].items())
    elif damage == "extra_world":
        import shutil
        shutil.copytree(wdir, universe.truth_root / "ffffffffffff")
    elif damage == "missing_world":
        import shutil
        shutil.rmtree(wdir)
    elif damage == "resealed_realization_receipt":
        rel = universe.realization_dir / UV.REALIZATION_RECEIPT_NAME
        rec = json.loads(rel.read_text(encoding="utf-8")); rec["status"] = "SYNTHETIC_RESEALED"
        rel.write_bytes((json.dumps(rec, indent=2, sort_keys=True) + "\n").encode("utf-8"))
    else:
        p = universe.package_dir / UV.ROOT_MANIFEST_NAME; p.write_bytes(p.read_bytes() + b" ")
    _assert_refused_before_truth(universe, truth_calls, match="realization_authority|truth_tree|blinded_inputs")


@pytest.mark.parametrize("damage", ["missing", "extra", "duplicate", "substituted"])
def test_fit_identity_set_must_equal_the_frozen_1056_fit_queue(universe, truth_calls, monkeypatch, damage):
    rows = [{"fit_id": q["fit_id"], "path": f"fit_{q['fit_id']}.json", "sha256": UV.sha_file(universe.result_dir / f"fit_{q['fit_id']}.json")}
            for q in universe.queue]
    victim = next(r for r in rows if r["fit_id"] not in universe.not_diagnosed_fit_ids)
    if damage == "missing":
        rows.remove(victim)
        (universe.result_dir / victim["path"]).unlink(); (universe.result_dir / f"donor_effect_draws_{victim['fit_id']}.npz").unlink()
    elif damage == "extra":
        fake = "f" * 64; (universe.result_dir / f"fit_{fake}.json").write_bytes((universe.result_dir / victim["path"]).read_bytes())
        rows.append({"fit_id": fake, "path": f"fit_{fake}.json", "sha256": victim["sha256"]})
    elif damage == "duplicate":
        source = next(r for r in rows if r["fit_id"] != victim["fit_id"])
        rows[rows.index(victim)] = dict(source)
        (universe.result_dir / victim["path"]).unlink(); (universe.result_dir / f"donor_effect_draws_{victim['fit_id']}.npz").unlink()
    else:
        fake = "e" * 64
        _rewrite_fit(universe, victim["fit_id"], lambda rec: rec.update({"fit_id": fake}))
        (universe.result_dir / victim["path"]).rename(universe.result_dir / f"fit_{fake}.json")
        rows[rows.index(victim)] = {"fit_id": fake, "path": f"fit_{fake}.json", "sha256": UV.sha_file(universe.result_dir / f"fit_{fake}.json")}
    universe.reseal_campaign(fit_rows=rows)
    _repatch(universe, monkeypatch, "campaign_receipt_sha256", "result_ledger_sha256", "result_file_count")
    _assert_refused_before_truth(universe, truth_calls, match="campaign_receipt|fit_identity_set|fit_records")


@pytest.mark.parametrize("damage", ["reclassified_to_complete", "complete_reclassified_to_not_diagnosed", "refit_bytes", "dropped"])
def test_frozen_not_diagnosed_fits_cannot_be_dropped_refit_or_reclassified(universe, truth_calls, monkeypatch, damage):
    nd = sorted(universe.not_diagnosed_fit_ids)[0]
    complete = next(q["fit_id"] for q in universe.queue if q["fit_id"] not in universe.not_diagnosed_fit_ids)
    if damage == "reclassified_to_complete":
        _rewrite_fit(universe, nd, lambda rec: rec.update({"final_diagnosis": "COMPLETE"}))
    elif damage == "complete_reclassified_to_not_diagnosed":
        _rewrite_fit(universe, complete, lambda rec: rec.update({"final_diagnosis": "NOT_DIAGNOSED"}))
    elif damage == "refit_bytes":
        _rewrite_fit(universe, nd, lambda rec: rec["final_diagnostics"].update({"worst_rhat": 1.05}))
    if damage == "dropped":
        rows = [{"fit_id": q["fit_id"], "path": f"fit_{q['fit_id']}.json", "sha256": UV.sha_file(universe.result_dir / f"fit_{q['fit_id']}.json")}
                for q in universe.queue if q["fit_id"] != nd]
        (universe.result_dir / f"fit_{nd}.json").unlink(); (universe.result_dir / f"donor_effect_draws_{nd}.npz").unlink()
        universe.reseal_campaign(fit_rows=rows)
    else:
        universe.reseal_campaign()
    if damage != "refit_bytes":
        # Everything else re-frozen to the altered campaign: only the frozen NOT_DIAGNOSED authority can refuse it.
        _repatch(universe, monkeypatch, "campaign_receipt_sha256", "result_ledger_sha256", "result_file_count")
        match = "campaign_receipt|not_diagnosed" if damage == "dropped" else "not_diagnosed"
    else:
        # A refit changes bytes. The frozen campaign identity refuses it, whether it is met first through the
        # authorization (which binds the frozen campaign receipt) or through the campaign receipt itself.
        match = "authorization|campaign_receipt"
    _assert_refused_before_truth(universe, truth_calls, match=match)


def test_existing_output_directory_is_a_write_once_failure_before_truth(universe, truth_calls):
    universe.output_dir.mkdir()
    _assert_refused_before_truth(universe, truth_calls, match="output")


def test_output_inside_an_input_authority_is_refused(universe, truth_calls):
    _assert_refused_before_truth(universe, truth_calls, match="output", output_dir=universe.custody_dir / "scoring")


# ------------------------------------------------------------------ after the barrier

def test_truth_manifest_must_cross_link_to_the_blinded_index_after_the_barrier(universe, truth_calls, monkeypatch):
    O = _orchestrator()
    oid = universe.world_by_name["Q02_STRONG_DONOR"]; mp = universe.truth_root / oid / "manifest.json"
    m = json.loads(mp.read_text(encoding="utf-8")); m["blinded_fit_manifest_sha256"] = "0" * 64; mp.write_bytes(UV.canon(m))
    universe.reseal_realization()
    _repatch(universe, monkeypatch, "realization_audit_receipt_sha256", "realization_ledger_sha256", "world_set_directory_digest")
    with pytest.raises(O.OrchestratorRefused, match="truth_cross_identity"):
        O.run_qualification_scoring(**universe.run_kwargs())
    assert truth_calls and all(c[1]["barrier_crossed"] for c in truth_calls)
    assert not (universe.output_dir / O.OUTPUT_NAMES["receipt"]).exists()


def test_partial_scoring_cannot_produce_a_successful_final_receipt(universe, truth_calls, monkeypatch):
    O = _orchestrator()

    def boom(*args, **kwargs):
        raise RuntimeError("injected failure after truth opening")

    monkeypatch.setattr(E, "build_gate_evaluations", boom)
    with pytest.raises((O.OrchestratorRefused, RuntimeError)):
        O.run_qualification_scoring(**universe.run_kwargs())
    assert not (universe.output_dir / O.OUTPUT_NAMES["receipt"]).exists()


def test_input_changed_during_scoring_prevents_the_final_receipt(universe, monkeypatch):
    """Added during GREEN after mutation planning showed post-run input re-verification was otherwise untested."""
    O = _orchestrator()
    original = A.build_adjudication_receipt

    def tamper_then_adjudicate(*args, **kwargs):
        draw = next(p for p in sorted(universe.result_dir.glob("donor_effect_draws_*.npz")))
        draw.write_bytes(draw.read_bytes() + b"\0")
        return original(*args, **kwargs)

    monkeypatch.setattr(A, "build_adjudication_receipt", tamper_then_adjudicate)
    with pytest.raises(O.OrchestratorRefused, match="input_reverification"):
        O.run_qualification_scoring(**universe.run_kwargs())
    assert not (universe.output_dir / O.OUTPUT_NAMES["receipt"]).exists()


def test_complete_scoring_run_is_truth_open_last_write_once_and_preserves_not_diagnosed(universe, truth_calls):
    O = _orchestrator()
    before = _tree_hashes(universe.root, exclude=universe.output_dir)
    receipt = O.run_qualification_scoring(**universe.run_kwargs())
    out = universe.output_dir

    # final receipt: canonical, write-once, bound to every input identity and output
    raw = (out / O.OUTPUT_NAMES["receipt"]).read_bytes()
    assert json.loads(raw.decode("utf-8")) == receipt and A._canon(receipt) == raw
    assert receipt["schema"] == "V79_V2_CORE_QUALIFICATION_SCORING_RUN_RECEIPT_V2"
    assert (receipt["qualification_scoring_run"], receipt["real_train_posterior_authorized"],
            receipt["factorial_science_authorized"], receipt["training_authorized"]) == (True, False, False, False)
    assert not any(k.endswith("_authorized") and v is True for k, v in receipt.items())
    for key, const in BINDING_TO_CONSTANT.items():
        if key != "result_file_count":
            assert receipt["inputs"][key] == getattr(A, const)
    assert receipt["inputs"]["campaign_code_sha"] == A.CAMPAIGN_CODE_SHA
    assert receipt["scorer_code_sha"] == universe.scorer_code_sha
    assert receipt["scoring_authorization_sha256"] == universe.bindings["scoring_authorization_sha256"]
    assert set(receipt["outputs"]) == set(R.SCORING_OUTPUT_KEYS)
    for key, digest in receipt["outputs"].items():
        assert hashlib.sha256((out / O.OUTPUT_NAMES[key]).read_bytes()).hexdigest() == digest

    # truth-open-last: every truth read happened after the barrier, which followed every authentication step
    assert receipt["truth_open_last"]["authentication_steps"] == list(O.REQUIRED_AUTHENTICATION_STEPS)
    assert receipt["truth_open_last"]["barrier_crossed_after_all_steps"] is True
    assert truth_calls and all(c[1]["barrier_crossed"] for c in truth_calls)

    # all 1,056 frozen fits scored in frozen queue order; NOT_DIAGNOSED preserved exactly
    scored = json.loads((out / O.OUTPUT_NAMES["scored_rows"]).read_text(encoding="utf-8"))
    assert [r["fit_id"] for r in scored["rows"]] == [q["fit_id"] for q in universe.queue]
    diag = {r["fit_id"]: r["final_diagnosis"] for r in scored["rows"]}
    assert {f for f, d in diag.items() if d == "NOT_DIAGNOSED"} == universe.not_diagnosed_fit_ids
    assert all(d == "COMPLETE" for f, d in diag.items() if f not in universe.not_diagnosed_fit_ids)
    assert receipt["not_diagnosed_fit_ids"] == sorted(universe.not_diagnosed_fit_ids)

    # frozen convergence treatment: exactly the world/part holding the three fails, and only it
    table = json.loads((out / O.OUTPUT_NAMES["gate_table"]).read_text(encoding="utf-8"))
    assert len(table["rows"]) == A.EXPECTED_GATES
    conv = [r for r in table["rows"] if r["gate"] == "CONVERGENCE_ALL_FITS_DIAGNOSED"]
    assert len(conv) == 24
    failed = [(r["world"], r["part"], r["statistic"]["not_diagnosed_count"]) for r in conv if not r["passed"]]
    assert failed == [(UV.NOT_DIAGNOSED_WORLD, "positive", 3)]
    first = next(i for i, r in enumerate(table["rows"]) if r["verdict_class"] == "FAIL" and r["passed"] is False)
    assert table["terminal"]["terminal"] == "V2_CORE_SYNTHETIC_QUALIFICATION_NOT_QUALIFIED"
    assert table["terminal"]["first_hard_fail_index"] == first
    assert all(r["interpretation"] == ("POST_TERMINAL_DIAGNOSTIC_ONLY" if i > first else "CONFIRMATORY") for i, r in enumerate(table["rows"]))

    adjudication = json.loads((out / O.OUTPUT_NAMES["adjudication"]).read_text(encoding="utf-8"))
    assert adjudication["terminal"] == table["terminal"]["terminal"] and adjudication["first_hard_fail_index"] == first
    assert adjudication["limit_fail_count"] == sum(r["verdict_class"] == "LIMIT" and r["passed"] is False for r in table["rows"])
    descriptive = json.loads((out / O.OUTPUT_NAMES["descriptive_metrics"]).read_text(encoding="utf-8"))
    A.validate_descriptive_metrics(descriptive)
    oracle = json.loads((out / O.OUTPUT_NAMES["heldout_oracle"]).read_text(encoding="utf-8"))
    assert set(oracle["oracle_by_fit_id"]) == {q["fit_id"] for q in universe.queue} and oracle["gating"] is False

    # inputs unchanged; output is write-once
    assert _tree_hashes(universe.root, exclude=universe.output_dir) == before
    with pytest.raises(O.OrchestratorRefused, match="output"):
        O.run_qualification_scoring(**universe.run_kwargs())


def test_fit_side_modules_never_import_the_scoring_orchestrator():
    # Same fit-side set as the CI trust-domain audit; the custody module is checked separately because it
    # legitimately names "controller_truth" in its forbidden-identity list.
    fit_side = ["v79_v2_core_fit_surface.py", "v79_v2_core_fit_model.py", "v79_v2_core_fit_runner.py", "run_v79_v2_core_benchmark.py",
                "run_v79_v2_core_qualification.py", "run_v79_v2_core_qualification_world.py"]
    for name in fit_side:
        text = (ROOT / "scripts" / "v79" / name).read_text(encoding="utf-8")
        assert ORCHESTRATOR not in text and "controller_truth" not in text
    assert ORCHESTRATOR not in (ROOT / "scripts" / "v79" / "v79_v2_core_qualification_custody.py").read_text(encoding="utf-8")
    assert (ROOT / "scripts" / "v79" / f"{ORCHESTRATOR}.py").is_file()
