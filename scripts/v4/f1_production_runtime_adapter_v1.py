#!/usr/bin/env python3
"""F1 production runtime adapter: the exact frozen model seam.

## Why this module exists

An independent review found that `TorchForwardEngine` called
`model_module.build_teacher_encoder(state)`, a factory the frozen
`src/sea_ad_jepa/v4/ipb_jepa.py` does not define, and then invoked the result as
`encoder(cell=..., mask=...)` while the frozen `IPBEncoder.forward` takes a
gene/expression/measurement/hidden-mask/view interface. The production seam was
therefore not executable as frozen, and no adapter was bound by the package or
the authorization.

This module is that adapter, built from the controlling authorities rather than
invented.

## Encoder construction, from the F0 reference

`scripts/v4/run_contextual_target_v1_f0.py::load_encoder` is the reviewed
construction, and it is reproduced exactly:

```python
loaded = torch.load(CHECKPOINT, map_location="cpu", weights_only=False)
encoder = IPBEncoder(vocabulary_size=41_238, width=160, heads=4, blocks=6,
                     gradient_checkpointing=False)
encoder.load_state_dict(loaded["online_encoder"], strict=True)
encoder.eval()
```

The state-dict key is `online_encoder`. Width 160 is architectural, not a
biological dimension.

## State construction, from the frozen query-local authority

All three routes call `construct_query_local_contextual_state` in
`src/sea_ad_jepa/v4/contextual_query_local.py`
(`6bd641cd22c160dfbec4e1ae4a0cc31929af436526487383f290397f4f55eeaa`). That
function is the authority: it validates the encoder source digest, the tokenizer
source digest, the physical-state authority digest, and binds
`model_state_sha256` to the supplied encoder. It also enforces its own firewall
on every row -- `reader_partition == "reader_fit"` and
`foundation_split == "foundation/train"` as two separate required fields, no
pathology, no external -- and rejects a mutated physical state.

Two readouts come from one forward, which is why 474,188 forwards suffice for
the six vectors the estimand needs:

- `h_query = gene_states[row, query_index]` is the DIRECT state;
- `contextual_state = layer_norm(h_query - mu_context)` is the CONTEXTUAL state.

## The three routes, from the matched-null causal contract

`outputs/contextual_teacher_target_v1_f1_prospective_repair_20260901/F1_MATCHED_NULL_CAUSAL_CONTRACT.md`
fixes them exactly:

- `T_true(c,q)`: recipient values, recipient `M_physical`, all lawful scalar
  context except q, teacher role. Reusable across all five evidence levels and
  the matched-null comparison, which is why there are 43,108 teacher forwards.
- `S_correct(c,q,e)`: recipient values, recipient `M_physical` and
  `U_evidence(e,q)`, student role.
- `S_null(c,q,e)`: normalized values from the frozen donor-distinct source row
  `P(c)`, but the RECIPIENT's `M_physical`, `U_evidence(e,q)`, q identity and
  operator/source.

That last point corrects a natural misreading. The substitution is of the
normalized expression values ONLY: "The permutation occurs before the encoder.
It changes normalized values, not M, U, q, operator or source." Substituting the
whole source row, including its physical state, would be a different and
unauthorised experiment. A nullized teacher is forbidden, and post-H
substitution is forbidden.

## Torch

Imported lazily inside the routes, so this module loads and its non-forward
logic is testable in environments without torch. The real forwards run under the
project's validated environment.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts" / "v4"))
sys.path.insert(0, str(REPO))

from f1_evidence_mask_authority_v1 import (  # noqa: E402
    EVIDENCE_LEVELS,
    MEASURED_SCALAR,
    build_row_evidence_masks,
)

# Frozen architecture constants, from the reviewed F0 encoder construction.
VOCABULARY_SIZE = 41_238
MODEL_WIDTH = 160          # architectural, not a biological dimension
MODEL_HEADS = 4
MODEL_BLOCKS = 6
CHECKPOINT_STATE_KEY = "online_encoder"

FROZEN_U0_CHECKPOINT_SHA256 = (
    "19fb0c25d9f7549c37de39285807d5b6a6e828ced94af63927e83fa3c5c6b7c4")
EXPECTED_ENCODER_SOURCE_SHA256 = (
    "732ea46f72384f29d503de1e0cc9d853315e2493cace054cced74849aa77485a")
EXPECTED_TOKENIZER_SOURCE_SHA256 = (
    "2a2ba7f4c2e52364cce471466ebacceefc2a1fccb29f4959860c885f281a89f4")
EXPECTED_PHYSICAL_STATE_AUTHORITY_SHA256 = (
    "852cb3ec6365cbd326dc6d5e8c8d885656f383b8f75b6e7a8d7aab72d9a42537")
QUERY_LOCAL_AUTHORITY_SHA256 = (
    "6bd641cd22c160dfbec4e1ae4a0cc31929af436526487383f290397f4f55eeaa")
MATCHED_NULL_MAP_SHA256 = (
    "aba31aea56190c32a00ac27a0356ea860761143f00f874db9c71c2080eb371a6")

TEACHER_ROLE = "teacher"
STUDENT_ROLE = "student"

CORRECT_ARM = "correct"
MATCHED_NULL_ARM = "matched_null"

STOP_ADAPTER_UNBOUND = "STOP_F1_ADAPTER_AUTHORITY_UNBOUND"
STOP_NULL_SOURCE = "STOP_F1_MATCHED_NULL_SOURCE_UNRESOLVED"
STOP_NULL_DONOR = "STOP_F1_MATCHED_NULL_SOURCE_NOT_DONOR_DISTINCT"
STOP_NULLIZED_TEACHER = "STOP_F1_NULLIZED_TEACHER_FORBIDDEN"
STOP_POST_H_SUBSTITUTION = "STOP_F1_POST_H_SUBSTITUTION_FORBIDDEN"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def physical_state_row_sha256(physical_state_row: Any) -> str:
    """Reproduce the query-local authority's `_tensor_sha256` exactly.

    The authority digests the dtype string, then the JSON shape list, then the
    C-order bytes, and it requires each provenance row to carry this digest of
    its own physical-state row. Reproducing it here is what lets the producer
    build provenance the frozen function will accept, rather than discovering
    the format by trial.
    """
    array = np.ascontiguousarray(np.asarray(physical_state_row, dtype=np.uint8))
    digest = hashlib.sha256()
    digest.update(str(array.dtype).encode("ascii"))
    digest.update(json.dumps(list(array.shape), separators=(",", ":")).encode("ascii"))
    digest.update(array.tobytes(order="C"))
    return digest.hexdigest()


def build_row_provenance(*, canonical_cell_id: str, query_address: int,
                         physical_state_row: Any, donor_id: str | None = None,
                         source: str | None = None,
                         operator_index: int | None = None) -> dict[str, Any]:
    """Provenance the frozen authority will accept, with its firewall fields.

    `reader_partition` and `foundation_split` are two SEPARATE required fields:
    the authority rejects a row whose partition is not `reader_fit` and,
    independently, one whose split is not `foundation/train`. They are not
    synonyms and neither substitutes for the other.
    """
    return {
        "canonical_cell_id": str(canonical_cell_id),
        "donor_id": None if donor_id is None else str(donor_id),
        "source": None if source is None else str(source),
        "operator_index": None if operator_index is None else int(operator_index),
        "reader_partition": "reader_fit",
        "foundation_split": "foundation/train",
        "pathology": False,
        "external": False,
        "physical_state_row_sha256": physical_state_row_sha256(physical_state_row),
        "query_address": int(query_address),
    }


def adapter_source_sha256() -> str:
    """This adapter's own digest, so the authorization can bind it."""
    return sha256_file(Path(__file__))


def load_matched_null_map(path: Path) -> dict[str, dict[str, str]]:
    """Recipient cell -> frozen donor-distinct source row, from the frozen map.

    The map is cell level: 2,781 recipient cells, matching `recipient_cells` in
    the frozen geometry, each with exactly one source row.
    """
    import csv

    digest = sha256_file(path)
    if digest != MATCHED_NULL_MAP_SHA256:
        raise AssertionError("%s: matched-null map digest %s expected %s"
                            % (STOP_ADAPTER_UNBOUND, digest, MATCHED_NULL_MAP_SHA256))
    with Path(path).open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    required = ("recipient_canonical_cell_id", "recipient_canonical_donor_id",
                "source_row_locator", "source_canonical_cell_id",
                "source_canonical_donor_id", "operator_index")
    absent = [c for c in required if rows and c not in rows[0]]
    if absent:
        raise AssertionError("%s: matched-null map schema absent=%r"
                            % (STOP_ADAPTER_UNBOUND, absent))
    mapping: dict[str, dict[str, str]] = {}
    for row in rows:
        recipient = str(row["recipient_canonical_cell_id"])
        if str(row["recipient_canonical_donor_id"]) == str(row["source_canonical_donor_id"]):
            raise AssertionError("%s: recipient %s maps to a same-donor source"
                                % (STOP_NULL_DONOR, recipient))
        mapping[recipient] = {
            "source_row_locator": str(row["source_row_locator"]),
            "source_canonical_cell_id": str(row["source_canonical_cell_id"]),
            "source_canonical_donor_id": str(row["source_canonical_donor_id"]),
            "recipient_canonical_donor_id": str(row["recipient_canonical_donor_id"]),
            "operator_index": str(row["operator_index"]),
        }
    return mapping


def resolve_matched_null_source(recipient_cell_id: str,
                                mapping: Mapping[str, Mapping[str, str]]) -> dict[str, str]:
    """The frozen donor-distinct source for one recipient. Never improvised."""
    entry = mapping.get(str(recipient_cell_id))
    if entry is None:
        raise KeyError("%s: recipient %r is not in the frozen matched-null map"
                       % (STOP_NULL_SOURCE, recipient_cell_id))
    return dict(entry)


def load_u0_encoder(checkpoint_path: Path, *, device: str = "cpu") -> Any:
    """Build the frozen encoder and load the exact u0 state dict.

    Reproduces the reviewed F0 construction exactly, including the
    `online_encoder` state-dict key and `strict=True`. The checkpoint digest is
    verified before the state is trusted. u0 is a mechanics fixture, not a
    qualified biological teacher.
    """
    import torch  # lazy: absent in source-only environments

    from sea_ad_jepa.v4.ipb_jepa import IPBEncoder

    digest = sha256_file(checkpoint_path)
    if digest != FROZEN_U0_CHECKPOINT_SHA256:
        raise AssertionError("%s: checkpoint digest %s expected %s"
                            % (STOP_ADAPTER_UNBOUND, digest, FROZEN_U0_CHECKPOINT_SHA256))
    loaded = torch.load(str(checkpoint_path), map_location="cpu", weights_only=False)
    if CHECKPOINT_STATE_KEY not in loaded:
        raise AssertionError("%s: checkpoint has no %r state"
                            % (STOP_ADAPTER_UNBOUND, CHECKPOINT_STATE_KEY))
    encoder = IPBEncoder(vocabulary_size=VOCABULARY_SIZE, width=MODEL_WIDTH,
                         heads=MODEL_HEADS, blocks=MODEL_BLOCKS,
                         gradient_checkpointing=False)
    encoder.load_state_dict(loaded[CHECKPOINT_STATE_KEY], strict=True)
    encoder.eval().to(device)
    return encoder


def module_state_sha256(encoder: Any) -> str:
    """Digest of the loaded parameters, as the query-local authority computes it."""
    import torch  # noqa: F401

    # The authority iterates `state_dict().items()` in INSERTION order, which is
    # module registration order. Sorting the names produces a different digest
    # and the authority then refuses to bind the encoder, so the order is copied
    # rather than tidied.
    digest = hashlib.sha256()
    for name, value in encoder.state_dict().items():
        digest.update(name.encode("utf-8"))
        digest.update(value.detach().contiguous().cpu().numpy().tobytes())
    return digest.hexdigest()


class F1ProductionAdapter:
    """The authorized runtime seam. Three routes, one frozen constructor.

    Every route calls `construct_query_local_contextual_state`, so the frozen
    authority performs the forward, the provenance firewall, the digest binding
    and the state construction. This adapter's job is only to assemble the exact
    inputs each route requires.
    """

    def __init__(self, *, encoder: Any, matched_null_map: Mapping[str, Mapping[str, str]],
                 physical_state_authority_sha256: str = EXPECTED_PHYSICAL_STATE_AUTHORITY_SHA256,
                 encoder_source_sha256: str = EXPECTED_ENCODER_SOURCE_SHA256,
                 tokenizer_source_sha256: str = EXPECTED_TOKENIZER_SOURCE_SHA256) -> None:
        self.encoder = encoder
        self.matched_null_map = dict(matched_null_map)
        self.encoder_source_sha256 = str(encoder_source_sha256)
        self.tokenizer_source_sha256 = str(tokenizer_source_sha256)
        self.physical_state_authority_sha256 = str(physical_state_authority_sha256)
        self._model_state_sha256: str | None = None

    def model_state_sha256(self) -> str:
        if self._model_state_sha256 is None:
            self._model_state_sha256 = module_state_sha256(self.encoder)
        return self._model_state_sha256

    # ---------------------------------------------------------------- helpers
    def _construct(self, *, normalized_expression: Any, physical_state: Any,
                   evidence_visible: Any, query_index: int,
                   row_provenance: Sequence[Mapping[str, object]], role: str) -> Any:
        import torch

        from sea_ad_jepa.v4.contextual_query_local import (
            construct_query_local_contextual_state,
        )

        width = int(np.asarray(physical_state).size)
        gene_ids = torch.arange(width, dtype=torch.long).unsqueeze(0)
        return construct_query_local_contextual_state(
            encoder=self.encoder,
            gene_ids=gene_ids,
            normalized_expression=torch.as_tensor(
                np.asarray(normalized_expression, dtype=np.float32)).reshape(1, width),
            physical_state=torch.as_tensor(
                np.asarray(physical_state, dtype=np.uint8)).reshape(1, width),
            evidence_visible=torch.as_tensor(
                np.asarray(evidence_visible, dtype=bool)).reshape(1, width),
            query_index=torch.as_tensor([int(query_index)], dtype=torch.long),
            row_provenance=list(row_provenance),
            encoder_source_sha256=self.encoder_source_sha256,
            tokenizer_source_sha256=self.tokenizer_source_sha256,
            model_state_sha256=self.model_state_sha256(),
            physical_state_authority_sha256=self.physical_state_authority_sha256,
            role=role)

    @staticmethod
    def _readouts(result: Any) -> dict[str, Any]:
        """Both readouts from one forward: contextual and direct."""
        contextual = np.asarray(result.contextual_state.detach().cpu().numpy()).reshape(-1)
        direct = np.asarray(result.h_query.detach().cpu().numpy()).reshape(-1)
        return {"contextual": contextual, "direct": direct,
                "evidence_sha256": result.evidence_sha256,
                "hidden_mask_sha256": result.hidden_mask_sha256,
                "physical_state_sha256": result.physical_state_sha256,
                "context_state_sha256": tuple(result.context_state_sha256),
                "context_counts": [int(c) for c in result.context_counts.tolist()],
                "model_state_sha256": result.model_state_sha256,
                "role": result.role}

    # ----------------------------------------------------------------- routes
    def teacher_state(self, *, row: Mapping[str, Any]) -> dict[str, Any]:
        """`T_true(c,q)`: recipient values and state, ALL lawful context except q.

        Evidence-invariant by construction, so it is computed once per (cell,q)
        and reused across all five evidence levels and both arms.
        """
        masks = build_row_evidence_masks(
            row["physical_state"], int(row["query_index"]),
            row_locator=str(row["row_locator"]),
            query_address=int(row["query_address"]))
        result = self._construct(
            normalized_expression=row["normalized_expression"],
            physical_state=row["physical_state"],
            evidence_visible=masks["teacher_rich_mask"],
            query_index=int(row["query_index"]),
            row_provenance=[row["provenance"]], role=TEACHER_ROLE)
        return dict(self._readouts(result), arm=None, evidence_level=None,
                    teacher_rich=True)

    def correct_student_state(self, *, row: Mapping[str, Any],
                              evidence_level: int) -> dict[str, Any]:
        """`S_correct(c,q,e)`: recipient values, recipient state and U(e,q)."""
        if int(evidence_level) not in EVIDENCE_LEVELS:
            raise ValueError("STOP_F1_EVIDENCE_LEVEL: %r" % (evidence_level,))
        masks = build_row_evidence_masks(
            row["physical_state"], int(row["query_index"]),
            row_locator=str(row["row_locator"]),
            query_address=int(row["query_address"]))
        result = self._construct(
            normalized_expression=row["normalized_expression"],
            physical_state=row["physical_state"],
            evidence_visible=masks["masks"][int(evidence_level)],
            query_index=int(row["query_index"]),
            row_provenance=[row["provenance"]], role=STUDENT_ROLE)
        return dict(self._readouts(result), arm=CORRECT_ARM,
                    evidence_level=int(evidence_level))

    def matched_null_student_state(self, *, row: Mapping[str, Any],
                                   evidence_level: int,
                                   source_normalized_expression: Any,
                                   source_row: Mapping[str, Any]) -> dict[str, Any]:
        """`S_null(c,q,e)`: SOURCE normalized values, RECIPIENT state/U/q/operator.

        Only the normalized expression is substituted. The recipient's
        `M_physical`, `U_evidence(e,q)`, query identity and operator/source are
        retained, because the contract states the permutation occurs before the
        encoder and changes normalized values, not M, U, q, operator or source.
        Substituting the source's physical state as well would be a different
        and unauthorised experiment.
        """
        if int(evidence_level) not in EVIDENCE_LEVELS:
            raise ValueError("STOP_F1_EVIDENCE_LEVEL: %r" % (evidence_level,))
        expected = resolve_matched_null_source(str(row["provenance"]["canonical_cell_id"]),
                                               self.matched_null_map)
        if str(source_row.get("canonical_cell_id")) != expected["source_canonical_cell_id"]:
            raise AssertionError(
                "%s: supplied source %r is not the frozen source %r for recipient %r"
                % (STOP_NULL_SOURCE, source_row.get("canonical_cell_id"),
                   expected["source_canonical_cell_id"],
                   row["provenance"]["canonical_cell_id"]))
        if str(source_row.get("canonical_donor_id")) == str(
                expected["recipient_canonical_donor_id"]):
            raise AssertionError(STOP_NULL_DONOR)

        masks = build_row_evidence_masks(
            row["physical_state"], int(row["query_index"]),
            row_locator=str(row["row_locator"]),
            query_address=int(row["query_address"]))
        result = self._construct(
            normalized_expression=source_normalized_expression,   # the ONLY substitution
            physical_state=row["physical_state"],                 # recipient M
            evidence_visible=masks["masks"][int(evidence_level)],  # recipient U(e,q)
            query_index=int(row["query_index"]),                  # recipient q
            row_provenance=[row["provenance"]], role=STUDENT_ROLE)
        return dict(self._readouts(result), arm=MATCHED_NULL_ARM,
                    evidence_level=int(evidence_level),
                    matched_null_source_cell_id=expected["source_canonical_cell_id"],
                    matched_null_source_donor_id=expected["source_canonical_donor_id"])


def assert_no_nullized_teacher(records: Sequence[Mapping[str, Any]]) -> None:
    """A nullized teacher is forbidden by the causal contract."""
    for record in records:
        if str(record.get("role")) == TEACHER_ROLE and record.get("arm") is not None:
            raise AssertionError(STOP_NULLIZED_TEACHER)


__all__ = [name for name in dir() if not name.startswith("_")]
