"""Prospective relational-loss reduction for ragged finite triplet samples.

Triplet count is a sampling/compute fact.  Scientific group contribution is an
explicit externally supplied weight.  Duplicating sampled triplets inside one
group therefore cannot increase that group's objective mass.
"""
from __future__ import annotations
import torch


def weighted_group_mean_relational_loss(
    triplet_losses: torch.Tensor,
    group_ids: torch.Tensor,
    group_weights: torch.Tensor,
) -> torch.Tensor:
    """Mean within each observed group, then scientific-weighted mean of groups.

    group_ids must be contiguous integer IDs 0..G-1 and every group must have at
    least one sampled triplet. group_weights has one nonnegative finite weight per
    group and positive total mass. There is deliberately no default weighting.
    """
    if triplet_losses.ndim != 1 or not triplet_losses.is_floating_point():
        raise ValueError("triplet_losses must be floating [triplets]")
    if group_ids.ndim != 1 or len(group_ids) != len(triplet_losses) or group_ids.dtype not in (torch.int32,torch.int64):
        raise ValueError("group_ids must be integer [triplets]")
    if group_weights.ndim != 1 or not group_weights.is_floating_point() or len(group_weights) < 1:
        raise ValueError("group_weights must be floating [groups]")
    if len(triplet_losses) < 1:
        raise ValueError("at least one sampled triplet is required")
    if not bool(torch.isfinite(triplet_losses).all()) or not bool(torch.isfinite(group_weights).all()):
        raise ValueError("losses and weights must be finite")
    if bool((group_weights < 0).any()) or not bool((group_weights > 0).any()):
        raise ValueError("group_weights must be nonnegative with positive total mass")
    gids=group_ids.to(torch.int64)
    if bool((gids < 0).any()) or int(gids.max()) >= len(group_weights):
        raise ValueError("group_ids outside group_weights range")
    expected=torch.arange(len(group_weights),device=gids.device,dtype=torch.int64)
    observed=torch.unique(gids,sorted=True)
    if not torch.equal(observed,expected):
        raise ValueError("every weighted group must have at least one sampled triplet and IDs must be contiguous")
    losses=triplet_losses.float()
    means=[]
    for group in range(len(group_weights)):
        means.append(losses[gids.eq(group)].mean())
    group_means=torch.stack(means)
    weights=group_weights.float().to(group_means.device)
    return (group_means*weights).sum()/weights.sum()
