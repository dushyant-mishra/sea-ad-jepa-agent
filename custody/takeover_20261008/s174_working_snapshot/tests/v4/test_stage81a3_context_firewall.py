from __future__ import annotations

import sys
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from sea_ad_jepa.v4.context_ledger_query import LedgerQuery
from sea_ad_jepa.v4.intrinsic_cell_package import IntrinsicCellPackage


def test_intrinsic_package_detaches_without_mutation() -> None:
    values = [torch.randn(2, 3, requires_grad=True), torch.randn(3, requires_grad=True), torch.randn(3), torch.randn(2), torch.randn(2)]
    package = IntrinsicCellPackage(*values)
    before = package.hashes(); detached = package.detached()
    assert package.hashes() == before == detached.hashes()
    assert all(not value.requires_grad for value in detached.tensors())


def test_ledger_query_is_read_only_and_can_retrieve_fine_signal() -> None:
    torch.manual_seed(1)
    query = LedgerQuery(width=4, heads=1).eval()
    target = torch.randn(1, 4, requires_grad=True)
    ledger = torch.zeros(1, 1, 4096, 4, requires_grad=True)
    with torch.no_grad(): ledger[0, 0, 3000] = target.detach()[0]
    before = ledger.detach().clone()
    output = query(target, ledger)
    output.sum().backward()
    assert target.grad is None and ledger.grad is None
    assert torch.equal(ledger.detach(), before)
    assert torch.isfinite(output).all()
