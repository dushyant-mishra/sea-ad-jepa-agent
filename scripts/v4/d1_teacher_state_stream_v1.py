#!/usr/bin/env python3
"""D1 Phase 1: resolve the authorized cell-level teacher readout seam.

This module does not invent a cell-level representation. It traces what the
model source actually exposes, enumerates every candidate cell-level readout,
checks whether any prospective authority selects one, and reports the result.
When no unique authorized readout exists it emits
`STOP_D1_TEACHER_READOUT_UNRESOLVED` and refuses to stream production states.

What the trace found on this branch, and why the terminal is a STOP rather than
a pick:

1. `IPBEncoder.forward` returns `EncoderOutput(gene_states, cell_state,
   minimum_denominator)` where `cell_state = final_norm(tokens)[:, 0]` is a
   dedicated prepended cell token, width 160, and `gene_states = tokens[:, 1:]`.
   Index 0 is the architectural definition of the cell state here, not an
   arbitrary slot-0 selection over interchangeable slots.
2. The historical T1 teacher export nevertheless writes *two* cell-level
   readouts side by side: that `cell_state`, shape (B, 160), and a
   program-pooled `h = einsum("kg,bgd->bkd", weights, gene_states)` of shape
   (B, K, 160). The second is a genuine multi-slot latent readout, and
   collapsing it would require exactly the averaging or pooling rule the
   authority forbids inventing.
3. No prospective representation or readout contract exists under `docs/agent/`
   naming a D1 cell-level teacher state, so nothing selects between them.
4. The historical export runs its forward under
   `torch.autocast("cuda", dtype=torch.float16)`, while the frozen F1
   production-mechanics acceptance contract fixes real forwards at float32 with
   autocast off. Adopting the historical seam verbatim would contradict that
   frozen contract.

Any of 2, 3 or 4 alone is enough to withhold a production teacher-dependent
value. Together they are an authority ambiguity, which is reported here as an
exact file/shape/hash conflict rather than resolved heuristically.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import io
import json
import os
import sys
from pathlib import Path
from typing import Any, Iterator, Mapping, Sequence

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts" / "v4"))

from d1_real_data_derivation_core_v1 import (  # noqa: E402
    MECHANICS_ONLY,
    PRODUCTION_FULL_FIT,
    payload_root,
)

AUTHORITY_ROOT_ENV = "D1_AUTHORITY_ROOT"
_EXPLICIT = os.environ.get(AUTHORITY_ROOT_ENV)
AUTHORITY_ROOTS: tuple[Path, ...] = ((Path(_EXPLICIT),) if _EXPLICIT
                                     else (Path("/mnt/d/Jepa project"), Path("D:/Jepa project"), REPO))

MODEL_SOURCE_REL = "src/sea_ad_jepa/v4/ipb_jepa.py"
HISTORICAL_TEACHER_EXPORT_REL = "scripts/v4/stage81a3_prod41k_teacher_t1.py"
CHECKPOINT_MANIFEST_REL = ("exports/foundation_calibration_bundle_20260824/"
                           "checkpoints/checkpoint_manifest.json")

STOP_READOUT_UNRESOLVED = "STOP_D1_TEACHER_READOUT_UNRESOLVED"
WAIT_HEALTHY_TEACHER = "WAIT_HEALTHY_TRAINED_TEACHER"

# u0000 is untrained; u0010-u0205 are TRAINING_MECHANICS_DEFECT_INHERITED.
UNTRAINED_UPDATES = (0,)
DEFECT_INHERITED_UPDATES = (10, 25, 50, 100, 200, 205)

# The frozen F1 production-mechanics acceptance requires float32 with autocast
# off for real forwards.
F1_ACCEPTED_FORWARD_DTYPE = "float32"
F1_ACCEPTED_AUTOCAST = False


def _resolve(relative: str) -> Path | None:
    for root in AUTHORITY_ROOTS:
        candidate = root / relative
        if candidate.is_file():
            return candidate
    return None


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def trace_encoder_output_fields(model_source: Path) -> dict[str, Any]:
    """Read the encoder's declared output fields and cell-state expression by AST."""
    tree = ast.parse(model_source.read_text(encoding="utf-8"))
    fields: list[str] = []
    width_default: int | None = None
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "EncoderOutput":
            for item in node.body:
                if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                    fields.append(item.target.id)
        if isinstance(node, ast.ClassDef) and node.name == "IPBEncoder":
            for item in ast.walk(node):
                if (isinstance(item, ast.arg) and item.arg == "width"
                        and isinstance(getattr(item, "annotation", None), ast.Name)):
                    pass
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name == "__init__":
                    for default in item.args.defaults + item.args.kw_defaults:
                        if isinstance(default, ast.Constant) and default.value == 160:
                            width_default = 160
    return {"encoder_output_fields": fields, "encoder_width_default": width_default}


def resolve_teacher_readout() -> dict[str, Any]:
    """Enumerate candidate cell-level readouts and decide whether one is authorized."""
    model_source = _resolve(MODEL_SOURCE_REL)
    export_source = _resolve(HISTORICAL_TEACHER_EXPORT_REL)
    manifest_path = _resolve(CHECKPOINT_MANIFEST_REL)

    report: dict[str, Any] = {
        "schema": "d1-teacher-readout-contract-v1",
        "model_source": {"path": MODEL_SOURCE_REL},
        "candidates": [],
        "frozen_representation_contract": None,
        "conflicts": [],
    }

    if model_source is None:
        report["terminal"] = STOP_READOUT_UNRESOLVED
        report["conflicts"].append("model source %s not reachable" % MODEL_SOURCE_REL)
        return report

    report["model_source"]["sha256"] = _sha256(model_source)
    report["model_source"].update(trace_encoder_output_fields(model_source))

    # Candidate 1: the dedicated cell token.
    report["candidates"].append({
        "candidate_id": "encoder_cell_state",
        "source_file": MODEL_SOURCE_REL,
        "source_function": "IPBEncoder.forward",
        "expression": "final_norm(tokens)[:, 0]  # dedicated prepended cell token",
        "output_shape": ["B", 160],
        "readout_operation": "select the dedicated cell token; no pooling or averaging",
        "multi_slot": False,
        "note": ("index 0 is the architectural cell token, not an arbitrary slot "
                 "chosen among interchangeable slots; gene_states is tokens[:, 1:]"),
    })

    # Candidate 2: the program-pooled H readout used by the historical export.
    if export_source is not None:
        text = export_source.read_text(encoding="utf-8")
        pooled = 'torch.einsum("kg,bgd->bkd", weight_tensor, output.gene_states.float())' in text
        autocast_fp16 = 'torch.autocast("cuda", dtype=torch.float16)' in text
        if pooled:
            report["candidates"].append({
                "candidate_id": "program_pooled_H",
                "source_file": HISTORICAL_TEACHER_EXPORT_REL,
                "source_function": "evaluation feature export",
                "expression": 'einsum("kg,bgd->bkd", weight_tensor, gene_states)',
                "output_shape": ["B", "K", 160],
                "readout_operation": "weighted pooling of gene states into K program slots",
                "multi_slot": True,
                "note": ("a genuine multi-slot latent readout; collapsing it to one "
                         "cell-level vector would require an averaging/pooling rule "
                         "that no prospective authority defines"),
            })
            report["conflicts"].append(
                "two cell-level readouts are written side by side by %s: "
                "encoder_cell_state (B,160) and program_pooled_H (B,K,160); no "
                "authority selects between them" % HISTORICAL_TEACHER_EXPORT_REL)
        report["historical_export"] = {
            "path": HISTORICAL_TEACHER_EXPORT_REL,
            "sha256": _sha256(export_source),
            "forward_autocast_float16": autocast_fp16,
        }
        if autocast_fp16:
            report["conflicts"].append(
                "the historical teacher export runs its forward under "
                'torch.autocast("cuda", dtype=torch.float16), while the frozen F1 '
                "production-mechanics acceptance contract fixes real forwards at "
                "dtype=%s with autocast=%s; adopting the historical seam verbatim "
                "would contradict that frozen contract"
                % (F1_ACCEPTED_FORWARD_DTYPE, F1_ACCEPTED_AUTOCAST))

    # Is any prospective representation/readout contract present?
    contract_hits: list[str] = []
    for root in AUTHORITY_ROOTS:
        agent_docs = root / "docs" / "agent"
        if agent_docs.is_dir():
            for entry in sorted(agent_docs.glob("*.md")):
                name = entry.name.upper()
                if "READOUT" in name or "REPRESENTATION" in name:
                    contract_hits.append(str(entry.relative_to(root)).replace("\\", "/"))
            break
    report["frozen_representation_contract"] = contract_hits or None
    if not contract_hits:
        report["conflicts"].append(
            "no prospective representation or readout contract exists under "
            "docs/agent/ naming a D1 cell-level teacher state")

    # Checkpoint availability.
    checkpoints: list[dict[str, Any]] = []
    healthy = []
    if manifest_path is not None:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for entry in manifest.get("checkpoints", []):
            update = int(entry.get("update", -1))
            if update in UNTRAINED_UPDATES:
                status = "UNTRAINED_U0"
            elif update in DEFECT_INHERITED_UPDATES:
                status = "TRAINING_MECHANICS_DEFECT_INHERITED"
            else:
                status = "UNCLASSIFIED"
                healthy.append(update)
            checkpoints.append({"update": update, "sha256": entry.get("sha256"),
                                "status": status})
        report["checkpoint_manifest"] = {"path": CHECKPOINT_MANIFEST_REL,
                                         "sha256": _sha256(manifest_path)}
    report["checkpoints"] = checkpoints
    report["healthy_trained_teacher_available"] = bool(healthy)
    if not healthy:
        report["conflicts"].append(
            "no mechanically healthy trained teacher checkpoint is available: every "
            "manifested checkpoint is either untrained u0000 or "
            "TRAINING_MECHANICS_DEFECT_INHERITED (u0010-u0205)")

    report["unique_authorized_cell_level_state"] = False
    report["terminal"] = STOP_READOUT_UNRESOLVED
    report["teacher_gate_open"] = False
    report["teacher_gate_terminal"] = WAIT_HEALTHY_TEACHER
    report["required_to_open"] = [
        "a prospective D1 representation contract selecting exactly one cell-level "
        "readout and its exact operation",
        "reconciliation of the readout dtype/autocast with the frozen F1 accepted "
        "mechanics (float32, autocast off)",
        "a mechanically healthy trained teacher checkpoint, byte/root-bound",
    ]
    report["readout_contract_hash"] = payload_root(
        {k: v for k, v in report.items() if k != "readout_contract_hash"})
    return report


def teacher_gate_open(report: Mapping[str, Any] | None = None) -> bool:
    """The teacher gate. Closed unless a unique readout AND a healthy teacher exist."""
    resolved = report if report is not None else resolve_teacher_readout()
    return bool(resolved.get("unique_authorized_cell_level_state")
                and resolved.get("healthy_trained_teacher_available"))


def iter_teacher_states(*, population_class: str, chunk_size: int = 8192,
                        report: Mapping[str, Any] | None = None) -> Iterator[Any]:
    """Stream cell-level teacher states. Refuses while the gate is closed.

    Kept as the single seam so that when a healthy teacher and a representation
    contract exist, exactly one function needs to change and every estimator
    downstream inherits the gate.
    """
    resolved = report if report is not None else resolve_teacher_readout()
    if population_class == PRODUCTION_FULL_FIT and not teacher_gate_open(resolved):
        raise PermissionError(
            "%s / %s: %s" % (STOP_READOUT_UNRESOLVED, WAIT_HEALTHY_TEACHER,
                             "; ".join(str(c) for c in resolved.get("conflicts", []))))
    if population_class == MECHANICS_ONLY:
        raise NotImplementedError(
            "mechanics fixtures supply their own arrays; this streamer exists only "
            "for the production seam and must not fabricate synthetic states")
    raise PermissionError("%s: unsupported population_class %r"
                          % (STOP_READOUT_UNRESOLVED, population_class))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=str, default=None)
    args = parser.parse_args()
    report = resolve_teacher_readout()
    text = json.dumps(report, indent=2, sort_keys=True, default=str)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        with io.open(args.out, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text + "\n")
    print(text)
    return 0 if report["terminal"] == STOP_READOUT_UNRESOLVED else 1


if __name__ == "__main__":
    raise SystemExit(main())
