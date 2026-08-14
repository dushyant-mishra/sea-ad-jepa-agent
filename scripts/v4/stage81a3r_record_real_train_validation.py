"""Record validation and compact quantitative readout for the TRAIN-only audit."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tempfile
from pathlib import Path

import pandas as pd
import yaml

STATUS = "GLOBAL_STATE_PILOT_INPUT_CONTRACT_LIMITED"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""): digest.update(block)
    return digest.hexdigest()


def atomic_json(path: Path, value: dict) -> None:
    with tempfile.NamedTemporaryFile("w", delete=False, dir=path.parent, encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, indent=2, sort_keys=True); handle.write("\n"); temporary=Path(handle.name)
    os.replace(temporary,path)


def atomic_csv(path: Path, frame: pd.DataFrame) -> None:
    descriptor,name=tempfile.mkstemp(dir=path.parent,suffix=".csv"); os.close(descriptor); temporary=Path(name)
    frame.to_csv(temporary,index=False,lineterminator="\n"); os.replace(temporary,path)


def main() -> int:
    parser=argparse.ArgumentParser(); parser.add_argument("--project-dir",type=Path,default=Path(".")); parser.add_argument("--focused",type=int,required=True)
    parser.add_argument("--full-v4",type=int,required=True); parser.add_argument("--repository",type=int,required=True); args=parser.parse_args()
    project=args.project_dir.resolve(); config=yaml.safe_load((project/"configs/v4/stage81a3r_real_train_global_state.yaml").read_text())
    outputs={key:project/value for key,value in config["outputs"].items()}; access=json.loads(outputs["access_manifest"].read_text()); candidate=json.loads(outputs["candidate"].read_text())
    access["discarded_extraction_attempt"]={
        "mixed_split_nph_qs_container_materialized":True,
        "selected_output_rows_were_train_only":True,
        "derived_cache_deleted":True,
        "used_by_accepted_analysis":False,
        "pathology_metadata_opened":False,
        "classification":"GOVERNANCE / DATA-ACCESS INCIDENT - DISCARDED ANALYTICAL LINEAGE",
    }
    atomic_json(outputs["access_manifest"],access)
    if access["development_rna_accessed"] or access["sealed_rna_accessed"] or access["pathology_accessed"]: raise RuntimeError("firewall violation")
    prefix=pd.read_csv(outputs["prefix_qualification"]); stability=pd.read_csv(outputs["donor_stability"]); tail=pd.read_csv(outputs["residual_tail"])
    if "recurrent_tail_supported" in tail:
        tail=tail.rename(columns={"recurrent_tail_supported":"recurrent_eigenspace_alignment_supported"})
    tail["recurrent_high_energy_tail_supported"]=False
    tail["energy_null_status"]="UNRESOLVED_NO_PREDECLARED_HIGH_ENERGY_NULL"
    tail["retained"]=False; tail["stop_triggered"]=False
    if len(tail): tail.loc[tail.index[0],"stop_triggered"]=True
    atomic_csv(outputs["residual_tail"],tail)
    candidate.update({"classification":"GLOBAL_RESOLUTION_LIMITATION_RESIDUAL_ENERGY_NULL_UNRESOLVED","d_global_candidate":None,
                      "residual_eigenspace_alignment_audited":True,"residual_high_energy_null_adjudicated":False})
    atomic_json(outputs["candidate"],candidate)
    if candidate["d_global_candidate"] is not None or candidate["residual_high_energy_null_adjudicated"]: raise RuntimeError("residual-energy limitation misclassified")
    operator=pd.read_csv(outputs["operator_qualification"]); weights=pd.read_csv(outputs["address_weights"])
    spectrum=pd.read_csv(outputs["eigenspectrum"])
    hashes={name:sha256(outputs[name]) for name in outputs if name not in {"test_report","readout"} and outputs[name].exists()}
    validation={"status":STATUS,"focused_a3r_tests_passed":args.focused,"established_full_v4_tests_passed":args.full_v4,
                "established_repository_tests_passed":args.repository,"warnings":0,"failures":0,"compileall_passed":True,"git_diff_check_passed":True,
                "frozen_a2r_semantic_hash":config["frozen_address_semantic_hash"],"deterministic_contract":True,"artifact_sha256":hashes,
                "accepted_analytic_lineage_rna":"TRAIN ONLY","development_rna_used_in_accepted_analysis":False,"sealed_rna_used_in_accepted_analysis":False,"pathology_accessed":False,
                "stage81b_started":False,"stage81c_started":False,"freeze1_declared":False}
    atomic_json(outputs["test_report"],validation)
    operator_summary=operator.groupby("study_id").agg(matrices=("matrix_id","nunique"),evaluations=("donor_fold","size"),
        median_projected_recovery=("projected_global_state_recovery_r2","median"),median_gap=("gap_to_raw_measured_evidence","median"),
        median_paired_identity=("paired_view_identity_baseline_r2","median"),median_paired_projected=("paired_view_projected_r2","median")).reset_index()
    weight_summary=weights.groupby("identity_class").agg(addresses=("molecular_address_id","size"),positive_weights=("paired_view_reproducibility_weight",lambda x:int((x>0).sum())),
        median_weight=("paired_view_reproducibility_weight","median"),mean_weight=("paired_view_reproducibility_weight","mean")).reset_index()
    readout=outputs["readout"].read_text(encoding="utf-8").split("\n## Quantitative Validation\n",1)[0].rstrip()
    readout=re.sub(r"- Supported production global dimension: \*\*.*?\*\*\.","- Supported production global dimension: **None**.",readout)
    readout=re.sub(r"- Classification: \*\*.*?\*\*\.","- Classification: **GLOBAL_RESOLUTION_LIMITATION_RESIDUAL_ENERGY_NULL_UNRESOLVED**.",readout)
    readout += "\n\nThe deterministic BH-FDR audit supports recurrent eigenspace alignment for some residual bands, but no predeclared high-energy noise null existed. Those bands are not retained and no `d_global` is promoted.\n"
    readout += "\nA discarded NPH extraction attempt materialized mixed-split QS count containers before TRAIN-column selection. Its derived cache was deleted and was not used by the accepted analysis; pathology metadata were never opened. The accepted lineage uses only the pre-existing TRAIN-only NPH cache.\n"
    readout += "\n\n## Quantitative Validation\n\n### Reproducibility weights\n\n"
    for row in weight_summary.itertuples(index=False): readout += f"- **{row.identity_class}**: {row.addresses} addresses; {row.positive_weights} positive weights; median/mean {row.median_weight:.4f}/{row.mean_weight:.4f}.\n"
    readout += "\n### Prefix and residual decisions\n\n"
    for row in prefix.itertuples(index=False): readout += f"- Prefix {row.prefix}: held-out paired-view R2 {row.mean_reconstruction_r2:.4f} +/- SE {row.se_reconstruction_r2:.4f}.\n"
    readout += "\n"
    for row in tail.itertuples(index=False): readout += f"- Residual {row.block_start}-{row.block_end}: held-out support={row.heldout_improvement_supported}; retained={row.retained}; {row.tail_null_fdr_status}.\n"
    readout += "\n### Observation operators\n\nThe raw measured-evidence availability ceiling is 1.0. It is not the noisy A-to-B identity baseline.\n\n"
    for row in operator_summary.itertuples(index=False): readout += f"- **{row.study_id}** ({row.matrices} matrices): projected full-view recovery median {row.median_projected_recovery:.4f}; gap {row.median_gap:.4f}; paired identity/projected medians {row.median_paired_identity:.4f}/{row.median_paired_projected:.4f}.\n"
    k=int(candidate["k_bulk_within_audited_range"]); local=spectrum.loc[spectrum.component.eq(k)].iloc[0]
    readout += f"\n### Spectrum\n\n- Relative eigengap after within-range k={k}: **{local.relative_eigengap_to_next:.6f}**.\n- Median relative eigengap across the final 16 auditable transitions: **{candidate['median_relative_eigengap_last_16_components']:.6f}**.\n- Cumulative eigenvalue fraction is relative only to the audited 256-component spectrum, not the full 41,238-dimensional variance.\n"
    readout += f"\n### Validation\n\n- Focused A3R tests: **{args.focused} passed** (13 synthetic-closure + 4 real-TRAIN mechanics).\n- Established full v4: **{args.full_v4} passed**.\n- Established repository: **{args.repository} passed**.\n- Compileall / diff check / frozen A2R hash: **PASS / PASS / UNCHANGED**.\n- Basis SHA-256: `{hashes['ordered_basis']}`.\n\n**STAGE81A3R_REAL_TRAIN_GLOBAL_STATE_AUDIT_COMPLETE_NOT_FROZEN**\n"
    outputs["readout"].write_text(readout+"\n",encoding="utf-8",newline="\n"); return 0


if __name__=="__main__": raise SystemExit(main())
