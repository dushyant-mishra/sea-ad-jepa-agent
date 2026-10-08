"""Out-of-fold and low-rank-plus-diagonal covariance mechanics."""

from __future__ import annotations

import math

import torch


def deterministic_fold_ids(n: int, folds: int = 8, *, device: torch.device | None = None) -> torch.Tensor:
    if folds < 2 or n % folds:
        raise ValueError("balanced deterministic folds require n divisible by folds")
    return torch.arange(n, device=device) % folds


def fold_indices(fold_ids: torch.Tensor, fold: int) -> tuple[torch.Tensor, torch.Tensor]:
    held_out = torch.nonzero(fold_ids == fold, as_tuple=False).flatten()
    fitting = torch.nonzero(fold_ids != fold, as_tuple=False).flatten()
    if torch.isin(held_out, fitting).any():
        raise RuntimeError("OOF leakage")
    return fitting, held_out


def positive_correlated_spectrum(covariance: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    diagonal_removed = covariance.double() - torch.diag(torch.diag(covariance.double()))
    diagonal_removed = 0.5 * (diagonal_removed + diagonal_removed.T)
    values, vectors = torch.linalg.eigh(diagonal_removed)
    order = torch.argsort(values, descending=True)
    values, vectors = values[order], vectors[:, order]
    positive = values > 0
    return values[positive], vectors[:, positive], diagonal_removed


def select_correlated_rank(
    positive_values: torch.Tensor,
    *,
    target: float = 0.50,
    minimum: int = 4,
    maximum: int = 32,
) -> tuple[int, float, bool]:
    if len(positive_values) < minimum:
        raise ValueError("fewer than minimum positive correlated eigenvalues")
    energy = positive_values.double().square()
    cumulative = torch.cumsum(energy, 0) / energy.sum().clamp_min(1e-30)
    first = int(torch.nonzero(cumulative >= target, as_tuple=False)[0]) + 1
    rank = min(max(first, minimum), maximum)
    captured = float(cumulative[rank - 1])
    return rank, captured, first <= maximum


def shared_architecture_rank(ranks_by_family: dict[str, list[int]], maximum: int = 32) -> int:
    if not ranks_by_family or any(not ranks for ranks in ranks_by_family.values()):
        raise ValueError("each mask family requires ranks")
    medians = [torch.quantile(torch.tensor(ranks, dtype=torch.float64), .5).item() for ranks in ranks_by_family.values()]
    return min(maximum, int(math.ceil(max(medians))))


def construct_lrd(
    covariance: torch.Tensor,
    rank: int,
    *,
    floor_multiplier: float = 1.0e-4,
) -> dict[str, torch.Tensor | float | int]:
    values, vectors, correlated = positive_correlated_spectrum(covariance)
    used = min(rank, len(values))
    u = vectors[:, :used] * torch.sqrt(values[:used])[None, :]
    if used < rank:
        u = torch.cat((u, torch.zeros(len(covariance), rank - used, dtype=u.dtype, device=u.device)), 1)
    target_diagonal = torch.diag(covariance.double())
    floor = floor_multiplier * float(target_diagonal.median())
    raw_diagonal = target_diagonal - u.square().sum(1)
    diagonal = raw_diagonal.clamp_min(floor)
    matrix = torch.diag(diagonal) + u @ u.T
    target_offdiag = correlated.square().sum().clamp_min(1e-30)
    predicted_offdiag = u @ u.T - torch.diag(u.square().sum(1))
    energy_ratio = float(predicted_offdiag.square().sum() / target_offdiag)
    explained = float(1.0 - (correlated - predicted_offdiag).square().sum() / target_offdiag)
    return {
        "diagonal": diagonal,
        "u": u,
        "matrix": matrix,
        "floor": floor,
        "floor_count": int((raw_diagonal < floor).sum()),
        "positive_eigenvalues": values,
        "offdiagonal_energy_ratio": energy_ratio,
        "offdiagonal_reconstruction_explained_fraction": explained,
    }


def woodbury_quadratic_logdet(
    residuals: torch.Tensor,
    diagonal: torch.Tensor,
    u: torch.Tensor,
) -> tuple[torch.Tensor, torch.Tensor]:
    values = residuals.double()
    diagonal = diagonal.double().clamp_min(1e-30)
    u = u.double()
    inverse_diagonal = diagonal.reciprocal()
    middle = torch.eye(u.shape[1], dtype=torch.float64, device=u.device) + u.T @ (inverse_diagonal[:, None] * u)
    cholesky = torch.linalg.cholesky(middle)
    scaled = values * inverse_diagonal
    projection = scaled @ u
    correction = torch.cholesky_solve(projection.T, cholesky).T
    quadratic = (values * scaled).sum(1) - (projection * correction).sum(1)
    logdet = diagonal.log().sum() + 2.0 * torch.log(torch.diag(cholesky)).sum()
    return quadratic, logdet


def lrd_gaussian_nll(residuals: torch.Tensor, diagonal: torch.Tensor, u: torch.Tensor) -> torch.Tensor:
    quadratic, logdet = woodbury_quadratic_logdet(residuals, diagonal, u)
    return 0.5 * (residuals.shape[1] * math.log(2 * math.pi) + logdet + quadratic)


def lrd_mahalanobis(residuals: torch.Tensor, diagonal: torch.Tensor, u: torch.Tensor) -> torch.Tensor:
    return woodbury_quadratic_logdet(residuals, diagonal, u)[0]
