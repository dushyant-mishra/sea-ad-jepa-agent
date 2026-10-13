#!/usr/bin/env python3
"""Physical controller-scoring orchestrator for the completed V79 V2_CORE qualification campaign.

One shot and write-once. The run:
  1. authenticates every frozen input, in a fixed order, before any controller truth is readable;
  2. crosses an executable truth-open-last barrier. Until it is crossed, a process audit hook refuses
     every open() under the controller-truth tree and the unblinded root manifest, except hash-only
     reads used to authenticate their bytes;
  3. scores all 1,056 frozen fits with the existing scoring primitives, unchanged;
  4. writes the scored rows, gate table, held-out oracle, descriptive metrics and adjudication, each
     with exclusive create, re-verifies every input, and only then writes the final run receipt.
It fits nothing, refits nothing, excludes nothing and carries no downstream authority. Any custody,
hash or poison-read failure stops the run before the final receipt exists.
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Mapping

import run_v79_v2_core_qualification as RQ
import run_v79_v2_core_scoring as R
import v79_v2_core_fit_contract as FC
import v79_v2_core_fit_surface as F
import v79_v2_core_launch as L
import v79_v2_core_qualification_custody as C
import v79_v2_core_qualification_plan as QP
import v79_v2_core_score as S
import v79_v2_core_score_authority as A
import v79_v2_core_score_descriptive as D
import v79_v2_core_score_evaluate as E
import v79_v2_core_score_oracle as O
import v79_v2_core_score_quantities as QN
import v79_v2_core_score_truth as T

REALIZATION_REL = "results/v79/v2_core_realization_audit_freeze_v1"
CONTRACT_REL = "results/v79/v2_core_qualification/V79_V2_CORE_QUALIFICATION_CONTRACT_V2.json"
REALIZATION_RECEIPT_NAME = "V79_V2_CORE_REALIZATION_AUDIT_FREEZE_RECEIPT_V1.json"
REALIZATION_LEDGER_NAME = "REALIZED_WORLDS_V1_COMPLETE_SHA256_LEDGER.tsv"
REALIZATION_TOP_LEVEL = frozenset({F.ROOT_MANIFEST_NAME, "realization_authorization.json", "runtime_environment_receipt.json"})
BLINDED_PREFIX = F.FIT_ROOT_NAME + "/"
TRUTH_PREFIX = "controller_truth/"
Q10_Q11 = frozenset({"Q10_S174_DESIGN_IMBALANCE", "Q11_OMITTED_OPERATOR"})
WORLD_COUNT = 12
OUTPUT_NAMES = {
    "scored_rows": "V79_V2_CORE_SCORED_ROWS_V1.json",
    "gate_table": "V79_V2_CORE_GATE_SCORE_TABLE_V1.json",
    "heldout_oracle": "V79_V2_CORE_HELDOUT_ORACLE_SET_V1.json",
    "descriptive_metrics": "V79_V2_CORE_DESCRIPTIVE_METRICS_V1.json",
    "adjudication": "V79_V2_CORE_QUALIFICATION_ADJUDICATION_V1.json",
    "receipt": "V79_V2_CORE_QUALIFICATION_SCORING_RUN_RECEIPT_V2.json",
}
REQUIRED_AUTHENTICATION_STEPS = (
    "output_guard", "authorization", "contract", "campaign_receipt", "result_ledger", "custody",
    "fit_identity_set", "fit_records", "campaign_reconstruction", "not_diagnosed_set",
    "realization_authority", "blinded_inputs", "truth_tree",
)
_PRIMITIVE_REFUSALS = (
    A.ScoreAuthorityRefused, R.ScoringRunRefused, C.QualificationCustodyRefused, F.FitSurfaceRefused,
    FC.FitContractRefused, QP.QualificationPlanRefused, RQ.QualificationRunRefused, L.LaunchAuthorityRefused,
    S.ScoreRefused, T.TruthRefused, QN.QuantityScoreRefused, E.GateEvaluationRefused, D.DescriptiveRefused,
    O.OracleRefused,
)
_LEDGER_LINE = re.compile(r"^([0-9a-f]{64}) (\d+) \*result/([^/\\\s]+)$")


class OrchestratorRefused(RuntimeError):
    pass


class TruthBarrierRefused(OrchestratorRefused):
    pass


def _refuse(step: str, msg: str):
    raise OrchestratorRefused(f"REFUSED V2_CORE scoring orchestrator at {step}: {msg}")


def _barrier_refuse(msg: str):
    raise TruthBarrierRefused(f"REFUSED V2_CORE scoring orchestrator at truth_barrier: {msg}")


# ---------------------------------------------------------------------------- truth-open-last barrier

def _norm(path) -> str | None:
    if path is None or isinstance(path, int):
        return None
    try:
        raw = os.fsdecode(path) if isinstance(path, bytes) else os.fspath(path)
        return os.path.normcase(os.path.realpath(raw))
    except (TypeError, ValueError, OSError):
        return None


class _TruthGuard:
    """Process-wide poison-read guard. While armed, open() of a protected path raises, except inside
    ``hash_only()``, whose only caller streams the bytes into SHA-256 and returns the digest."""

    def __init__(self):
        self.armed = False
        self.barrier_crossed = False
        self._protected: tuple[str, ...] = ()
        self._hash_only = 0

    def arm(self, *, protected) -> None:
        _install_hook()
        self._protected = tuple(p for p in (_norm(x) for x in protected) if p)
        self.barrier_crossed = False
        self.armed = True

    def disarm(self) -> None:
        self.armed = False
        self._protected = ()

    @contextlib.contextmanager
    def hash_only(self):
        self._hash_only += 1
        try:
            yield
        finally:
            self._hash_only -= 1

    def check(self, path) -> None:
        if not self.armed or self._hash_only:
            return
        p = _norm(path)
        if p is None:
            return
        for root in self._protected:
            if p == root or p.startswith(root + os.sep):
                _barrier_refuse(f"controller truth read attempted before every authentication step passed: {path}")


TRUTH_GUARD = _TruthGuard()
_HOOK_INSTALLED = False


def _audit(event, args):
    if event == "open" and TRUTH_GUARD.armed and args:
        TRUTH_GUARD.check(args[0])


def _install_hook() -> None:
    global _HOOK_INSTALLED
    if not _HOOK_INSTALLED:
        sys.addaudithook(_audit)
        _HOOK_INSTALLED = True


def hash_only_sha256(path) -> str:
    """SHA-256 of a file's bytes; the only sanctioned read of protected files before the barrier."""
    h = hashlib.sha256()
    with TRUTH_GUARD.hash_only():
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b""):
                h.update(chunk)
    return h.hexdigest()


class TruthBarrier:
    """Records the frozen authentication steps in order; truth may be loaded only once crossed."""

    def __init__(self):
        self.steps: list[str] = []
        self.crossed = False

    def record(self, step: str) -> None:
        i = len(self.steps)
        expected = REQUIRED_AUTHENTICATION_STEPS[i] if i < len(REQUIRED_AUTHENTICATION_STEPS) else None
        if self.crossed or step != expected:
            _barrier_refuse(f"authentication step {step!r} out of frozen order (expected {expected!r})")
        self.steps.append(step)

    def cross(self) -> None:
        if self.crossed or tuple(self.steps) != REQUIRED_AUTHENTICATION_STEPS:
            _barrier_refuse("the barrier requires every authentication step, in frozen order, exactly once")
        self.crossed = True


def load_truth_after_barrier(barrier: TruthBarrier, truth_root: Path, contract: Mapping) -> dict:
    if not isinstance(barrier, TruthBarrier) or not barrier.crossed:
        _barrier_refuse("controller truth requested before the barrier was crossed")
    return T.load_truth_set(Path(truth_root), contract)


# ---------------------------------------------------------------------------- helpers

def _canon(obj) -> bytes:
    return (json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def _files(base: Path, step: str) -> dict[str, Path]:
    out = {}
    for p in sorted(Path(base).rglob("*")):
        if p.is_symlink():
            _refuse(step, f"symlink in authenticated tree: {p}")
        if p.is_file():
            out[p.relative_to(base).as_posix()] = p
    return out


def _inside(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def _directory_digest(ledger: Mapping[str, str]) -> str:
    h = hashlib.sha256()
    for rel in sorted(ledger):
        h.update(rel.encode("utf-8")); h.update(b"\0"); h.update(bytes.fromhex(ledger[rel])); h.update(b"\0")
    return h.hexdigest()


def _parse_result_ledger(raw: bytes) -> dict[str, tuple[str, int]]:
    out = {}
    for line in raw.decode("utf-8").splitlines():
        m = _LEDGER_LINE.fullmatch(line)
        if not m:
            _refuse("result_ledger", f"noncanonical ledger line {line[:100]!r}")
        sha, size, name = m.group(1), int(m.group(2)), m.group(3)
        if name in out:
            _refuse("result_ledger", f"duplicate ledger path {name}")
        out[name] = (sha, size)
    return out


def _parse_realization_ledger(raw: bytes) -> dict[str, str]:
    out = {}; previous = None
    for line in raw.decode("utf-8").splitlines():
        rel, sep, sha = line.partition("\t")
        if not sep or not re.fullmatch(r"[0-9a-f]{64}", sha) or not rel or rel.startswith("/") or ".." in rel.split("/"):
            _refuse("realization_authority", f"noncanonical realization ledger line {line[:100]!r}")
        if previous is not None and rel <= previous:
            _refuse("realization_authority", "realization ledger is not strictly sorted and unique")
        out[rel] = sha; previous = rel
    return out


def _write_exclusive(path: Path, obj) -> str:
    raw = _canon(obj)
    with open(path, "xb") as fh:
        fh.write(raw); fh.flush(); os.fsync(fh.fileno())
    return hashlib.sha256(raw).hexdigest()


# ---------------------------------------------------------------------------- authentication phase

def _authenticate(ctx: dict, barrier: TruthBarrier, step: list) -> dict:
    repo_root = ctx["repo_root"]; out_dir = ctx["output_dir"]

    step[0] = "output_guard"
    if os.path.lexists(out_dir):
        _refuse("output_guard", f"output directory already exists (write-once): {out_dir}")
    for name in ("repo_root", "campaign_result_dir", "custody_dir", "realization_dir"):
        if _inside(out_dir, ctx[name]):
            _refuse("output_guard", f"output directory lies inside an input authority ({name})")
    out_dir.parent.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(exist_ok=False)
    barrier.record("output_guard")

    step[0] = "authorization"
    auth = R.load_scoring_authorization(ctx["authorization_path"], expected_sha256=ctx["authorization_sha256"],
                                        campaign_receipt_sha256=A.CAMPAIGN_RECEIPT_SHA256, scorer_code_sha=ctx["scorer_code_sha"])
    barrier.record("authorization")

    step[0] = "contract"
    if A.CONTRACT_SHA256 != L.FINAL_CONTRACT_SHA256 or A.CONTRACT_SHA256 != FC.SOURCE_CONTRACT_SHA256:
        _refuse("contract", "frozen contract identities disagree across modules")
    contract = L.require_launch_authority(repo_root / CONTRACT_REL, root=repo_root)
    S.gate_authority(contract)
    barrier.record("contract")

    step[0] = "campaign_receipt"
    campaign_path = ctx["campaign_result_dir"] / RQ.CAMPAIGN_RECEIPT_NAME
    campaign = A.load_completed_campaign(campaign_path, expected_sha256=A.CAMPAIGN_RECEIPT_SHA256)
    barrier.record("campaign_receipt")

    step[0] = "result_ledger"
    ledger_raw = Path(ctx["result_ledger_path"]).read_bytes()
    if hashlib.sha256(ledger_raw).hexdigest() != A.RESULT_LEDGER_SHA256:
        _refuse("result_ledger", "result-file ledger SHA-256 differs from the frozen ledger")
    ledger = _parse_result_ledger(ledger_raw)
    if len(ledger) != A.RESULT_FILE_COUNT:
        _refuse("result_ledger", f"result ledger lists {len(ledger)} files, frozen count is {A.RESULT_FILE_COUNT}")
    physical = {}
    for p in sorted(ctx["campaign_result_dir"].iterdir()):
        if p.is_symlink() or not p.is_file():
            _refuse("result_ledger", f"non-file entry in campaign result directory: {p.name}")
        physical[p.name] = p
    if set(physical) != set(ledger):
        _refuse("result_ledger", f"physical result set differs; extra={sorted(set(physical) - set(ledger))[:5]}, missing={sorted(set(ledger) - set(physical))[:5]}")
    result_hashes = {}
    for name, p in physical.items():
        sha, size = ledger[name]
        actual = hash_only_sha256(p)
        if actual != sha or p.stat().st_size != size:
            _refuse("result_ledger", f"result file bytes differ from the frozen ledger: {name}")
        result_hashes[name] = actual
    if result_hashes.get(RQ.CAMPAIGN_RECEIPT_NAME) != A.CAMPAIGN_RECEIPT_SHA256:
        _refuse("result_ledger", "ledger does not bind the frozen campaign receipt")
    for row in campaign["fit_records"]:
        if result_hashes.get(row["path"]) != row["sha256"]:
            _refuse("result_ledger", f"campaign fit-record hash is not the ledger hash: {row['path']}")
    barrier.record("result_ledger")

    step[0] = "custody"
    if (F.QUALIFICATION_ROOT_MANIFEST_SHA256, F.QUALIFICATION_INDEX_SHA256, C.QUALIFICATION_INDEX_SHA256) != \
            (A.ROOT_MANIFEST_SHA256, A.BLINDED_INDEX_SHA256, A.BLINDED_INDEX_SHA256):
        _refuse("custody", "frozen root/index identities disagree across modules")
    custody = C.load_qualification_custody(ctx["custody_dir"], expected_receipt_sha256=A.CUSTODY_RECEIPT_SHA256)
    if custody.receipt.get("executor_code_head") != A.CAMPAIGN_CODE_SHA:
        _refuse("custody", f"custody was prepared for executor head {custody.receipt.get('executor_code_head')!r}, not the frozen campaign code head")
    if campaign.get("custody_receipt_sha256") != custody.receipt_sha256:
        _refuse("custody", "campaign receipt does not bind this custody receipt")
    barrier.record("custody")

    step[0] = "fit_identity_set"
    queue = list(custody.queue)
    expected_ids = [q["fit_id"] for q in queue]
    campaign_ids = [r["fit_id"] for r in campaign["fit_records"]]
    if len(expected_ids) != A.EXPECTED_FITS or len(set(expected_ids)) != A.EXPECTED_FITS:
        _refuse("fit_identity_set", "frozen qualification queue is not 1,056 unique fits")
    if campaign_ids != expected_ids:
        _refuse("fit_identity_set", f"campaign fit identities differ from the frozen queue; missing={sorted(set(expected_ids) - set(campaign_ids))[:3]}, "
                                    f"extra={sorted(set(campaign_ids) - set(expected_ids))[:3]}, order_or_duplicates={len(campaign_ids) != len(set(campaign_ids))}")
    barrier.record("fit_identity_set")

    step[0] = "fit_records"
    fits = R.load_fit_receipts(campaign, ctx["campaign_result_dir"])
    validated = RQ.completed_prefix(ctx["campaign_result_dir"], queue, expected_code_sha=A.CAMPAIGN_CODE_SHA, seed_by_fit_id=custody.seed_by_fit_id)
    if validated != A.EXPECTED_FITS:
        _refuse("fit_records", f"only {validated} of {A.EXPECTED_FITS} fit records validate as a complete prefix")
    S.require_complete_campaign(contract, fits)
    fits_by_id = {f["fit_id"]: f for f in fits}
    for q in queue:
        f = fits_by_id[q["fit_id"]]
        if (f["opaque_world_id"], int(f["gene_index"]), f["part"]) != (q["opaque_world_id"], int(q["gene_index"]), q["part"]):
            _refuse("fit_records", f"fit record scientific identity differs from the queue: {q['fit_id']}")
    barrier.record("fit_records")

    step[0] = "campaign_reconstruction"
    rebuilt = RQ.campaign_receipt_skeleton(code_sha=A.CAMPAIGN_CODE_SHA, custody_receipt_sha=custody.receipt_sha256, fit_count=len(queue))
    rebuilt["fit_records"] = [{"fit_id": q["fit_id"], "path": f"fit_{q['fit_id']}.json", "sha256": result_hashes[f"fit_{q['fit_id']}.json"]} for q in queue]
    rebuilt["qualification_fits_run"] = len(queue)
    if _canon(rebuilt) != campaign_path.read_bytes():
        _refuse("campaign_reconstruction", "campaign receipt is not the deterministic reconstruction of the validated fit records")
    barrier.record("campaign_reconstruction")

    step[0] = "not_diagnosed_set"
    diagnoses = {fid: f.get("final_diagnosis") for fid, f in fits_by_id.items()}
    not_diagnosed = {fid for fid, d in diagnoses.items() if d == "NOT_DIAGNOSED"}
    other = {d for fid, d in diagnoses.items() if fid not in not_diagnosed}
    if not_diagnosed != set(A.NOT_DIAGNOSED_FIT_IDS) or other != {"COMPLETE"}:
        _refuse("not_diagnosed_set", f"NOT_DIAGNOSED fits differ from the frozen set; missing={sorted(set(A.NOT_DIAGNOSED_FIT_IDS) - not_diagnosed)}, "
                                     f"extra={sorted(not_diagnosed - set(A.NOT_DIAGNOSED_FIT_IDS))}, other_diagnoses={sorted(map(str, other))}")
    barrier.record("not_diagnosed_set")

    step[0] = "realization_authority"
    rdir = ctx["realization_dir"]; package = rdir / "package"
    rraw = (rdir / REALIZATION_RECEIPT_NAME).read_bytes()
    if hashlib.sha256(rraw).hexdigest() != A.REALIZATION_AUDIT_RECEIPT_SHA256:
        _refuse("realization_authority", "realization audit receipt SHA-256 differs from the frozen receipt")
    rrec = json.loads(rraw.decode("utf-8"))
    expected_fields = {
        "schema": "V79_V2_CORE_REALIZATION_AUDIT_FREEZE_RECEIPT_V1", "complete_ledger": REALIZATION_LEDGER_NAME,
        "complete_ledger_sha256": A.REALIZATION_LEDGER_SHA256, "root_manifest_sha256": A.ROOT_MANIFEST_SHA256,
        "blinded_fit_index_sha256": A.BLINDED_INDEX_SHA256, "world_count": WORLD_COUNT, "mode": T.MODE,
        "world_set_directory_digest": A.WORLD_SET_DIRECTORY_DIGEST, "total_file_count": A.REALIZED_FILE_COUNT,
        "committed_controller_truth_file_count": A.CONTROLLER_TRUTH_FILE_COUNT, "committed_controller_truth_manifest_count": WORLD_COUNT,
        "committed_package_file_count": A.COMMITTED_PACKAGE_FILE_COUNT, "committed_package_root": "package/",
        "benchmark_run": False, "qualification_fits_run": 0, "scoring_run": False, "training_authorized": False,
    }
    for key, want in expected_fields.items():
        if rrec.get(key) != want:
            _refuse("realization_authority", f"realization receipt field {key} differs from the frozen authority")
    lraw = (rdir / REALIZATION_LEDGER_NAME).read_bytes()
    if hashlib.sha256(lraw).hexdigest() != A.REALIZATION_LEDGER_SHA256:
        _refuse("realization_authority", "realization ledger SHA-256 differs from the frozen ledger")
    rledger = _parse_realization_ledger(lraw)
    if len(rledger) != A.REALIZED_FILE_COUNT or _directory_digest(rledger) != A.WORLD_SET_DIRECTORY_DIGEST:
        _refuse("realization_authority", "realization ledger does not reproduce the frozen world-set directory digest")
    top = {r for r in rledger if "/" not in r}
    blinded = {r for r in rledger if r.startswith(BLINDED_PREFIX)}
    truth = {r for r in rledger if r.startswith(TRUTH_PREFIX)}
    if top != REALIZATION_TOP_LEVEL or len(blinded) != A.BLINDED_FIT_FILE_COUNT or len(truth) != A.CONTROLLER_TRUTH_FILE_COUNT or \
            len(top) + len(blinded) + len(truth) != len(rledger):
        _refuse("realization_authority", "realization ledger partition differs from the frozen authority")
    if rledger[F.ROOT_MANIFEST_NAME] != A.ROOT_MANIFEST_SHA256 or rledger[BLINDED_PREFIX + F.FIT_INDEX_NAME] != A.BLINDED_INDEX_SHA256:
        _refuse("realization_authority", "realization ledger does not bind the frozen root manifest and blinded index")
    package_files = _files(package, "realization_authority")
    committed_non_truth = top | {BLINDED_PREFIX + F.FIT_INDEX_NAME} | {r for r in blinded if r.count("/") == 2 and r.endswith("/manifest.json")}
    package_non_truth = {r for r in package_files if not r.startswith(TRUTH_PREFIX)}
    if package_non_truth != committed_non_truth or len(package_files) != A.COMMITTED_PACKAGE_FILE_COUNT:
        _refuse("realization_authority", "committed package file set differs from the frozen realization authority")
    for rel in sorted(committed_non_truth):
        if hash_only_sha256(package_files[rel]) != rledger[rel]:
            _refuse("realization_authority", f"committed package bytes differ from the realization ledger: {rel}")
    barrier.record("realization_authority")

    step[0] = "blinded_inputs"
    custody_blinded = {BLINDED_PREFIX + rel: p for rel, p in _files(ctx["custody_dir"] / F.FIT_ROOT_NAME, "blinded_inputs").items()}
    if set(custody_blinded) != blinded:
        _refuse("blinded_inputs", "fit-custody blinded inputs differ from the realization ledger file set")
    for rel, p in sorted(custody_blinded.items()):
        if hash_only_sha256(p) != rledger[rel]:
            _refuse("blinded_inputs", f"fit-custody blinded bytes differ from the realization ledger: {rel}")
    index = custody.blinded_index.index
    index_ids = {w["opaque_world_id"] for w in index["worlds"]}
    if len(index_ids) != WORLD_COUNT or {q["opaque_world_id"] for q in queue} != index_ids or {f["opaque_world_id"] for f in fits} != index_ids:
        _refuse("blinded_inputs", "opaque world identities differ across blinded index, queue and fit records")
    blinded_worlds = {oid: F.load_blinded_world(custody.blinded_index, oid) for oid in sorted(index_ids)}
    barrier.record("blinded_inputs")

    step[0] = "truth_tree"
    truth_files = {TRUTH_PREFIX + rel: p for rel, p in _files(ctx["truth_root"], "truth_tree").items()}
    if set(truth_files) != truth:
        _refuse("truth_tree", f"controller-truth file set differs from the realization ledger; extra={sorted(set(truth_files) - truth)[:3]}, missing={sorted(truth - set(truth_files))[:3]}")
    for rel, p in sorted(truth_files.items()):
        if hash_only_sha256(p) != rledger[rel]:
            _refuse("truth_tree", f"controller-truth bytes differ from the realization ledger: {rel}")
    truth_worlds = {r.split("/")[1] for r in truth}
    if truth_worlds != index_ids or any(f"{TRUTH_PREFIX}{oid}/manifest.json" not in truth for oid in index_ids):
        _refuse("truth_tree", "controller-truth world identities differ from the blinded index")
    barrier.record("truth_tree")

    return {"auth": auth, "contract": contract, "campaign": campaign, "custody": custody, "queue": queue, "fits_by_id": fits_by_id,
            "index": index, "blinded_worlds": blinded_worlds, "rledger": rledger, "result_hashes": result_hashes}


# ---------------------------------------------------------------------------- scoring phase

def _score(ctx: dict, barrier: TruthBarrier, auth_state: dict, step: list) -> dict:
    contract = auth_state["contract"]; queue = auth_state["queue"]; fits_by_id = auth_state["fits_by_id"]; index = auth_state["index"]

    step[0] = "truth_open"
    worlds = load_truth_after_barrier(barrier, ctx["truth_root"], contract)
    by_oid = {w.opaque_world_id: w for w in worlds.values()}

    step[0] = "truth_cross_identity"
    index_records = {w["opaque_world_id"]: w for w in index["worlds"]}
    if set(by_oid) != set(index_records):
        _refuse("truth_cross_identity", "loaded truth worlds differ from the blinded index")
    for oid, tw in sorted(by_oid.items()):
        m = tw.manifest
        if m.get("blinded_fit_manifest_sha256") != index_records[oid]["manifest_sha256"] or \
                m.get("pairing_amendment_sha256") != index.get("pairing_amendment_sha256") or \
                m.get("generator_bundle_sha256") != index.get("generator_bundle_sha256"):
            _refuse("truth_cross_identity", f"truth manifest for {oid} does not cross-link to its blinded fit manifest/index")

    step[0] = "scoring"
    rows = []
    for q in queue:
        fit = fits_by_id[q["fit_id"]]
        rows.append({"fit_id": q["fit_id"], **QN.score_gene_quantities(by_oid[q["opaque_world_id"]], fit)})
    scored_not_diagnosed = {r["fit_id"] for r in rows if r["final_diagnosis"] == "NOT_DIAGNOSED"}
    if scored_not_diagnosed != set(A.NOT_DIAGNOSED_FIT_IDS) or len(rows) != A.EXPECTED_FITS:
        _refuse("scoring", "scored rows do not preserve the frozen 1,056 fits and NOT_DIAGNOSED set")

    step[0] = "gates"
    evaluations = E.build_gate_evaluations(contract, rows)
    table = S.bind_gate_evaluations(contract, evaluations)
    nd_groups = {(r["world_name"], r["part"]) for r in rows if r["final_diagnosis"] == "NOT_DIAGNOSED"}
    conv = [r for r in table["rows"] if r["gate"] == "CONVERGENCE_ALL_FITS_DIAGNOSED"]
    if {(r["world"], r["part"]) for r in conv if not r["passed"]} != nd_groups or \
            sum(int(r["statistic"]["not_diagnosed_count"]) for r in conv) != len(A.NOT_DIAGNOSED_FIT_IDS):
        _refuse("gates", "convergence gates do not account for exactly the frozen NOT_DIAGNOSED fits")

    step[0] = "heldout_oracle"
    oracle = {}
    for q in queue:
        oracle[q["fit_id"]] = O.heldout_oracle(by_oid[q["opaque_world_id"]], auth_state["blinded_worlds"][q["opaque_world_id"]],
                                               gene_index=int(q["gene_index"]), part=q["part"])

    step[0] = "descriptive_metrics"
    fits = [fits_by_id[q["fit_id"]] for q in queue]
    heldout_metric = {(r["world_name"], r["part"], int(r["gene_index"])): R.q10_q11_heldout_model_metric(fits_by_id[r["fit_id"]])
                      for r in rows if r["world_name"] in Q10_Q11}
    descriptive = A.validate_descriptive_metrics(D.build_descriptive_metrics(rows, fits, oracle, heldout_model_metric=heldout_metric))

    step[0] = "adjudication"
    adjudication = A.build_adjudication_receipt(scorer_code_sha=ctx["scorer_code_sha"], campaign_receipt_sha256=A.CAMPAIGN_RECEIPT_SHA256,
                                                scoring_authorization_sha256=ctx["authorization_sha256"], gate_table=table,
                                                descriptive_metrics=descriptive)
    return {
        "scored_rows": {"schema": "V79_V2_CORE_SCORED_ROWS_V1", "campaign_receipt_sha256": A.CAMPAIGN_RECEIPT_SHA256,
                        "scorer_code_sha": ctx["scorer_code_sha"], "fit_count": len(rows), "rows": rows},
        "gate_table": table,
        "heldout_oracle": {"schema": "V79_V2_CORE_HELDOUT_ORACLE_SET_V1", "gating": False, "oracle_by_fit_id": oracle},
        "descriptive_metrics": descriptive,
        "adjudication": adjudication,
    }


def _reverify_inputs(ctx: dict, auth_state: dict) -> None:
    """Every authenticated input must be byte-identical after scoring."""
    if hashlib.sha256(Path(ctx["authorization_path"]).read_bytes()).hexdigest() != ctx["authorization_sha256"]:
        _refuse("input_reverification", "scoring authorization bytes changed during the run")
    if hashlib.sha256(Path(ctx["result_ledger_path"]).read_bytes()).hexdigest() != A.RESULT_LEDGER_SHA256:
        _refuse("input_reverification", "result ledger changed during the run")
    now = {p.name: hash_only_sha256(p) for p in sorted(ctx["campaign_result_dir"].iterdir())}
    if now != auth_state["result_hashes"]:
        _refuse("input_reverification", "campaign result files changed during the run")
    rledger = auth_state["rledger"]; rdir = ctx["realization_dir"]
    for name, want in ((REALIZATION_RECEIPT_NAME, A.REALIZATION_AUDIT_RECEIPT_SHA256), (REALIZATION_LEDGER_NAME, A.REALIZATION_LEDGER_SHA256)):
        if hashlib.sha256((rdir / name).read_bytes()).hexdigest() != want:
            _refuse("input_reverification", f"{name} changed during the run")
    package = {r: p for r, p in _files(rdir / "package", "input_reverification").items()}
    custody_blinded = {BLINDED_PREFIX + rel: p for rel, p in _files(ctx["custody_dir"] / F.FIT_ROOT_NAME, "input_reverification").items()}
    for rel, p in list(package.items()) + list(custody_blinded.items()):
        if rledger.get(rel) != hash_only_sha256(p):
            _refuse("input_reverification", f"authenticated bytes changed during the run: {rel}")
    if hashlib.sha256((ctx["custody_dir"] / C.RECEIPT_NAME).read_bytes()).hexdigest() != A.CUSTODY_RECEIPT_SHA256:
        _refuse("input_reverification", "custody receipt changed during the run")


# ---------------------------------------------------------------------------- entrypoints

def run_qualification_scoring(*, repo_root, scorer_code_sha: str, authorization_path, authorization_sha256: str,
                              campaign_result_dir, result_ledger_path, custody_dir, realization_dir, output_dir) -> dict:
    """Run the one authorized qualification scoring pass and return the final run receipt."""
    ctx = {"repo_root": Path(repo_root), "scorer_code_sha": scorer_code_sha, "authorization_path": Path(authorization_path),
           "authorization_sha256": authorization_sha256, "campaign_result_dir": Path(campaign_result_dir),
           "result_ledger_path": Path(result_ledger_path), "custody_dir": Path(custody_dir),
           "realization_dir": Path(realization_dir), "output_dir": Path(output_dir)}
    ctx["truth_root"] = ctx["realization_dir"] / "package" / "controller_truth"
    barrier = TruthBarrier(); step = ["output_guard"]
    TRUTH_GUARD.arm(protected=[ctx["truth_root"], ctx["realization_dir"] / "package" / F.ROOT_MANIFEST_NAME])
    try:
        auth_state = _authenticate(ctx, barrier, step)
        barrier.cross()
        TRUTH_GUARD.barrier_crossed = True
        TRUTH_GUARD.disarm()
        products = _score(ctx, barrier, auth_state, step)
        step[0] = "write_outputs"
        hashes = {key: _write_exclusive(ctx["output_dir"] / OUTPUT_NAMES[key], products[key]) for key in R.SCORING_OUTPUT_KEYS}
        step[0] = "input_reverification"
        _reverify_inputs(ctx, auth_state)
        step[0] = "receipt"
        receipt = R.scoring_run_receipt(scorer_code_sha=scorer_code_sha, campaign_receipt_sha256=A.CAMPAIGN_RECEIPT_SHA256,
                                        scoring_authorization_sha256=authorization_sha256, outputs=hashes,
                                        authentication_steps=list(barrier.steps))
        _write_exclusive(ctx["output_dir"] / OUTPUT_NAMES["receipt"], receipt)
        return receipt
    except OrchestratorRefused:
        raise
    except _PRIMITIVE_REFUSALS as exc:
        raise OrchestratorRefused(f"REFUSED V2_CORE scoring orchestrator at {step[0]}: {exc}") from exc
    finally:
        TRUTH_GUARD.disarm()
        TRUTH_GUARD.barrier_crossed = False


def _git_head(root: Path) -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()


def _require_clean(root: Path) -> None:
    if subprocess.check_output(["git", "status", "--porcelain", "--untracked-files=all"], cwd=root, text=True).strip():
        _refuse("scorer_code", "repository working tree is not clean")


def _require_executing_code_in(root: Path) -> None:
    """The authorization binds the checkout's HEAD, so the code actually executing must be that checkout's."""
    base = (Path(root) / "scripts" / "v79").resolve()
    for mod in (sys.modules[__name__], RQ, R, FC, F, L, C, QP, S, A, D, E, O, QN, T):
        loaded = Path(mod.__file__).resolve()
        try:
            loaded.relative_to(base)
        except ValueError:
            _refuse("scorer_code", f"executing module {mod.__name__} is not loaded from the authorized checkout: {loaded}")


def main(argv=None) -> dict:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--repo-root", required=True, help="clean checkout of the authorized scorer head")
    p.add_argument("--campaign-result-dir", required=True)
    p.add_argument("--result-ledger", required=True)
    p.add_argument("--custody-dir", required=True)
    p.add_argument("--realization-dir", default=None, help=f"defaults to <repo-root>/{REALIZATION_REL}")
    p.add_argument("--authorization", required=True)
    p.add_argument("--authorization-sha256", required=True)
    p.add_argument("--output-dir", required=True)
    a = p.parse_args(argv)
    root = Path(a.repo_root).resolve()
    _require_clean(root)
    _require_executing_code_in(root)
    head = _git_head(root)
    receipt = run_qualification_scoring(
        repo_root=root, scorer_code_sha=head, authorization_path=Path(a.authorization), authorization_sha256=a.authorization_sha256,
        campaign_result_dir=Path(a.campaign_result_dir), result_ledger_path=Path(a.result_ledger), custody_dir=Path(a.custody_dir),
        realization_dir=Path(a.realization_dir) if a.realization_dir else root / REALIZATION_REL, output_dir=Path(a.output_dir))
    receipt_path = Path(a.output_dir) / OUTPUT_NAMES["receipt"]
    print(json.dumps({"receipt": str(receipt_path), "receipt_sha256": hashlib.sha256(receipt_path.read_bytes()).hexdigest(),
                      "outputs": receipt["outputs"]}, indent=2, sort_keys=True))
    return receipt


if __name__ == "__main__":
    main()
