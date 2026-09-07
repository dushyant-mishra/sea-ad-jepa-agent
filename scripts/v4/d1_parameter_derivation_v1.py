#!/usr/bin/env python3
"""D1 parameter derivation driver: Phase 0 + Phase 1 + gated production path.

Runs the fail-closed population audit, resolves the teacher readout seam, and
then attempts the production derivation. While the teacher gate is closed the
production path terminates `WAIT_HEALTHY_TRAINED_TEACHER` and writes no
production parameter artifact. That is the expected outcome today, not a
failure.

The config is validated here rather than trusted: a procedure-constants file
that had acquired a hand-entered production D, program count, neighbourhood
scale, tail cutpoint, stability cutoff or redundancy cutoff is a STOP, and so is
a numeric value colliding with a prohibited historical constant.
"""

from __future__ import annotations

import argparse
import io
import json
import re
import sys
from pathlib import Path
from typing import Any, Mapping

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts" / "v4"))

from d1_real_data_derivation_core_v1 import (  # noqa: E402
    PRODUCTION_FULL_FIT,
    PROHIBITED_HISTORICAL_VALUES,
    D1Provenance,
    emit_production_parameter,
    payload_root,
)
from d1_full_fit_population_audit_v1 import (  # noqa: E402
    STOP_AUTHORITY_UNREACHABLE,
    audit_full_fit_population,
)
from d1_teacher_state_stream_v1 import (  # noqa: E402
    WAIT_HEALTHY_TEACHER,
    resolve_teacher_readout,
    teacher_gate_open,
)

DEFAULT_CONFIG = REPO / "configs" / "v4" / "d1_real_data_derivation_v1.yaml"

# Config keys that would make the procedure-constants file a production
# parameter file. Matched on the key name, so a renamed section cannot smuggle
# one in under a different heading.
FORBIDDEN_CONFIG_KEY_PATTERNS = (
    r"^production_d$", r"^\s*d\s*$", r"^latent_dimension$", r"^n_components$",
    r"^program_count", r"^\bK\b$", r"^k$", r"^n_neighbors$", r"^knn",
    r"^neighborhood_(radius|scale|k)$", r"^resolution", r"^svd_components$",
    r"^candidate_rank$", r"^sketch_dimension$",
    r"^tail_score_cut", r"^score_cutpoint", r"^score_threshold",
    r"^stability_cut", r"^stability_threshold$",
    r"^redundancy_cut", r"^redundancy_threshold$", r"^correlation_cut",
    r"^donor_resamples$", r"^matched_null_replicates$",
)

STOP_CONFIG_HAS_PRODUCTION_VALUE = "STOP_D1_CONFIG_CONTAINS_PRODUCTION_ADAPTIVE_VALUE"
STOP_CONFIG_PROHIBITED_VALUE = "STOP_D1_CONFIG_CONTAINS_PROHIBITED_HISTORICAL_VALUE"


def _load_yaml(path: Path) -> Any:
    try:
        import yaml  # type: ignore
    except ImportError:
        return _minimal_yaml(path)
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _minimal_yaml(path: Path) -> dict[str, Any]:
    """Indentation-aware fallback for the restricted subset this config uses.

    Only mappings, scalars and '- ' lists appear in the config. A fallback is
    used rather than making PyYAML a hard dependency of the validator, because
    the validator must be runnable anywhere the config is reviewed.
    """
    root: dict[str, Any] = {}
    stack: list[tuple[int, Any]] = [(-1, root)]
    pending_list: list[Any] | None = None
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip())
        text = line.strip()
        if text.startswith("- "):
            if pending_list is None:
                continue
            pending_list.append(_scalar(text[2:].strip()))
            continue
        while stack and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]
        if text.endswith(":"):
            key = text[:-1].strip()
            child: dict[str, Any] = {}
            parent[key] = child
            stack.append((indent, child))
            pending_list = None
            # A key with no scalar may be either a mapping or a list; decide lazily.
            parent[key] = child
            holder: list[Any] = []
            child["__list__"] = holder
            pending_list = holder
        elif ":" in text:
            key, value = text.split(":", 1)
            parent[key.strip()] = _scalar(value.strip())
            pending_list = None
    return _prune(root)


def _scalar(text: str) -> Any:
    if text in ("true", "True"):
        return True
    if text in ("false", "False"):
        return False
    if text in ("null", "~", ""):
        return None
    try:
        return int(text)
    except ValueError:
        pass
    try:
        return float(text)
    except ValueError:
        return text.strip('"\'')


def _prune(node: Any) -> Any:
    if isinstance(node, dict):
        holder = node.get("__list__")
        others = {k: _prune(v) for k, v in node.items() if k != "__list__"}
        if holder and not others:
            return list(holder)
        return others
    return node


def walk_config(node: Any, prefix: str = "") -> list[tuple[str, Any]]:
    out: list[tuple[str, Any]] = []
    if isinstance(node, dict):
        for key, value in node.items():
            out.append((str(key), value))
            out.extend(walk_config(value, prefix + "/" + str(key)))
    elif isinstance(node, list):
        for item in node:
            out.extend(walk_config(item, prefix))
    return out


def validate_config_has_no_production_values(config_path: Path | str) -> dict[str, Any]:
    """A procedure-constants config must contain no Class-C production value."""
    path = Path(config_path)
    config = _load_yaml(path)
    entries = walk_config(config)
    offending_keys = []
    for key, value in entries:
        if isinstance(value, (dict, list)):
            continue
        for pattern in FORBIDDEN_CONFIG_KEY_PATTERNS:
            if re.match(pattern, key, flags=re.IGNORECASE):
                offending_keys.append({"key": key, "value": value, "pattern": pattern})
                break
    if offending_keys:
        raise AssertionError("%s: %r" % (STOP_CONFIG_HAS_PRODUCTION_VALUE, offending_keys))

    # Numeric collisions with prohibited historical constants, excluding the
    # population expectations, which are authority totals to verify rather than
    # tunable parameters.
    prohibited = set(PROHIBITED_HISTORICAL_VALUES.values())
    collisions = []
    for key, value in entries:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            continue
        if key.startswith("expected_"):
            continue
        if int(value) in prohibited and float(value) == int(value):
            collisions.append({"key": key, "value": value})
    if collisions:
        raise AssertionError("%s: %r" % (STOP_CONFIG_PROHIBITED_VALUE, collisions))
    return {"config": str(path).replace("\\", "/"),
            "keys_checked": len(entries),
            "production_adaptive_values": 0,
            "prohibited_historical_values": 0}


def derive(*, config_path: Path | str = DEFAULT_CONFIG,
           open_molecular: bool = True) -> dict[str, Any]:
    """Phase 0, Phase 1, then the gated production path."""
    report: dict[str, Any] = {"schema": "d1-parameter-derivation-v1"}
    report["config_validation"] = validate_config_has_no_production_values(config_path)

    try:
        report["population_audit"] = audit_full_fit_population(open_molecular=open_molecular)
    except FileNotFoundError as error:
        report["population_audit"] = {"terminal": STOP_AUTHORITY_UNREACHABLE,
                                      "detail": str(error)}
        report["terminal"] = STOP_AUTHORITY_UNREACHABLE
        return report

    readout = resolve_teacher_readout()
    report["teacher_readout"] = readout
    gate = teacher_gate_open(readout)
    report["teacher_gate_open"] = gate

    audit = report["population_audit"]
    provenance = D1Provenance(
        statistic_id="D1-P009:D",
        population_class=PRODUCTION_FULL_FIT,
        formula_version="d1-real-data-derivation-v1",
        input_roots={"population_audit_root": audit.get("audit_root_sha256", ""),
                     "teacher_readout_contract_hash": readout.get("readout_contract_hash", "")},
        donors=audit["observed"]["donors"],
        cells=audit["observed"]["cells"],
        operators=audit["observed"]["operators"],
        teacher_readout_contract_hash=readout.get("readout_contract_hash"),
        rng_namespace="d1-real-data-derivation-v1",
    )
    report["production_provenance_ready"] = provenance.is_production_eligible()

    # The production attempt. Proves the gate is real by actually trying.
    try:
        emit_production_parameter(parameter_id="D1-P009:D", value=None,
                                  provenance=provenance, teacher_gate_open=gate)
        report["production_parameter_emitted"] = True
        report["terminal"] = "D1_PRODUCTION_DERIVATION_COMPLETE"
    except PermissionError as error:
        report["production_parameter_emitted"] = False
        report["production_refusal"] = str(error)
        report["terminal"] = WAIT_HEALTHY_TEACHER

    report["derivable_now_without_teacher"] = {
        "D1-P002:donor_operator_cell_weights": "DERIVED_FROM_REAL_METADATA",
        "D1-P028:normalization_transform": "FROZEN_UPSTREAM_VERIFIED",
        "D1-P029:molecular_address_registry": "FROZEN_UPSTREAM_VERIFIED",
        "D1-P030:fit_population_counts": "DERIVED_FROM_REAL_METADATA",
    }
    report["teacher_dependent_parameters_withheld"] = [
        "D1-P003:weighted_teacher_mean_mu", "D1-P004:weighted_teacher_covariance_C",
        "D1-P005:observed_eigenspectrum", "D1-P006:null_eigenvalue_envelope",
        "D1-P007:D_PA", "D1-P008:donor_bootstrap_subspace_stability",
        "D1-P009:D", "D1-P010:entropy_effective_rank",
        "D1-P011:participation_effective_rank", "D1-P012:program_count_K",
        "D1-P013:component_degeneracy_blocks", "D1-P014:raw_cell_program_score",
        "D1-P015:within_donor_centered_score", "D1-P016:score_percentiles",
        "D1-P017:tail_numeric_cutpoints", "D1-P020:redundancy_similarity",
        "D1-P021:gene_program_effects", "D1-P022:gene_program_uncertainty",
        "D1-P023:program_measurement_support", "D1-P024:donor_recurrence",
        "D1-P025:source_operator_heterogeneity", "D1-P026:novelty_score",
    ]
    report["no_synthetic_or_auxiliary_production_value_written"] = True
    report["derivation_root_sha256"] = payload_root(
        {k: v for k, v in report.items() if k != "derivation_root_sha256"})
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=str, default=str(DEFAULT_CONFIG))
    parser.add_argument("--skip-molecular", action="store_true")
    parser.add_argument("--out", type=str, default=None)
    args = parser.parse_args()
    report = derive(config_path=args.config, open_molecular=not args.skip_molecular)
    text = json.dumps(report, indent=2, sort_keys=True, default=str)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        with io.open(args.out, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text + "\n")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
