"""Synthetic, custody-consistent V79 V2_CORE qualification universe for scoring-orchestrator tests.

Every artifact the scoring orchestrator authenticates is generated here in its production schema:
the realization audit receipt, complete ledger and committed package (blinded index and manifests,
controller truth); the fit custody directory (blinded inputs, fit-contract view, sanitized execution
authorization, custody receipt); the completed campaign (1,056 fit records, donor-draw files, campaign
receipt); the result-file ledger; and a controller scoring authorization. The frozen Contract V2 is the
only production input. No real controller truth and no real fit output is read.

Frozen module constants are re-pointed at this universe with ``Universe.patch(monkeypatch)``. The
``reseal_*`` methods recompute downstream receipts after a deliberate change, so a test can make an
artifact self-consistent but wrong and check that a higher authority still refuses it.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "scripts" / "v79"
sys.path.insert(0, str(HERE))
import prepare_v79_v2_core_qualification_campaign as PREP  # noqa: E402
import run_v79_v2_core_qualification as RQ  # noqa: E402
import v79_v2_core_fit_contract as FC  # noqa: E402
import v79_v2_core_fit_surface as F  # noqa: E402
import v79_v2_core_qualification_custody as C  # noqa: E402
import v79_v2_core_qualification_plan as QP  # noqa: E402
import v79_v2_core_score_authority as A  # noqa: E402
import v79_v2_core_score_truth as T  # noqa: E402

CONTRACT_PATH = ROOT / "results/v79/v2_core_qualification/V79_V2_CORE_QUALIFICATION_CONTRACT_V2.json"
SOURCE = FC.SOURCE_CONTRACT_SHA256
PAIRING = hashlib.sha256(b"synthetic-pairing-amendment").hexdigest()
GENERATOR = hashlib.sha256(b"synthetic-generator-bundle").hexdigest()
N_GENE = 44
N_DONOR = 6
REPLICATES = ("train", "same_donor", "new_donor")
LEDGER_NAME = "REALIZED_WORLDS_V1_COMPLETE_SHA256_LEDGER.tsv"
REALIZATION_RECEIPT_NAME = "V79_V2_CORE_REALIZATION_AUDIT_FREEZE_RECEIPT_V1.json"
ROOT_MANIFEST_NAME = F.ROOT_MANIFEST_NAME
INDEX_NAME = F.FIT_INDEX_NAME
CAMPAIGN_RECEIPT_NAME = RQ.CAMPAIGN_RECEIPT_NAME
TOP_LEVEL = (ROOT_MANIFEST_NAME, "runtime_environment_receipt.json", "realization_authorization.json")
NOT_DIAGNOSED_WORLD = "Q05_CLASS_ABSENT"
NOT_DIAGNOSED_SPECS = ((2, "positive"), (13, "positive"), (43, "positive"))
CAMPAIGN_CODE_SHA = "1" * 40
SCORER_CODE_SHA = "2" * 40


def canon(obj) -> bytes:
    return (json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def sha_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def sha_file(path: Path) -> str:
    return sha_bytes(Path(path).read_bytes())


def _save_npy(path: Path, arr) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as fh:
        np.save(fh, np.asarray(arr), allow_pickle=False)
    return sha_file(path)


def _write(path: Path, raw: bytes) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    return sha_bytes(raw)


def _files(base: Path) -> dict[str, Path]:
    return {p.relative_to(base).as_posix(): p for p in sorted(base.rglob("*")) if p.is_file()}


def directory_digest(ledger: dict[str, str]) -> str:
    h = hashlib.sha256()
    for rel in sorted(ledger):
        h.update(rel.encode("utf-8")); h.update(b"\0"); h.update(bytes.fromhex(ledger[rel])); h.update(b"\0")
    return h.hexdigest()


def _design() -> dict[str, np.ndarray]:
    src, donor, cls = [], [], []
    for s in range(3):
        for d in range(2):
            for c in range(3):
                for _ in range(2):
                    src.append(s); donor.append(2 * s + d); cls.append(c)
    n = len(src)
    log_lib = np.linspace(-1.5, 1.5, n) + 0.1 * np.sin(np.arange(n))
    return {"src": np.asarray(src, dtype=np.int64), "donor": np.asarray(donor, dtype=np.int64),
            "cls": np.asarray(cls, dtype=np.int64), "log_lib": np.asarray(log_lib, dtype=float)}


def _summary_quantity(truth, labels, rng) -> dict:
    t = np.asarray(truth, dtype=float).reshape(-1)
    mean = t + 0.05 * rng.standard_normal(t.size)
    sd = np.full(t.size, 0.2)
    z = {"q005": -2.576, "q025": -1.96, "q05": -1.645, "q50": 0.0, "q95": 1.645, "q975": 1.96, "q995": 2.576}
    out = {"labels": list(labels), "mean": mean.tolist(), "sd": sd.tolist()}
    for k, v in z.items():
        out[k] = (mean + v * sd).tolist()
    return out


def _calibration(n: int, predicted: float, observed: float) -> list[dict]:
    rows = [{"bin_index": b, "lower": b / 10, "upper": (b + 1) / 10, "n": 0, "mean_predicted": None, "observed_rate": None}
            for b in range(10)]
    rows[5] = {"bin_index": 5, "lower": 0.5, "upper": 0.6, "n": n, "mean_predicted": predicted, "observed_rate": observed}
    return rows


class Universe:
    """A complete synthetic qualification universe rooted at ``root``."""

    def __init__(self, root: Path):
        self.root = Path(root)
        self.realization_dir = self.root / "realization"
        self.package_dir = self.realization_dir / "package"
        self.truth_root = self.package_dir / "controller_truth"
        self.custody_dir = self.root / "fit_custody"
        self.fit_root = self.custody_dir / F.FIT_ROOT_NAME
        self.result_dir = self.root / "campaign" / "result"
        self.result_ledger_path = self.root / "campaign" / "RESULT_FILE_LEDGER_SHA256.txt"
        self.scoring_auth_path = self.root / "V79_V2_CORE_QUALIFICATION_SCORING_AUTHORIZATION_SYNTHETIC.json"
        self.output_dir = self.root / "scoring_output"
        self.scorer_code_sha = SCORER_CODE_SHA
        self.bindings: dict = {}
        self.world_by_name: dict[str, str] = {}

    # ---------------------------------------------------------------- construction
    @classmethod
    def build(cls, root: Path) -> "Universe":
        u = cls(root)
        contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
        names = [str(w["name"]) for w in contract["worlds"]["world_list"]]
        design = _design(); n_cells = len(design["src"])
        support = np.ones((n_cells, N_GENE), dtype=bool)
        truths = {}
        for i, name in enumerate(names):
            oid = sha_bytes(f"synthetic-v79-world-{i}".encode())[:12]
            u.world_by_name[name] = oid
            rng = np.random.default_rng(1000 + i)
            # blinded fit-side world
            wdir = u.fit_root / oid; outputs = {}
            for key in F.DESIGN_KEYS:
                outputs[f"design/{key}.npy"] = _save_npy(wdir / f"design/{key}.npy", design[key])
            outputs["support.npy"] = _save_npy(wdir / "support.npy", support)
            for rep in REPLICATES:
                detected = rng.integers(0, 2, size=(n_cells, N_GENE)).astype(np.int8); detected[0, :] = 1; detected[1, :] = 0
                observed = np.where(detected == 1, rng.lognormal(0.0, 0.5, size=(n_cells, N_GENE)), 0.0)
                outputs[f"observations/{rep}/observed.npy"] = _save_npy(wdir / f"observations/{rep}/observed.npy", observed)
                outputs[f"observations/{rep}/detected.npy"] = _save_npy(wdir / f"observations/{rep}/detected.npy", detected)
            manifest = {"schema": "V79_V2_CORE_BLINDED_WORLD_DATA_MANIFEST_V1", "opaque_world_id": oid,
                        "final_contract_sha256": SOURCE, "pairing_amendment_sha256": PAIRING,
                        "generator_bundle_sha256": GENERATOR, "generated_outputs": dict(sorted(outputs.items())),
                        "benchmark_run": False, "qualification_fits_run": 0, "training_authorized": False}
            msha = _write(wdir / "manifest.json", canon(manifest))
            # controller truth
            tdir = u.truth_root / oid; touts = {}
            op = (np.arange(n_cells) % 3).astype(np.int64) if name == "Q11_OMITTED_OPERATOR" else np.zeros(n_cells, dtype=np.int64)
            touts["design/op.npy"] = _save_npy(tdir / "design/op.npy", op)
            touts["support.npy"] = _save_npy(tdir / "support.npy", support)
            world_truth = {}
            for part in ("detection", "positive"):
                arrays = {"intercept": rng.normal(0.0, 0.5, N_GENE), "depth1": rng.normal(0.0, 0.3, N_GENE),
                          "depth2": rng.normal(0.0, 0.1, N_GENE), "class_contrasts": rng.normal(0.0, 0.4, (N_GENE, 2)),
                          "source_contrasts": rng.normal(0.0, 0.4, (N_GENE, 2)), "donor_sd": rng.uniform(0.2, 0.6, N_GENE),
                          "donor_effects": rng.normal(0.0, 0.4, (N_DONOR, N_GENE))}
                if part == "detection": arrays["prevalence"] = rng.uniform(0.02, 0.9, N_GENE)
                else: arrays["sigma"] = rng.uniform(0.5, 1.0, N_GENE)
                for key, value in arrays.items():
                    touts[f"truth/{part}/{key}.npy"] = _save_npy(tdir / f"truth/{part}/{key}.npy", value)
                if name == "Q11_OMITTED_OPERATOR":
                    touts[f"truth/operator_offsets/{part}.npy"] = _save_npy(tdir / f"truth/operator_offsets/{part}.npy", rng.normal(0.0, 0.3, (3, N_GENE)))
                world_truth[part] = arrays
            tmanifest = {"benchmark_run": False, "blinded_fit_manifest_sha256": msha, "design_sha256": sha_bytes(f"design-{i}".encode()),
                         "final_contract_sha256": SOURCE, "generated_outputs": dict(sorted(touts.items())),
                         "generator_bundle_sha256": GENERATOR, "mode": T.MODE, "opaque_world_id": oid,
                         "pairing_amendment_sha256": PAIRING, "qualification_fits_run": 0,
                         "qualification_payload_sha256": sha_bytes(b"synthetic-payload"), "schema": T.TRUTH_SCHEMA,
                         "scientific_truth_sha256": sha_bytes(f"truth-{i}".encode()), "seed_parent_world_index": i,
                         "seed_root": 7919, "training_authorized": False, "world_index": i, "world_name": name}
            _write(tdir / "manifest.json", canon(tmanifest))
            truths[oid] = world_truth
        index = {"schema": "V79_V2_CORE_BLINDED_FIT_INDEX_V1", "final_contract_sha256": SOURCE, "pairing_amendment_sha256": PAIRING,
                 "generator_bundle_sha256": GENERATOR, "world_count": len(names),
                 "worlds": [{"opaque_world_id": oid, "manifest_path": f"{oid}/manifest.json",
                             "manifest_sha256": sha_file(u.fit_root / oid / "manifest.json")} for oid in sorted(u.world_by_name.values())],
                 "benchmark_run": False, "qualification_fits_run": 0, "training_authorized": False}
        _write(u.fit_root / INDEX_NAME, canon(index))
        _write(u.package_dir / ROOT_MANIFEST_NAME, canon({"schema": "SYNTHETIC_UNBLINDED_ROOT_MANIFEST", "worlds": u.world_by_name}))
        _write(u.package_dir / "runtime_environment_receipt.json", canon({"schema": "SYNTHETIC_RUNTIME"}))
        _write(u.package_dir / "realization_authorization.json", canon({"schema": "SYNTHETIC_REALIZATION_AUTHORIZATION"}))
        (u.package_dir / F.FIT_ROOT_NAME).mkdir(parents=True, exist_ok=True)
        shutil.copyfile(u.fit_root / INDEX_NAME, u.package_dir / F.FIT_ROOT_NAME / INDEX_NAME)
        for oid in u.world_by_name.values():
            (u.package_dir / F.FIT_ROOT_NAME / oid).mkdir(parents=True, exist_ok=True)
            shutil.copyfile(u.fit_root / oid / "manifest.json", u.package_dir / F.FIT_ROOT_NAME / oid / "manifest.json")
        u.reseal_realization(seal_downstream=False)
        u._write_custody(contract)
        u._write_fit_records(truths)
        u.reseal_campaign()
        return u

    def _write_custody(self, contract) -> None:
        view = PREP.build_fit_contract_view(contract)
        view_sha = _write(self.custody_dir / C.FIT_VIEW_NAME, FC.canonical_bytes(view))
        index = json.loads((self.fit_root / INDEX_NAME).read_text(encoding="utf-8"))
        self.queue = QP.build_qualification_queue(view, index)
        ledger = sorted(({"fit_id": q["fit_id"], "primary_seed": int(q["fit_id"][:8], 16)} for q in self.queue), key=lambda x: x["fit_id"])
        auth = {"schema": C.AUTH_SCHEMA, "qualification_campaign_authorized": True, "benchmark_controller_pass": True,
                "contract_sha256": SOURCE, "blinded_index_sha256": sha_file(self.fit_root / INDEX_NAME), "fit_seed_ledger": ledger,
                "scoring_authorized": False, "training_authorized": False}
        auth_sha = _write(self.custody_dir / C.AUTH_NAME, canon(auth))
        self._custody_parts = {"view_sha": view_sha, "auth_sha": auth_sha}
        self.reseal_custody(seal_downstream=False)

    def _write_fit_records(self, truths) -> None:
        nd_oid = self.world_by_name[NOT_DIAGNOSED_WORLD]
        nd = {(nd_oid, g, part) for g, part in NOT_DIAGNOSED_SPECS}
        self.not_diagnosed_fit_ids = set()
        self.result_dir.mkdir(parents=True, exist_ok=True)
        index = json.loads((self.fit_root / INDEX_NAME).read_text(encoding="utf-8"))
        n_cells = len(_design()["src"])
        for item in self.queue:
            fid = item["fit_id"]; oid = item["opaque_world_id"]; g = int(item["gene_index"]); part = item["part"]
            rng = np.random.default_rng(int(fid[:12], 16))
            arr = truths[oid][part]
            truth = {"intercept": [arr["intercept"][g]], "depth1": [arr["depth1"][g]], "depth2": [arr["depth2"][g]],
                     "class": arr["class_contrasts"][g], "source": arr["source_contrasts"][g], "donor_sd": [arr["donor_sd"][g]],
                     "donor_effects": arr["donor_effects"][:, g]}
            labels = {"intercept": ["intercept"], "depth1": ["depth1"], "depth2": ["depth2"], "class": ["helmert_0", "helmert_1"],
                      "source": ["helmert_0", "helmert_1"], "donor_sd": ["donor_sd"], "donor_effects": [f"donor_{d}" for d in range(N_DONOR)]}
            if part == "positive":
                truth["sigma"] = [arr["sigma"][g]]; labels["sigma"] = ["sigma"]
            summary = {"schema": "V79_V2_CORE_IDENTIFIED_POSTERIOR_SUMMARY_V1", "part": part,
                       "identification": {"class": {"mode": "helmert", "observed_levels": [0, 1, 2], "reference_level": None},
                                          "source": {"mode": "helmert", "observed_levels": [0, 1, 2], "reference_level": None},
                                          "donor_codes": list(range(N_DONOR))},
                       "quantities": {k: _summary_quantity(truth[k], labels[k], rng) for k in truth}}
            if part == "detection":
                held = {mode: {"schema": "V79_V2_CORE_DETECTION_HELDOUT_V1", "replicate_mode": mode, "posterior_draws": 200,
                               "gauss_hermite_nodes": None if mode == "same_donor" else 40, "n_measured": n_cells,
                               "mean_log_loss": 0.6 + 0.01 * rng.random(), "predicted_prevalence": 0.55, "observed_prevalence": 0.5,
                               "calibration_bins": _calibration(n_cells, 0.55, 0.5)} for mode in ("same_donor", "new_donor")}
            else:
                held = {mode: {"schema": "V79_V2_CORE_POSITIVE_HELDOUT_V1", "replicate_mode": mode, "posterior_draws": 200,
                               "gauss_hermite_nodes": None if mode == "same_donor" else 40, "n_positive": n_cells // 2,
                               "mean_lpd": -1.1 - 0.01 * rng.random()} for mode in ("same_donor", "new_donor")}
            draws_name = f"donor_effect_draws_{fid}.npz"
            with (self.result_dir / draws_name).open("wb") as fh:
                np.savez(fh, draws=rng.standard_normal((4, N_DONOR)))
            seed = int(fid[:8], 16)
            not_diag = (oid, g, part) in nd
            attempts = [{"stage": "PRIMARY", "seed": seed}] + ([{"stage": "ESCALATION", "seed": seed}, {"stage": "EXTENSION", "seed": seed}] if not_diag else [])
            rec = {"schema": "V79_V2_CORE_FIT_RECORD_V1", "execution_mode": "QUALIFICATION", "fit_id": fid, "opaque_world_id": oid,
                   "gene_index": g, "part": part, "input_manifest_sha256": item["world_manifest_sha256"], "contract_sha256": SOURCE,
                   "code_sha": CAMPAIGN_CODE_SHA, "benchmark_run": False, "qualification_fits_run": 1, "scoring_run": False,
                   "truth_accessed": False, "training_authorized": False, "attempts": attempts,
                   "final_diagnosis": "NOT_DIAGNOSED" if not_diag else "COMPLETE",
                   "final_diagnostics": {"divergences": 0, "worst_rhat": 1.2 if not_diag else 1.001, "worst_ess_bulk": 50 if not_diag else 900,
                                         "worst_ess_tail": 40 if not_diag else 800, "mean_tree_steps": 15},
                   "scoring_summary": summary,
                   "ppc": [{"name": "zero_fraction", "observed": 0.4, "p_value": 0.45}, {"name": "mean", "observed": 1.0, "p_value": 0.3}],
                   "heldout_predictive": held,
                   "posterior_artifacts": {"donor_effect_draws": {"path": draws_name, "sha256": sha_file(self.result_dir / draws_name)}}}
            _write(self.result_dir / f"fit_{fid}.json", canon(rec))
            if not_diag: self.not_diagnosed_fit_ids.add(fid)
        assert len(self.not_diagnosed_fit_ids) == 3 and index["world_count"] == 12

    # ---------------------------------------------------------------- sealing
    def reseal_realization(self, *, seal_downstream: bool = True) -> None:
        ledger = {}
        for rel in TOP_LEVEL:
            ledger[rel] = sha_file(self.package_dir / rel)
        for rel, p in _files(self.fit_root).items():
            ledger[f"{F.FIT_ROOT_NAME}/{rel}"] = sha_file(p)
        for rel, p in _files(self.truth_root).items():
            ledger[f"controller_truth/{rel}"] = sha_file(p)
        ledger_raw = "".join(f"{rel}\t{ledger[rel]}\n" for rel in sorted(ledger)).encode("utf-8")
        ledger_sha = _write(self.realization_dir / LEDGER_NAME, ledger_raw)
        truth = [r for r in ledger if r.startswith("controller_truth/")]
        committed = _files(self.package_dir)
        receipt = {"schema": "V79_V2_CORE_REALIZATION_AUDIT_FREEZE_RECEIPT_V1",
                   "status": "REALIZATION_AUDIT_EVIDENCE_FROZEN__CONTROLLER_INDEPENDENT_BYTE_AUDIT_REQUIRED",
                   "source_checkout_sha": "3" * 40, "source_realized_directory": "synthetic", "authorization_receipt_sha256": "4" * 64,
                   "root_manifest_sha256": ledger[ROOT_MANIFEST_NAME], "world_set_directory_digest": directory_digest(ledger),
                   "directory_digest_rule": "sha256 over sorted portable relative paths of: utf8(rel) 0x00 sha256(file bytes) 0x00",
                   "total_file_count": len(ledger), "world_count": 12, "mode": T.MODE,
                   "runtime_environment_receipt_sha256": ledger["runtime_environment_receipt.json"],
                   "blinded_fit_index_sha256": ledger[f"{F.FIT_ROOT_NAME}/{INDEX_NAME}"], "complete_ledger": LEDGER_NAME,
                   "complete_ledger_sha256": ledger_sha, "complete_ledger_equals_post_realization_records_ledger": True,
                   "source_unchanged_after_freeze": True, "committed_package_root": "package/",
                   "committed_package_file_count": len(committed), "committed_top_level_files": list(TOP_LEVEL) + [f"{F.FIT_ROOT_NAME}/{INDEX_NAME}"],
                   "committed_blinded_manifest_count": 12, "committed_controller_truth_file_count": len(truth),
                   "committed_controller_truth_manifest_count": 12, "committed_controller_truth_authority_array_count": len(truth) - 12,
                   "not_committed_file_count": len(ledger) - len(committed),
                   "not_committed_observation_array_count": sum("/observations/" in r for r in ledger), "not_committed_note": "synthetic",
                   "copy_method": "synthetic", "benchmark_run": False, "qualification_fits_run": 0, "scoring_run": False,
                   "real_train_posterior_run": False, "factorial_science_run": False, "training_authorized": False}
        receipt_sha = _write(self.realization_dir / REALIZATION_RECEIPT_NAME, (json.dumps(receipt, indent=2, sort_keys=True) + "\n").encode("utf-8"))
        self.bindings.update({"root_manifest_sha256": ledger[ROOT_MANIFEST_NAME], "blinded_index_sha256": ledger[f"{F.FIT_ROOT_NAME}/{INDEX_NAME}"],
                              "realization_audit_receipt_sha256": receipt_sha, "realization_ledger_sha256": ledger_sha,
                              "world_set_directory_digest": receipt["world_set_directory_digest"], "realized_file_count": len(ledger),
                              "controller_truth_file_count": len(truth), "committed_package_file_count": len(committed),
                              "blinded_fit_file_count": sum(r.startswith(F.FIT_ROOT_NAME + "/") for r in ledger)})
        if seal_downstream:
            self.reseal_authorization()

    def reseal_custody(self, *, seal_downstream: bool = True) -> None:
        receipt = {"schema": C.RECEIPT_SCHEMA, "executor_code_head": self.bindings.get("custody_executor_code_head", CAMPAIGN_CODE_SHA),
                   "source_contract_sha256": SOURCE, "root_manifest_sha256": self.bindings["root_manifest_sha256"],
                   "blinded_index_sha256": sha_file(self.fit_root / INDEX_NAME), "blinded_directory_digest": C._digest(self.fit_root),
                   "fit_contract_view_path": C.FIT_VIEW_NAME, "fit_contract_view_sha256": sha_file(self.custody_dir / C.FIT_VIEW_NAME),
                   "authorization_path": C.AUTH_NAME, "authorization_sha256": sha_file(self.custody_dir / C.AUTH_NAME), "fit_count": 1056,
                   "ppc_draws": 1000, "donor_draws_stored": 200, "qualification_fits_run": 0, "scoring_run": False, "truth_accessed": False,
                   "training_authorized": False}
        self.bindings["custody_receipt_sha256"] = _write(self.custody_dir / C.RECEIPT_NAME, canon(receipt))
        if seal_downstream:
            self.reseal_campaign()

    def reseal_campaign(self, *, fit_rows: list[dict] | None = None, code_sha: str | None = None) -> None:
        """Rebuild the campaign receipt (queue order unless rows are given), the result ledger and the authorization."""
        code = code_sha or self.bindings.get("campaign_code_sha", CAMPAIGN_CODE_SHA)
        if fit_rows is None:
            fit_rows = [{"fit_id": q["fit_id"], "path": f"fit_{q['fit_id']}.json", "sha256": sha_file(self.result_dir / f"fit_{q['fit_id']}.json")}
                        for q in self.queue]
        rec = RQ.campaign_receipt_skeleton(code_sha=code, custody_receipt_sha=self.bindings["custody_receipt_sha256"], fit_count=1056)
        rec["fit_records"] = fit_rows; rec["qualification_fits_run"] = 1056
        self.bindings["campaign_receipt_sha256"] = _write(self.result_dir / CAMPAIGN_RECEIPT_NAME, canon(rec))
        self.bindings["campaign_code_sha"] = code
        self.reseal_result_ledger()

    def reseal_result_ledger(self) -> None:
        lines = [f"{sha_file(p)} {p.stat().st_size} *result/{p.name}" for p in sorted(self.result_dir.iterdir()) if p.is_file()]
        self.bindings["result_ledger_sha256"] = _write(self.result_ledger_path, ("\n".join(lines) + "\n").encode("utf-8"))
        self.bindings["result_file_count"] = len(lines)
        self.reseal_authorization()

    def reseal_authorization(self, *, scorer_code_sha: str | None = None, **overrides) -> None:
        auth = {"schema": A.AUTH_SCHEMA, "scoring_authorized": True, "qualification_campaign_controller_pass": True,
                "contract_sha256": A.CONTRACT_SHA256, "root_manifest_sha256": self.bindings["root_manifest_sha256"],
                "blinded_index_sha256": self.bindings["blinded_index_sha256"],
                "realization_audit_receipt_sha256": self.bindings["realization_audit_receipt_sha256"],
                "campaign_receipt_sha256": self.bindings.get("campaign_receipt_sha256", "0" * 64),
                "scorer_code_sha": scorer_code_sha or self.scorer_code_sha, "real_train_posterior_authorized": False,
                "factorial_science_authorized": False, "training_authorized": False}
        auth.update(overrides)
        self.bindings["scoring_authorization_sha256"] = _write(self.scoring_auth_path, canon(auth))

    # ---------------------------------------------------------------- test helpers
    def copy_to(self, dst: Path) -> "Universe":
        shutil.copytree(self.root, dst)
        u = Universe(dst)
        u.bindings = dict(self.bindings); u.world_by_name = dict(self.world_by_name)
        u.queue = [dict(q) for q in self.queue]; u.not_diagnosed_fit_ids = set(self.not_diagnosed_fit_ids)
        u._custody_parts = dict(self._custody_parts)
        return u

    def patch(self, monkeypatch) -> None:
        """Point every frozen production identity at this synthetic universe."""
        b = self.bindings
        frozen = {"CAMPAIGN_RECEIPT_SHA256": b["campaign_receipt_sha256"], "CAMPAIGN_CODE_SHA": CAMPAIGN_CODE_SHA,
                  "CUSTODY_RECEIPT_SHA256": b["custody_receipt_sha256"], "RESULT_LEDGER_SHA256": b["result_ledger_sha256"],
                  "RESULT_FILE_COUNT": b["result_file_count"], "ROOT_MANIFEST_SHA256": b["root_manifest_sha256"],
                  "BLINDED_INDEX_SHA256": b["blinded_index_sha256"], "REALIZATION_AUDIT_RECEIPT_SHA256": b["realization_audit_receipt_sha256"],
                  "REALIZATION_LEDGER_SHA256": b["realization_ledger_sha256"], "WORLD_SET_DIRECTORY_DIGEST": b["world_set_directory_digest"],
                  "REALIZED_FILE_COUNT": b["realized_file_count"], "CONTROLLER_TRUTH_FILE_COUNT": b["controller_truth_file_count"],
                  "COMMITTED_PACKAGE_FILE_COUNT": b["committed_package_file_count"], "BLINDED_FIT_FILE_COUNT": b["blinded_fit_file_count"],
                  "NOT_DIAGNOSED_FIT_IDS": frozenset(self.not_diagnosed_fit_ids)}
        for name, value in frozen.items():
            monkeypatch.setattr(A, name, value, raising=False)
        monkeypatch.setattr(F, "QUALIFICATION_ROOT_MANIFEST_SHA256", b["root_manifest_sha256"])
        monkeypatch.setattr(F, "QUALIFICATION_INDEX_SHA256", b["blinded_index_sha256"])
        monkeypatch.setattr(C, "QUALIFICATION_INDEX_SHA256", b["blinded_index_sha256"])

    def run_kwargs(self, **overrides) -> dict:
        kw = {"repo_root": ROOT, "scorer_code_sha": self.scorer_code_sha, "authorization_path": self.scoring_auth_path,
              "authorization_sha256": self.bindings["scoring_authorization_sha256"], "campaign_result_dir": self.result_dir,
              "result_ledger_path": self.result_ledger_path, "custody_dir": self.custody_dir,
              "realization_dir": self.realization_dir, "output_dir": self.output_dir}
        kw.update(overrides)
        return kw
