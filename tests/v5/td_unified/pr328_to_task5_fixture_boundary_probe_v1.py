"""Two-process, two-exact-head synthetic-to-fixture *test-of-interface*.

Producer imports PR #328 at its frozen commit, emits only reader-fit-like
synthetic RNA observations. Consumer imports PR #451's unmodified Task5 and
post-TD code. This test-only projection is NOT an authenticated production
observation producer, issuer, registered adapter, qualified scientific gate,
mode-equivalence proof, real human target, or JEPA training.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys

PR328 = "25bbdbe18aa5ed3c8a39a7e4295bc36de1e328ec"
PR451 = "bbdf9a90973303e41cee6d8bd9d05de38e9b828a"
BRIDGE_BLOB = "7ee09461cab959f4cfe67d2dc945fbcc372a0654"
CASE_BLOB = "23bbdcfc3234b7d621beb870fa019b34822446af"
MODE_BLOB = "e0bf61113f7c1acc46cc4b46cd69ca8b1092594b"

def require(ok: bool, message: str) -> None:
    if not ok:
        raise AssertionError(message)

def git(*args: str, cwd: Path) -> str:
    return subprocess.check_output(["git", *args], cwd=cwd, text=True).strip()

def digest(v: object) -> str:
    return hashlib.sha256(json.dumps(v, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()).hexdigest()

def produce(root: Path, output: Path) -> None:
    require(git("rev-parse", "HEAD", cwd=root) == PR328, "wrong source-generator head")
    sys.path.insert(0, str(root))
    from scripts.v79.unified_synthetic_integration_v1 import (
        UnifiedBiologyConfig, build_unified_biology, validate_integration_manifest
    )
    from scripts.v79.unified_synthetic_fit_view_v1 import (
        UnifiedObservationConfig, observe_unified_world, fit_view_sha256
    )
    manifest_path=root/"results/v79/unified_synthetic/UNIFIED_SYNTHETIC_INTEGRATION_MANIFEST_V1.json"
    manifest_bytes=manifest_path.read_bytes()
    manifest=json.loads(manifest_bytes)
    authority=validate_integration_manifest(manifest)
    require(not any(authority.authority.values()), "synthetic world authority escalated")
    # A *new ephemeral deterministic fixture*, not the protected or pre-existing
    # PR328 V2 receipt/world and not the production V3.1.1 realization.
    world=build_unified_biology(UnifiedBiologyConfig(n_cells=120, n_genes=24, n_donors=10),seed=31)
    fit=observe_unified_world(world, UnifiedObservationConfig(), seed=32)
    require(fit.values.ndim == 2 and fit.support.shape == fit.values.shape, "observation shape")
    require(not bool((fit.values[~fit.support] != 0).any()), "unmeasured value cannot become a scalar")
    choices=[i for i in range(len(fit.donor_id))
             if str(fit.split[i])=="train" and int(fit.values[i].sum())>0][:18]
    require(len(choices)>=4 and len({int(fit.donor_id[i]) for i in choices})>=2,
            "not enough lawful synthetic training-fold cells")
    universe=[f"SYNTH_ADDR_{int(a):04d}" for a in fit.address_index]
    rights={"probe_mapping":"synthetic_train_to_reader_fit_fixture_only",
            "no_human_evidence_rights_authenticated":True,"count_library":"sum_all_fixture_gene_counts",
            "not_an_independent_physical_library_size":True}
    obs=[]
    for i in choices:
        mass=int(fit.values[i].sum())
        require(mass>0, "positive cell mass required by fixture contract")
        for j,address in enumerate(universe):
            measured=bool(fit.support[i,j])
            count=int(fit.values[i,j]) if measured else None
            obs.append({
                "cell_id":str(fit.rna_entity_id[i]),
                "donor_id":f"D{int(fit.donor_id[i]):04d}",
                "source_id":str(fit.source[i]),
                "operator_id":str(fit.operator[i]),
                "address_id":address,
                "state":"MEASURED_SCALAR" if measured else "STRUCTURALLY_UNMEASURED",
                "count":count,
                "library_size":mass if measured else None,
                "evidence_right":"RNA:TEST_FIXTURE_ONLY",
            })
    case={
        "schema":"KNOWN_TRUTH_CASEBUNDLE_V1",
        "case_id":"PR328_EPHEMERAL_RNA_FIT_FIXTURE_ONLY",
        "authority_scope":"FIXTURE_ONLY",
        "manifest_sha256":hashlib.sha256(manifest_bytes).hexdigest(),
        "population_access_policy_sha256":digest(rights),
        "address_universe_sha256":digest(universe),
        "reader_partition":"reader_fit",
        "observations":obs,
    }
    # DO NOT include any world/latent/rare-program/controller hidden truth.
    out={
        "probe_schema":"PR328_TO_PR451_BOUNDARY_PROBE_V1",
        "producer_head":PR328,
        "world_sha256":world.world_hash,
        "source_fit_view_sha256":fit_view_sha256(fit),
        "source_counts_sha256":fit.counts_hash,
        "source_manifest_bytes_sha256":case["manifest_sha256"],
        "sampled_cells":len(choices),
        "sampled_donors":len({int(fit.donor_id[i]) for i in choices}),
        "case":case,
        "limits":[
          "Synthetic newly generated fixture, not PR328 frozen production world",
          "Only RNA scalar/structural support; ATAC and context NOT conveyed",
          "Train split mapped to reader_fit shape only, not Task2 real partition",
          "Sum of fixture gene counts is not externally authenticated physical library mass",
          "No measured collision, rights-withheld proof, query exclusion or external issuer",
          "No synthetic truth, source target label or controller result transmitted"
        ],
    }
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(out,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print(f"PR328_FIXTURE_OBSERVATIONS_EXPORTED__NO_TRUTH__{len(obs)}_ATOMS")

def _stage(role: str):
    def step(value):
        # Imported by the test handler, not captured in its closure. The
        # existing PR440 fingerprint contract permits only primitive captures.
        from scripts.v5.td_unified.canonical_v1 import canonical_sha256
        return {"fixture_stage":role,"previous_sha256":canonical_sha256(value)}
    return step

def consume(root: Path, input_path: Path, report_path: Path) -> None:
    require(git("rev-parse", f"{PR451}:scripts/v5/td_unified/post_td_fixture_bridge_v1.py",cwd=root)==BRIDGE_BLOB,
            "PR451 bridge source identity drift")
    require(git("hash-object", "scripts/v5/td_unified/post_td_fixture_bridge_v1.py",cwd=root)==BRIDGE_BLOB,
            "active PR451 bridge changed")
    require(git("hash-object", "scripts/v5/td_unified/casebundle_v1.py",cwd=root)==CASE_BLOB,
            "active Task5 case validation changed")
    require(git("hash-object", "scripts/v5/td_unified/mode_equivalence_v1.py",cwd=root)==MODE_BLOB,
            "active Task5 in-process trace changed")
    sys.path.insert(0,str(root))
    from scripts.v5.td_unified.casebundle_v1 import validate_casebundle, CaseBundleError
    from scripts.v5.td_unified.mode_equivalence_v1 import SCIENTIFIC_ROLES, FixtureStage
    from scripts.v5.td_unified.post_td_fixture_bridge_v1 import stage_fixture_downstream
    raw=json.loads(input_path.read_text(encoding="utf-8"))
    require(raw["producer_head"]==PR328 and raw["probe_schema"]=="PR328_TO_PR451_BOUNDARY_PROBE_V1",
            "wrong probe source")
    case=raw["case"]
    require(set(case)=={
        "schema","case_id","authority_scope","manifest_sha256",
        "population_access_policy_sha256","address_universe_sha256",
        "reader_partition","observations"
    }, "producer leaked sidecar/truth into case")
    require(len(case["observations"])==raw["sampled_cells"]*24, "atoms missing from source projection")
    check=validate_casebundle(case)
    require(check["status"]=="CASEBUNDLE_FIXTURE_VALIDATED_NO_AUTHORITY", "not fixture receipt")
    require(check["authority_effect"]=="NONE" and check["externally_authenticated"] is False,
            "fixture unexpectedly authorized")
    stages=tuple(FixtureStage(role=role, handler=_stage(role)) for role in SCIENTIFIC_ROLES)
    none=stage_fixture_downstream(case_payload=case,stages=stages,
           fixture_qualifications={"C1":"FAIL","C3":"NOT_ESTIMABLE"})
    positive=stage_fixture_downstream(case_payload=case,stages=stages,
           fixture_candidate="C1",fixture_qualifications={"C1":"PASS"})
    require(none["target_candidate_fixture"]=="NONE" and none["post_td_portfolio"] is None,
            "false target selection on negative fixture evidence")
    require(positive["target_candidate_fixture"]=="C1" and positive["post_td_portfolio"] is not None,
            "existing fixture policy not exercised")
    require(positive["post_td_portfolio"]["blocks"][0]["qualification_receipt"]["receipt_class"]==
            "TASK5_PLANTED_FIXTURE_LABEL", "source of fixture PASS label lost")
    require(positive["post_td_portfolio"]["blocks"][0]["qualification_receipt"]["biological_qualification"] is False,
            "fixture false biological claim")
    for result in (none,positive):
        require(result["authenticated_target_bundle_consumed"] is False,"forged TQB claim")
        require(result["mode_path_receipt"]["status"]==
                "SAME_PROCESS_SELF_COMPARISON__NOT_MODE_EQUIVALENCE_EVIDENCE","false A7")
        for flag in ("same_code_path_authorized","human_execution_authorized",
                     "real_training_authorized","stage4_authorized"):
            require(result[flag] is False,"authority promotion: "+flag)
    leak=deepcopy(case)
    leak["latent_truth"]={"fake":"forbidden"}
    try:
        validate_casebundle(leak)
    except CaseBundleError:
        pass
    else:
        raise AssertionError("synthetic controller truth could enter fixture CaseBundle")
    # A valid-looking but replaced manifest digest *does* pass. This verifies
    # an important LIMIT, not a vulnerability fixed by this test.
    fake=deepcopy(case);fake["manifest_sha256"]="f"*64
    opaque_check=validate_casebundle(fake)
    require(opaque_check["externally_authenticated"] is False,
            "faked manifest incorrectly authenticated")
    require(opaque_check["observable_sha256"]!=check["observable_sha256"],
            "case content checksum failed to react")
    result={
        "schema":"PR328_TO_PR451_TWO_HEAD_BOUNDARY_RESULT_V1",
        "source_producer_head":PR328,
        "source_consumer_base_head":PR451,
        "synthetic_world_sha256":raw["world_sha256"],
        "source_fit_view_sha256":raw["source_fit_view_sha256"],
        "fit_only_casebundle_sha256":check["observable_sha256"],
        "source_generated_measurement_atoms":len(case["observations"]),
        "training_fold_fixture_cells":raw["sampled_cells"],
        "training_fold_fixture_donors":raw["sampled_donors"],
        "two_processes":True,
        "pr451_casebundle_validation":"EXECUTED_FIXTURE_ONLY",
        "pr451_same_process_dual_trace":"EXECUTED_DIAGNOSTIC_ONLY",
        "pr451_target_none_and_planted_C1_portfolio":"EXECUTED_FIXTURE_ONLY",
        "production_adapter_qualified":False,
        "actual_registered_gate_executor_consumed":False,
        "external_source_issuer_authenticated":False,
        "real_target_bundle_issued":False,
        "genuine_independent_A7_qualified":False,
        "real_training_authorized":False,
        "limits":raw["limits"]+[
            "Test-local projection, not original producer of Task5 authority",
            "CaseBundle accepts a swapped 64-hex manifest claim without a resolving source issuer",
            "Stage handlers are test fixture functions, not registered real gate producer/executor code",
            "Positive C1 portfolio is induced from a planted PASS label, not measured biological evidence"
        ]
    }
    report_path.parent.mkdir(parents=True,exist_ok=True)
    report_path.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("PR328_WORLD_TO_PR451_CASEBUNDLE_AND_POST_TD_FIXTURE_BOUNDARY_PASS__NO_REAL_AUTHORITY")

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("mode",choices=["produce","consume"])
    ap.add_argument("--source-root",type=Path)
    ap.add_argument("--payload",type=Path,required=True)
    ap.add_argument("--report",type=Path)
    args=ap.parse_args()
    if args.mode=="produce":
        require(args.source_root is not None,"PR328 source root required")
        produce(args.source_root.resolve(),args.payload.resolve())
    else:
        require(args.report is not None,"report path required")
        consume(Path(__file__).resolve().parents[3],args.payload.resolve(),args.report.resolve())
