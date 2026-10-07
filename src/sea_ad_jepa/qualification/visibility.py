from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class VisibilityViolation(ValueError):
    """Raised when data attempts to cross a qualification visibility firewall."""


class VisibilityClass(str, Enum):
    MODEL_VISIBLE = "MODEL_VISIBLE"
    PREPROCESSING_VISIBLE = "PREPROCESSING_VISIBLE"
    LAWFUL_OPERATOR_CONTEXT = "LAWFUL_OPERATOR_CONTEXT"
    SPLIT_ONLY = "SPLIT_ONLY"
    READOUT_ONLY = "READOUT_ONLY"
    PROVENANCE_ONLY = "PROVENANCE_ONLY"
    ORACLE_ONLY = "ORACLE_ONLY"


@dataclass(frozen=True)
class FieldDeclaration:
    name: str
    visibility: VisibilityClass
    parent_names: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise VisibilityViolation("field name must be explicit and nonempty")
        if not isinstance(self.visibility, VisibilityClass):
            raise VisibilityViolation(f"field {self.name} has unknown visibility")
        if not isinstance(self.parent_names, tuple) or not all(
            isinstance(parent, str) and parent for parent in self.parent_names
        ):
            raise VisibilityViolation(f"field {self.name} has invalid parent lineage")


def derive_field_visibility(
    child_name: str,
    parents: tuple[FieldDeclaration, ...],
    requested: VisibilityClass,
) -> FieldDeclaration:
    if not parents:
        raise VisibilityViolation(f"derived field {child_name} requires explicit parent lineage")
    if not isinstance(requested, VisibilityClass):
        raise VisibilityViolation(f"derived field {child_name} requested unknown visibility")
    if not all(isinstance(parent, FieldDeclaration) for parent in parents):
        raise VisibilityViolation(f"derived field {child_name} has invalid parent declarations")

    parent_visibilities = {parent.visibility for parent in parents}
    if len(parent_visibilities) != 1 or requested not in parent_visibilities:
        names = ", ".join(parent.name for parent in parents)
        raise VisibilityViolation(
            f"derived field {child_name} cannot declassify or mix parent visibility from {names}"
        )

    return FieldDeclaration(
        name=child_name,
        visibility=requested,
        parent_names=tuple(parent.name for parent in parents),
    )


def assert_model_visible(field: FieldDeclaration) -> None:
    if field.visibility is not VisibilityClass.MODEL_VISIBLE:
        raise VisibilityViolation(f"field {field.name} is not MODEL_VISIBLE")


def assert_preprocessing_visible(field: FieldDeclaration) -> None:
    if field.visibility not in {
        VisibilityClass.MODEL_VISIBLE,
        VisibilityClass.PREPROCESSING_VISIBLE,
    }:
        raise VisibilityViolation(f"field {field.name} is not preprocessing-visible")
