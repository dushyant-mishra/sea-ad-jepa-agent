from sea_ad_jepa.perturbation.benchmark_domain_contract_v1 import (
    BiologicalContext, ClaimScope, qualify_domain,
)


def brain():
    return BiologicalContext(
        species="Homo sapiens",
        tissue="adult human brain",
        preparation="single-nucleus/single-cell transcriptomics",
        cell_type="microglia",
        culture_status="in_tissue",
    )


def cultured_microglia():
    return BiologicalContext(
        species="Homo sapiens",
        tissue="in vitro",
        preparation="iPSC-derived microglia CROP-seq",
        cell_type="microglia",
        culture_status="cell_culture",
    )


def test_cultured_microglia_never_becomes_direct_brain_generalization():
    q = qualify_domain(brain(), cultured_microglia(),
                       baseline_state_similarity_measured=True)
    assert q.claim_scope == ClaimScope.CROSS_DOMAIN_DEVELOPMENT
    assert q.direct_brain_generalization_authorized is False
    assert q.baseline_state_similarity_measured is True


def test_unmeasured_baseline_similarity_stays_explicit():
    q = qualify_domain(brain(), cultured_microglia(),
                       baseline_state_similarity_measured=False)
    assert q.claim_scope == ClaimScope.CROSS_DOMAIN_DEVELOPMENT
    assert q.baseline_state_similarity_measured is False


def test_same_domain_can_be_labeled_same_domain_only():
    q = qualify_domain(brain(), brain(), baseline_state_similarity_measured=True)
    assert q.claim_scope == ClaimScope.SAME_DOMAIN
    assert q.direct_brain_generalization_authorized is True


def test_cross_species_is_not_qualified():
    mouse = BiologicalContext(
        species="Mus musculus", tissue="brain",
        preparation="single-cell", cell_type="microglia",
        culture_status="in_tissue",
    )
    q = qualify_domain(brain(), mouse, baseline_state_similarity_measured=True)
    assert q.claim_scope == ClaimScope.NOT_QUALIFIED
    assert q.direct_brain_generalization_authorized is False
