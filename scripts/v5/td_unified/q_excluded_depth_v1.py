"""Rights-ladder observation producer with a query-excluded depth (stub for RED)."""
from __future__ import annotations


class QExcludedObservationError(ValueError):
    """Malformed, ambiguous or non-exact producer input."""


class QExcludedDepthNotEstimable(QExcludedObservationError):
    """Withheld mass cannot be removed exactly from the depth."""


def produce_rights_ladder_observations(*, cells, address_rights, operator_states, ladder):
    raise NotImplementedError("RED stub")
