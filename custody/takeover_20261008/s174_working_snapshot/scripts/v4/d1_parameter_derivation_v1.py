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
    STOP_NOT_PRODUCTION_POPULATION,
    STOP_TEACHER_GATE_CLOSED,
    D1Provenance,
    derive_D_end_to_end,
    emit_production_parameter,
    payload_root,
)
from d1_full_fit_population_audit_v1 import (  # noqa: E402
    CELL_METADATA_REL,
    MANDATORY_AUTHORITIES,
    STOP_AUTHORITY_UNREACHABLE,
    audit_full_fit_population,
    read_fit_donor_operator_counts,
    read_frozen_reader_roster,
    resolve_authority,
)
from d1_teacher_state_stream_v1 import (  # noqa: E402
    STOP_READOUT_UNRESOLVED,
    WAIT_HEALTHY_TEACHER,
    build_production_strata_source,
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
STOP_CONFIG_UNPARSED = "STOP_D1_CONFIG_NOT_FULLY_PARSED"


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
            # A key with no scalar may be either a mapping or a list; decide lazily.
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

    # A validator that parsed almost nothing would report zero violations for
    # the wrong reason. The fallback parser exists so the config can be checked
    # without PyYAML, and a fallback that mis-parsed would fail open exactly
    # here, so the parse itself must be shown to have succeeded.
    keys = {key for key, _ in entries}
    required_sections = {"population", "numerics", "monte_carlo", "tail_views",
                         "ranking", "gates", "schemas", "degeneracy"}
    absent = sorted(required_sections - keys)
    if absent:
        raise AssertionError(
            "%s: config parse produced no %r section; refusing to report a clean "
            "validation from an incomplete parse" % (STOP_CONFIG_UNPARSED, absent))
    if len(entries) < 30:
        raise AssertionError(
            "%s: config parse yielded only %d keys, which is too few to have "
            "parsed this file" % (STOP_CONFIG_UNPARSED, len(entries)))
    return {"config": str(path).replace("\\", "/"),
            "keys_checked": len(entries),
            "sections_present": sorted(required_sections),
            "production_adaptive_values": 0,
            "prohibited_historical_values": 0}


def build_production_provenance(*, audit: Mapping[str, Any],
                                readout: Mapping[str, Any]) -> D1Provenance:
    """Assemble the mandatory provenance from the audit and readout artifacts.

    Every root here is taken from an artifact rather than asserted. A missing
    one leaves the provenance incomplete, which is the intended outcome: the
    teacher checkpoint root is `None` today because no qualified healthy teacher
    exists, and that alone makes the provenance ineligible.
    """
    authority = audit.get("authority_sha256", {})
    qualified = readout.get("qualified_healthy_checkpoints") or []
    teacher_root = str(qualified[0]["sha256"]) if qualified else None
    return D1Provenance(
        statistic_id="D1-P009:D",
        population_class=PRODUCTION_FULL_FIT,
        formula_version="d1-real-data-derivation-v1",
        input_roots={
            "population_audit_root": audit.get("audit_root_sha256", ""),
            "cell_metadata_authority_root": authority.get("cell_metadata_sqlite", ""),
            "loader_manifest_root": authority.get("production_loader_manifest", ""),
            "split_registry_root": authority.get("foundation_split_registry", ""),
        },
        donors=audit["observed"]["donors"],
        cells=audit["observed"]["cells"],
        operators=audit["observed"]["operators"],
        teacher_checkpoint_root=teacher_root,
        teacher_readout_contract_hash=readout.get("readout_contract_hash"),
        firewall_evidence={
            "protected_rows_delivered": audit["firewall"]["protected_rows_delivered"],
            "lawful_partition": audit["firewall"]["lawful_partition"],
            "donor_roster_verified": audit["firewall"]["donor_roster_verified"],
        },
        rng_namespace="d1-real-data-derivation-v1",
    )


def run_production_D_derivation(*, audit: Mapping[str, Any], readout: Mapping[str, Any],
                                config_path: Path | str) -> dict[str, Any]:
    """Actually run the full-population D derivation.

    Only reachable with the teacher gate open. It builds the lawful streaming
    source over the audited strata and calls the end-to-end engine, so the
    weighted moments, the donor/operator-preserving null, the donor-block
    bootstrap and the fail-closed D rule all execute on real data. An earlier
    revision of this driver called none of those.
    """
    config = _load_yaml(Path(config_path))
    monte_carlo = config.get("monte_carlo", {})
    dimension = int(readout.get("readout_dimension") or 0)
    if dimension <= 0:
        raise AssertionError(
            "STOP_D1_READOUT_DIMENSION_UNRESOLVED: the readout contract must fix the "
            "exact cell-level state dimension before D can be derived")
    counts = load_lawful_donor_operator_counts()
    # Cross-check the freshly loaded strata against the audited population, so a
    # derivation cannot silently run over a different set of rows than the one
    # Phase 0 proved.
    observed = audit["observed"]
    if sum(counts.values()) != int(observed["cells"]):
        raise AssertionError(
            "STOP_D1_DERIVATION_POPULATION_DRIFT: loaded %d cells but the audit "
            "proved %d" % (sum(counts.values()), int(observed["cells"])))
    if "donor_operator_pairs" in observed and len(counts) != int(observed["donor_operator_pairs"]):
        raise AssertionError(
            "STOP_D1_DERIVATION_POPULATION_DRIFT: loaded %d donor x operator pairs "
            "but the audit proved %d" % (len(counts), int(observed["donor_operator_pairs"])))
    source = build_production_strata_source(
        donor_operator_counts=counts,
        readout=resolve_production_readout(readout),
        dimension=dimension, report=readout)
    return derive_D_end_to_end(
        source, dimension,
        rng_namespace=str(monte_carlo.get("rng_namespace", "d1-real-data-derivation-v1")),
        confidence_level=float(monte_carlo.get("confidence_level", 0.95)),
        minimum_replicates=int(monte_carlo.get("minimum_replicates", 64)),
        maximum_replicates=int(monte_carlo.get("maximum_replicates", 8192)),
        precision_target_half_width=float(
            monte_carlo.get("precision_target_half_width", 0.01)),
        doubling_factor=int(monte_carlo.get("doubling_factor", 2)))


def resolve_production_readout(readout: Mapping[str, Any]) -> Any:
    """Return the authorized readout callable, or refuse.

    There is no authorized cell-level readout today, so this refuses. It is a
    single named seam rather than a scattered condition: when a prospective
    representation contract selects one candidate and reconciles its
    dtype/autocast with the frozen F1 accepted mechanics, this is the one
    function that gains an implementation.
    """
    raise PermissionError(
        "%s: no authorized cell-level teacher readout exists; conflicts=%r"
        % (STOP_READOUT_UNRESOLVED, list(readout.get("conflicts", []))))


def load_lawful_donor_operator_counts() -> dict[tuple[str, int], int]:
    """Donor x operator lawful cell counts, from the audited authority."""
    split = resolve_authority(MANDATORY_AUTHORITIES["reader_donor_split"][0])
    roster = read_frozen_reader_roster(split)
    sqlite_path = resolve_authority(CELL_METADATA_REL)
    return read_fit_donor_operator_counts(sqlite_path, roster["fit_roster"])["counts"]


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
    provenance = build_production_provenance(audit=audit, readout=readout)
    missing = provenance.missing_production_provenance()
    report["production_provenance_ready"] = not missing
    report["production_provenance_missing"] = missing

    # The production path. It either runs the real derivation or it does not run
    # at all; it never probes the gate with a placeholder.
    #
    # An earlier revision called emit_production_parameter(value=None) purely to
    # test the gate. Today's closed gate hid the consequence: had the gate
    # opened, that call would have emitted D=None and reported
    # D1_PRODUCTION_DERIVATION_COMPLETE without any estimator having run. The
    # gate is now checked before the derivation is attempted, the derivation
    # produces the value, and emission happens only with a real value in hand.
    if not gate:
        report["production_parameter_emitted"] = False
        report["production_refusal"] = (
            "%s: teacher gate closed; the production derivation was not attempted "
            "and no placeholder was emitted" % STOP_TEACHER_GATE_CLOSED)
        report["terminal"] = WAIT_HEALTHY_TEACHER
        report["production_derivation_attempted"] = False
    elif missing:
        report["production_parameter_emitted"] = False
        report["production_refusal"] = (
            "%s: mandatory provenance incomplete %r" % (STOP_NOT_PRODUCTION_POPULATION, missing))
        report["terminal"] = STOP_NOT_PRODUCTION_POPULATION
        report["production_derivation_attempted"] = False
    else:
        report["production_derivation_attempted"] = True
        derivation = run_production_D_derivation(
            audit=audit, readout=readout, config_path=config_path)
        report["derivation"] = derivation
        emitted = emit_production_parameter(
            parameter_id="D1-P009:D", value=derivation["D"], provenance=provenance,
            teacher_gate_open=gate, diagnostics=derivation)
        report["production_parameter"] = emitted
        report["production_parameter_emitted"] = True
        report["terminal"] = "D1_PRODUCTION_DERIVATION_COMPLETE"

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
