"""Adapter replay of *unchanged* Macha #481 test functions on NEW versioned consumer.

The original reviewer source is byte-identical to Git blob
3dda6c2cc9be19d5daececfb07967e94067519f6. This adapter is
not claimed to be unmodified #481 execution on the original V2 API.
It binds the three original API names to the distinct V2-bound-content
producer/consumer and imports the original parametrized tests.

The upstream #474 A4 test is deliberately NOT included; A4 remains RED
with a separately preserved failure receipt. All other tests including the
240-world invariance experiment and the original A1-A3 attacks are replayed.
"""
from types import SimpleNamespace

from scripts.v5.td_unified import observation_normalization_view_v2_bound_content_v1 as B
from tests.v5.td_unified import (
    macha481_review_source_immutable as REVIEW,
)

REVIEW.V2 = SimpleNamespace(
    produce_fixture_student_view_v2=B.produce_fixture_student_view_v2_bound,
    produce_fixture_teacher_view_v2=B.produce_fixture_teacher_view_v2_bound,
    validate_fixture_observation_view_v2=B.validate_fixture_observation_view_v2_bound,
)

_A4_UPSTREAM = "test_red_refusal_of_an_empty_base_cell_does_not_depend_on_withheld_mass"
_replayed_names = []
for _name, _fn in tuple(vars(REVIEW).items()):
    if _name.startswith("test_") and _name != _A4_UPSTREAM:
        globals()[_name] = _fn
        _replayed_names.append(_name)
assert len(_replayed_names) == 8  # 9 original test functions minus upstream A4
assert _A4_UPSTREAM not in _replayed_names
