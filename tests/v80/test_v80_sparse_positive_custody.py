from pathlib import Path

from scripts.v80.finalize_v80_sparse_positive_package import build_package_receipt
from scripts.v80.v80_sparse_positive_benchmark import build_sparse_positive_worlds


def test_receipt_binds_all_v80_executables_runtime_and_nonregression_file():
    receipt = build_package_receipt(
        worlds=build_sparse_positive_worlds(seed_root=41000000),
        repo_root=Path.cwd(),
        contract_path=Path("results/v80/sparse_positive/V80_SPARSE_POSITIVE_QUALIFICATION_CONTRACT_V1.json"),
    )
    assert set(receipt["source_sha256"]) == {
        "scripts/v80/v80_sparse_positive_benchmark.py",
        "scripts/v80/v80_sparse_positive_adjudicator.py",
        "scripts/v80/finalize_v80_sparse_positive_package.py",
    }
    assert all(len(x) == 64 for x in receipt["source_sha256"].values())
    assert receipt["runtime_environment"] == {"python": "3.11.9", "numpy": "2.3.5"}
    assert len(receipt["nonregression_binding_sha256"]) == 64
    assert receipt["status"] == "BENCHMARK_PACKAGE_ONLY__NO_ESTIMATOR_RUN"
    assert not any(receipt["authority"].values())
