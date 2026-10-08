import pytest

from sea_ad_jepa.qualification.visibility import (
    FieldDeclaration,
    VisibilityClass,
    VisibilityViolation,
    assert_model_visible,
    assert_preprocessing_visible,
    derive_field_visibility,
)


def test_split_only_donor_id_cannot_be_hashed_into_model_feature():
    donor = FieldDeclaration("donor_id", VisibilityClass.SPLIT_ONLY)
    with pytest.raises(VisibilityViolation, match="donor_id"):
        derive_field_visibility(
            "donor_hash",
            (donor,),
            VisibilityClass.MODEL_VISIBLE,
        )


def test_oracle_private_state_cannot_be_renamed_or_aggregated_into_visible_feature():
    private = FieldDeclaration("z_reg_private", VisibilityClass.ORACLE_ONLY)
    with pytest.raises(VisibilityViolation, match="z_reg_private"):
        derive_field_visibility(
            "private_summary",
            (private,),
            VisibilityClass.PREPROCESSING_VISIBLE,
        )
    with pytest.raises(VisibilityViolation):
        derive_field_visibility(
            "private_embedding",
            (private,),
            VisibilityClass.MODEL_VISIBLE,
        )


def test_model_visible_parents_can_produce_model_visible_descendant():
    expression = FieldDeclaration("expression", VisibilityClass.MODEL_VISIBLE)
    mask = FieldDeclaration("measurement_mask", VisibilityClass.MODEL_VISIBLE)
    child = derive_field_visibility(
        "masked_expression",
        (expression, mask),
        VisibilityClass.MODEL_VISIBLE,
    )
    assert child.visibility is VisibilityClass.MODEL_VISIBLE
    assert child.parent_names == ("expression", "measurement_mask")
    assert_model_visible(child)


def test_lawful_operator_context_stays_on_operator_interface():
    depth = FieldDeclaration("depth_characteristics", VisibilityClass.LAWFUL_OPERATOR_CONTEXT)
    derived = derive_field_visibility(
        "depth_bucket",
        (depth,),
        VisibilityClass.LAWFUL_OPERATOR_CONTEXT,
    )
    assert derived.visibility is VisibilityClass.LAWFUL_OPERATOR_CONTEXT
    with pytest.raises(VisibilityViolation):
        assert_model_visible(derived)
    with pytest.raises(VisibilityViolation):
        derive_field_visibility(
            "depth_as_free_feature",
            (depth,),
            VisibilityClass.MODEL_VISIBLE,
        )


def test_preprocessing_visibility_does_not_imply_model_visibility():
    library_context = FieldDeclaration(
        "lawful_preprocessing_context", VisibilityClass.PREPROCESSING_VISIBLE
    )
    assert_preprocessing_visible(library_context)
    with pytest.raises(VisibilityViolation):
        assert_model_visible(library_context)


def test_unknown_or_empty_parent_lineage_fails_closed_for_derived_field():
    with pytest.raises(VisibilityViolation, match="parent"):
        derive_field_visibility(
            "orphan_derived_feature",
            (),
            VisibilityClass.MODEL_VISIBLE,
        )
