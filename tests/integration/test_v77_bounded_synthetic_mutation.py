import inspect


def test_bounded_mutation_surface_matches_preregistered_contract():
    from sea_ad_jepa.qualification import v77_bounded_mutation

    assert v77_bounded_mutation.HALF_LIFE_PRESENTATIONS == 1000
    assert v77_bounded_mutation.PRESENTATIONS_PER_SUCCESSFUL_REHEARSAL == 2
    assert (
        v77_bounded_mutation.SUCCESS_VERDICT
        == "PASS__ONE_SYNTHETIC_GUARDED_UPDATE_PHYSICALLY_BOUND__NON_PRODUCTION"
    )

    parameters = inspect.signature(v77_bounded_mutation.run_bounded_synthetic_mutation).parameters
    assert tuple(parameters) == (
        "batch",
        "physical_bindings",
        "q_safety_proof",
        "runtime_source_sha256",
        "init_seed",
        "persistence_path",
    )
