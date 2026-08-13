from __future__ import annotations

import sys
from pathlib import Path

import pytest
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from sea_ad_jepa.v4.context_entities import ContextEntity, ContextNeighborhood
from sea_ad_jepa.v4.intrinsic_cell_package import IntrinsicCellPackage


def package() -> IntrinsicCellPackage:
    return IntrinsicCellPackage(torch.zeros(4096, 160), torch.zeros(160), torch.zeros(160), torch.zeros(3), torch.zeros(2))


def test_context_entity_requires_physical_relation() -> None:
    with pytest.raises(ValueError, match="similarity"):
        ContextEntity("x", "cell", package(), "rna_similarity", 1.0, True, torch.ones(1))


def test_stage81a3_forbids_pathology_entities() -> None:
    with pytest.raises(ValueError, match="pathology"):
        ContextEntity("x", "plaque", None, "euclidean", 1.0, True, torch.ones(1))


def test_generic_noncell_entity_is_supported() -> None:
    entity = ContextEntity("v", "future_vessel", None, "euclidean", 2.0, True, torch.ones(1))
    neighborhood = ContextNeighborhood("target", (entity,), "synthetic")
    assert neighborhood.valid_entities() == (entity,)
