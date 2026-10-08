"""The S174 replay reruns the affected analyses on the rebuilt cache without rewriting history. Every
script that reads the real TRAIN cache must take --cache, defaulting to the original cache so the old
results stay reproducible, and the ones that read upstream envelopes must take --inputs-dir, defaulting
to results/v77, so a corrected replay reads corrected inputs."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
V77 = ROOT / "scripts" / "v77"
CACHE_READERS = ("build_v77_frozen_evaluation_universe.py", "build_v77_calibration_envelope.py",
                 "build_v77_topology_calibration.py", "build_v77_real_calibration.py", "build_v77_abundance_envelope.py",
                 "build_v77_within_cohort_envelope.py", "diagnose_v77_real_coverage_confound.py",
                 "validate_v77_coverage_strata.py")
INPUT_READERS = ("build_v77_within_cohort_envelope.py", "diagnose_v77_real_coverage_confound.py")


def test_every_cache_reader_takes_cache_with_the_original_default():
    for name in CACHE_READERS:
        src = (V77 / name).read_text(encoding="utf-8")
        assert 'add_argument("--cache", default=str(' in src and "DEFAULT_CACHE" in src, name
        assert "load_real(RC.DEFAULT_CACHE)" not in src, f"{name} still loads a fixed cache"


def test_upstream_readers_take_inputs_dir_defaulting_to_results_v77():
    for name in INPUT_READERS:
        src = (V77 / name).read_text(encoding="utf-8")
        assert 'add_argument("--inputs-dir"' in src and '"results"' in src and '"v77"' in src, name
        assert 'ROOT / "results/v77/V77_REAL' not in src and '"results" / "v77" /\n' not in src, name
