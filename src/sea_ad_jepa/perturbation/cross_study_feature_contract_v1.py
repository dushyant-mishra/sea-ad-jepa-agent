"""Fail-closed cross-study feature identity and assay observation contract V1.

SCHEMA-ONLY: Mapping tables must be obtained from a separately authenticated,
frozen annotation release. This module cannot authorize a producer-curated
mapping, validate the biological truth of a gene alias, or claim that a value
was measured. It never silently infers synonyms, cis targets, orthology, or
intervention equivalence.

In particular: source feature present but all-zero = ASSAYED_UNDETECTED;
source feature absent = STRUCTURALLY_UNMEASURED. An all-zero assayed gene may
be excluded by a separate explicit detectability filter, never mislabeled
as absent from the assay.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
import re
from typing import Mapping, Sequence

import numpy as np


class FeatureContractError(ValueError):
    pass


class ObservationStatus(str, Enum):
    STRUCTURALLY_UNMEASURED = "STRUCTURALLY_UNMEASURED"
    ASSAYED_UNDETECTED = "ASSAYED_UNDETECTED"
    ASSAYED_DETECTED = "ASSAYED_DETECTED"


ENSG = re.compile(r"^ENSG[0-9]{11}$")
ENSG_VERSIONED = re.compile(r"^(ENSG[0-9]{11})\.([1-9][0-9]*)$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
VALID_NAMESPACES = frozenset({"HGNC_SYMBOL", "ENSEMBL_GENE_ID"})
VALID_STATUS = frozenset({"PRIMARY_ID", "REVIEWED_ALIAS", "VERSIONED_ID"})


def sha_json(obj: object) -> str:
    return hashlib.sha256(json.dumps(
        obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class FeatureMapEntry:
    namespace: str
    source_id: str
    canonical_ensembl: str
    annotation_evidence_id: str
    mapping_status: str

    def validate(self) -> None:
        if self.namespace not in VALID_NAMESPACES:
            raise FeatureContractError("unknown source feature namespace")
        if not self.source_id or self.source_id != self.source_id.strip():
            raise FeatureContractError("empty or untrimmed source identity")
        if self.mapping_status not in VALID_STATUS:
            raise FeatureContractError("mapping-status authority missing")
        if not self.annotation_evidence_id.strip():
            raise FeatureContractError("missing annotation evidence")
        if not ENSG.fullmatch(self.canonical_ensembl):
            raise FeatureContractError("canonical Ensembl ID must be unversioned ENSG")
        if self.namespace == "ENSEMBL_GENE_ID":
            m = ENSG_VERSIONED.fullmatch(self.source_id)
            if m is not None:
                if m.group(1) != self.canonical_ensembl or self.mapping_status != "VERSIONED_ID":
                    raise FeatureContractError("versioned Ensembl identity has wrong base or status")
            elif (not ENSG.fullmatch(self.source_id)
                  or self.source_id != self.canonical_ensembl
                  or self.mapping_status != "PRIMARY_ID"):
                raise FeatureContractError("Ensembl identity does not match frozen canonical ID")


@dataclass(frozen=True)
class FrozenAnnotation:
    release: str
    annotation_file_sha256: str
    entries: tuple[FeatureMapEntry, ...]
    contract_sha256: str

    def body(self) -> dict:
        return {
            "schema": "CROSS_STUDY_FEATURE_MAP_V1",
            "release": self.release,
            "annotation_file_sha256": self.annotation_file_sha256,
            "entries": [
                {
                    "namespace": e.namespace, "source_id": e.source_id,
                    "canonical_ensembl": e.canonical_ensembl,
                    "annotation_evidence_id": e.annotation_evidence_id,
                    "mapping_status": e.mapping_status,
                } for e in self.entries
            ],
        }

    def validate(self) -> None:
        if not self.release or not SHA256.fullmatch(self.annotation_file_sha256):
            raise FeatureContractError("frozen annotation release and source-file SHA required")
        if not self.entries:
            raise FeatureContractError("empty mapping table is not valid")
        for entry in self.entries:
            entry.validate()
        keys = [(e.namespace, e.source_id) for e in self.entries]
        if keys != sorted(keys) or len(set(keys)) != len(keys):
            raise FeatureContractError("mapping keys must be unique and sorted")
        if sha_json(self.body()) != self.contract_sha256:
            raise FeatureContractError("frozen annotation digest mismatch")

    def lookup_index(self) -> dict[tuple[str, str], str]:
        """Validate once, then construct a one-to-one source-key lookup.

        For tens of thousands of genes, rebuilding the entire mapping on every
        query is quadratic. This validated index is local to one operation:
        it is NEVER cached across a changed annotation or used as authority
        independently of the frozen annotation digest.
        """
        self.validate()
        return {
            (e.namespace, e.source_id): e.canonical_ensembl for e in self.entries
        }

    def lookup(self, namespace: str, source_id: str) -> str | None:
        if namespace not in VALID_NAMESPACES:
            raise FeatureContractError("unknown source feature namespace")
        # Direct standalone lookups remain fail-closed, including for an
        # independently altered or malformed frozen-annotation object.
        return self.lookup_index().get((namespace, source_id))


def freeze_annotation(
    *, release: str, annotation_file_sha256: str,
    entries: Sequence[FeatureMapEntry],
) -> FrozenAnnotation:
    """Build a content-digested table after external annotation authentication.

    Deliberately does NOT claim independent authentication of the externally
    supplied release/hash. Producer use requires a separate physical gate.
    """
    ordered = tuple(sorted(entries, key=lambda e: (e.namespace, e.source_id)))
    body = {
        "schema": "CROSS_STUDY_FEATURE_MAP_V1",
        "release": release, "annotation_file_sha256": annotation_file_sha256,
        "entries": [
            {
                "namespace": e.namespace, "source_id": e.source_id,
                "canonical_ensembl": e.canonical_ensembl,
                "annotation_evidence_id": e.annotation_evidence_id,
                "mapping_status": e.mapping_status,
            } for e in ordered
        ],
    }
    result = FrozenAnnotation(release, annotation_file_sha256, ordered, sha_json(body))
    result.validate()
    return result


@dataclass(frozen=True)
class StudyFeatures:
    study: str
    assay: str
    namespace: str
    original_ids: tuple[str, ...]
    # Shape (samples, features). Rows must be bona fide assay units, not cells
    # silently relabeled as independent donors.
    assayed: np.ndarray
    detected: np.ndarray

    def validate(self) -> None:
        if not self.study or not self.assay or self.namespace not in VALID_NAMESPACES:
            raise FeatureContractError("study, assay and known namespace required")
        if not self.original_ids or not all(self.original_ids):
            raise FeatureContractError("empty original feature universe")
        if len(set(self.original_ids)) != len(self.original_ids):
            raise FeatureContractError("duplicate original feature ID")
        a, d = np.asarray(self.assayed), np.asarray(self.detected)
        if a.ndim != 2 or a.shape != d.shape or a.shape[1] != len(self.original_ids):
            raise FeatureContractError("assay and detection masks must align each sample×feature")
        if a.dtype != np.bool_ or d.dtype != np.bool_:
            raise FeatureContractError("assay and detection masks must be boolean")
        if np.any(d & ~a):
            raise FeatureContractError("detected feature cannot be structurally unmeasured")

    def status(self, row: int, column: int) -> ObservationStatus:
        self.validate()
        if not self.assayed[row, column]:
            return ObservationStatus.STRUCTURALLY_UNMEASURED
        if self.detected[row, column]:
            return ObservationStatus.ASSAYED_DETECTED
        return ObservationStatus.ASSAYED_UNDETECTED



def study_identity_digest(study: StudyFeatures) -> str:
    """Bind source feature order and experimental identity into alignment."""
    study.validate()
    return sha_json({
        "study": study.study, "assay": study.assay,
        "namespace": study.namespace, "original_ids": list(study.original_ids),
    })


@dataclass(frozen=True)
class CrossStudyAlignment:
    canonical_ids: tuple[str, ...]
    # One row per canonical ID. Missing source feature is -1, NOT zero.
    index_a: tuple[int, ...]
    index_b: tuple[int, ...]
    namespace_a: str
    namespace_b: str
    frozen_annotation_sha256: str
    source_order_digest_a: str
    source_order_digest_b: str
    alignment_sha256: str

    def validate(self) -> None:
        if len(self.canonical_ids) != len(self.index_a) or len(self.canonical_ids) != len(self.index_b):
            raise FeatureContractError("alignment vector lengths disagree")
        if len(set(self.canonical_ids)) != len(self.canonical_ids):
            raise FeatureContractError("duplicate canonical gene after join")
        body = {
            "schema": "CROSS_STUDY_ALIGNMENT_V1",
            "canonical_ids": list(self.canonical_ids),
            "index_a": list(self.index_a), "index_b": list(self.index_b),
            "namespace_a": self.namespace_a, "namespace_b": self.namespace_b,
            "frozen_annotation_sha256": self.frozen_annotation_sha256,
            "source_order_digest_a": self.source_order_digest_a,
            "source_order_digest_b": self.source_order_digest_b,
        }
        if sha_json(body) != self.alignment_sha256:
            raise FeatureContractError("alignment was changed after freeze")


def align(
    a: StudyFeatures, b: StudyFeatures, annotation: FrozenAnnotation,
    *, same_gene_policy: str = "REJECT_COLLISION",
) -> CrossStudyAlignment:
    """Full outer union. No zero fill; unresolved/ambiguous IDs fail closed.

    Explicit duplicate canonical mappings within a study are not arbitrarily
    collapsed: downstream operators must adopt a separately reviewed collision
    policy and produce a new versioned contract.
    """
    a.validate()
    b.validate()
    # One frozen-digest validation and one lookup-index build per alignment.
    # Previously annotation.lookup() rebuilt/rehash-validated all entries
    # once for EVERY SOURCE FEATURE, O(features * annotation entries).
    mapping_index = annotation.lookup_index()
    if same_gene_policy != "REJECT_COLLISION":
        raise FeatureContractError("unsupported gene collision policy")
    mapped = []
    for study in (a, b):
        index: dict[str, int] = {}
        for i, gene in enumerate(study.original_ids):
            canonical = mapping_index.get((study.namespace, gene))
            if canonical is None:
                raise FeatureContractError(
                    f"{study.study}/{study.assay}: unmapped feature {gene!r}; "
                    "publish an explicit source-specific NOT_MAPPED exclusion table "
                    "before cross-study evaluation rather than silently dropping"
                )
            if canonical in index:
                raise FeatureContractError(
                    f"{study.study}/{study.assay}: multiple original IDs map to "
                    f"{canonical}; collision cannot be resolved silently"
                )
            index[canonical] = i
        mapped.append(index)
    ids = tuple(sorted(set(mapped[0]) | set(mapped[1])))
    ia = tuple(mapped[0].get(g, -1) for g in ids)
    ib = tuple(mapped[1].get(g, -1) for g in ids)
    body = {
        "schema": "CROSS_STUDY_ALIGNMENT_V1",
        "canonical_ids": list(ids), "index_a": list(ia), "index_b": list(ib),
        "namespace_a": a.namespace, "namespace_b": b.namespace,
        "frozen_annotation_sha256": annotation.contract_sha256,
        "source_order_digest_a": study_identity_digest(a),
        "source_order_digest_b": study_identity_digest(b),
    }
    result = CrossStudyAlignment(
        ids, ia, ib, a.namespace, b.namespace,
        annotation.contract_sha256,
        study_identity_digest(a), study_identity_digest(b),
        sha_json(body),
    )
    result.validate()
    return result


def aligned_observation(
    study: StudyFeatures, alignment: CrossStudyAlignment,
    values: np.ndarray, *, side: str, sample_index: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return aligned values and distinct assay/detection masks.

    STRUCTURALLY_UNMEASURED output is NaN; ASSAYED_UNDETECTED retains measured
    zero if and only if the original source values are genuinely zero.
    """
    study.validate()
    alignment.validate()
    if side not in ("a", "b"):
        raise FeatureContractError("must select alignment side a or b")
    expected_namespace = alignment.namespace_a if side == "a" else alignment.namespace_b
    expected_study = (
        alignment.source_order_digest_a if side == "a"
        else alignment.source_order_digest_b
    )
    if study.namespace != expected_namespace or study_identity_digest(study) != expected_study:
        raise FeatureContractError(
            "study identity or original feature order drifted from the frozen alignment"
        )
    source_index = alignment.index_a if side == "a" else alignment.index_b
    raw = np.asarray(values, dtype=float)
    if raw.shape != study.assayed.shape:
        raise FeatureContractError("molecular values and assay masks differ")
    if not 0 <= sample_index < raw.shape[0]:
        raise FeatureContractError("sample index not found")
    n = len(source_index)
    out = np.full(n, np.nan, dtype=float)
    assayed = np.zeros(n, dtype=bool)
    detected = np.zeros(n, dtype=bool)
    for j, i in enumerate(source_index):
        if i == -1:
            continue
        if not 0 <= i < len(study.original_ids):
            raise FeatureContractError("invalid source feature index")
        assayed[j] = bool(study.assayed[sample_index, i])
        detected[j] = bool(study.detected[sample_index, i])
        if assayed[j]:
            val = raw[sample_index, i]
            if not np.isfinite(val) or val < 0:
                raise FeatureContractError("assayed raw count must be nonnegative and finite")
            if detected[j] != (val > 0):
                raise FeatureContractError("detection mask contradicts observed raw counts")
            out[j] = val
    return out, assayed, detected
