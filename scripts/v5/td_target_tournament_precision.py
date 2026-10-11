"""Outcome-blind precision/estimability helpers for target-tournament design."""
import math


def _validate_alpha(alpha_eff):
    if not (0.0 < float(alpha_eff) < 1.0):
        raise ValueError('alpha_eff must be in (0,1)')
    return float(alpha_eff)


def minimum_donors_for_sign_resolution(alpha_eff):
    alpha_eff = _validate_alpha(alpha_eff)
    n = 1
    while min(1.0, 2.0 * (0.5 ** n)) > alpha_eff:
        n += 1
    return n


def _binom_tail_ge(k, n):
    return sum(math.comb(n, j) for j in range(k, n + 1)) / (2.0 ** n)


def _binom_tail_le(k, n):
    return sum(math.comb(n, j) for j in range(0, k + 1)) / (2.0 ** n)


def exact_two_sided_sign_p(successes, n_nonzero):
    if n_nonzero < 0 or successes < 0 or successes > n_nonzero:
        raise ValueError('invalid sign counts')
    if n_nonzero == 0:
        return 1.0
    lower = _binom_tail_le(successes, n_nonzero)
    upper = _binom_tail_ge(successes, n_nonzero)
    return min(1.0, 2.0 * min(lower, upper))


def sign_recurrence_gate(deltas, alpha_eff):
    alpha_eff = _validate_alpha(alpha_eff)
    positives = sum(float(x) > 0 for x in deltas)
    negatives = sum(float(x) < 0 for x in deltas)
    ties = sum(float(x) == 0 for x in deltas)
    n = positives + negatives
    min_n = minimum_donors_for_sign_resolution(alpha_eff)
    p = exact_two_sided_sign_p(positives, n)
    estimable = n >= min_n
    return {
        'n_total': len(deltas),
        'n_nonzero': n,
        'n_positive': positives,
        'n_negative': negatives,
        'n_ties': ties,
        'minimum_nonzero_donors_for_resolution': min_n,
        'resolution_estimable': estimable,
        'two_sided_p': p,
        'alpha_eff': alpha_eff,
        'pass': bool(estimable and positives > negatives and p <= alpha_eff),
    }


def minimum_permutation_draws_for_resolution(alpha_eff):
    alpha_eff = _validate_alpha(alpha_eff)
    return max(1, math.ceil(1.0 / alpha_eff) - 1)
