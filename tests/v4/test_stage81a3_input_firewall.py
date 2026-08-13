from __future__ import annotations

import ast
import inspect
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT / "src"))

from sea_ad_jepa.v4 import (
    GeneExpressionTokenizer,
    GeneSetMechanicsEncoder,
    LatentPredictor,
    PerceiverCrossAttention,
    V4AEncoderSkeleton,
)


V4_SOURCE = PROJECT / "src/sea_ad_jepa/v4"
FORBIDDEN_API_TERMS = {
    "donor", "study", "dataset", "source", "library", "specimen", "sample",
    "cell_type", "diagnosis", "pathology", "trajectory", "graph", "regulatory",
    "spatial", "coordinate", "perturbation", "dose", "drug", "amyloid", "tau",
    "braak", "cerad", "thal", "at8", "gfap", "iba1", "neun", "split_identity",
}
FORBIDDEN_IMPORT_FRAGMENTS = {
    "sea_ad_jepa.jepa", "sea_ad_jepa.graph_jepa", "sea_ad_jepa.mil_head",
    "sea_ad_jepa.models.non_graph_v3", "trajectory", "pathology", "condition",
}


def test_public_forward_apis_are_narrow_typed_tensor_interfaces() -> None:
    expected = {
        GeneExpressionTokenizer.forward: {"self", "gene_ids", "expression"},
        PerceiverCrossAttention.forward: {
            "self", "gene_tokens", "valid_mask", "return_attention",
        },
        GeneSetMechanicsEncoder.forward: {
            "self", "gene_ids", "expression", "measurement_mask", "context_mask",
            "view", "return_attention",
        },
        V4AEncoderSkeleton.forward: {
            "self", "gene_ids", "expression", "measurement_mask", "context_mask",
            "view",
        },
        LatentPredictor.forward: {"self", "context_latents"},
    }
    for method, allowed in expected.items():
        parameters = set(inspect.signature(method).parameters)
        assert parameters == allowed
        assert parameters.isdisjoint(FORBIDDEN_API_TERMS)


def test_v4_modules_have_no_metadata_dictionary_or_forbidden_imports() -> None:
    for path in sorted(V4_SOURCE.glob("*.py")):
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.append(node.module or "")
            elif isinstance(node, ast.arg):
                assert node.arg not in {"metadata", "metadata_dict", "covariates"}
        joined = " ".join(imports).lower()
        assert not any(fragment in joined for fragment in FORBIDDEN_IMPORT_FRAGMENTS)


def test_no_mask_or_unmeasured_embedding_and_no_positional_embedding() -> None:
    source = "\n".join(
        path.read_text(encoding="utf-8").lower()
        for path in sorted(V4_SOURCE.glob("*.py"))
    )
    assert "mask_embedding" not in source
    assert "unmeasured_embedding" not in source
    assert "source_embedding" not in source
    assert "position_embedding" not in source
    assert "positional_embedding" not in source
