"""Authenticated metadata-first loader for the bounded reader-fit F0 fixture."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Callable, Mapping, Sequence

import numpy as np
import pandas as pd


EXPECTED_SELECTION_SHA256 = "2f2eacee4274a0e07684e1744adf3750aae6b712f86264e061ccf517a6240acb"
EXPECTED_IDENTITY_SHA256 = "8a73338f171de459c5bb5733fa9f4f25d4cd4f16b14b8c7d3ff6ba0339690309"
EXPECTED_READER_SPLIT_SHA256 = "efe43e63bfd580085f115f74dd00fdf3051f2c2a77674c99cee5c9ce43322511"


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def load_authenticated_reader_fit_fixture(
    *,
    requests: Sequence[Mapping[str, object]],
    selection_path: Path,
    identity_path: Path,
    reader_split_path: Path,
    payload_loader: Callable[[], Mapping[str, np.ndarray]],
) -> tuple[np.ndarray, np.ndarray, pd.DataFrame]:
    """Resolve and authorize every requested row before payload_loader is called."""
    authorities = {
        Path(selection_path): EXPECTED_SELECTION_SHA256,
        Path(identity_path): EXPECTED_IDENTITY_SHA256,
        Path(reader_split_path): EXPECTED_READER_SPLIT_SHA256,
    }
    for path, expected in authorities.items():
        if not path.is_file() or _sha(path) != expected:
            raise RuntimeError("authenticated F0 fixture authority mismatch: " + str(path))
    split = pd.read_csv(reader_split_path, dtype=str)
    if split.donor_id.duplicated().any() or set(split.reader_partition) != {
        "reader_fit",
        "reader_validation",
        "reader_oracle",
    }:
        raise RuntimeError("reader split authority geometry mismatch")
    donor_role = split.set_index("donor_id").reader_partition.to_dict()
    selection = pd.read_csv(selection_path).sort_values("selection_row", kind="stable")
    identity = pd.read_csv(identity_path).sort_values("selection_row", kind="stable")
    authority = selection.merge(
        identity[["selection_row", "retrieval_backend"]],
        on="selection_row",
        how="inner",
        validate="one_to_one",
    )
    if len(authority) != 84 or authority.selection_row.duplicated().any():
        raise RuntimeError("bounded fixture row authority mismatch")
    by_row = authority.set_index("selection_row", drop=False)
    resolved_rows: list[int] = []
    for request in requests:
        donor = str(request.get("donor_id", ""))
        declared_partition = str(request.get("reader_partition", ""))
        if donor not in donor_role or donor_role[donor] != "reader_fit" or declared_partition != "reader_fit":
            raise PermissionError("protected donor/partition rejected before expression read")
        if str(request.get("foundation_split", "")) != "foundation/train":
            raise PermissionError("DEV/SEALED/non-TRAIN rejected before expression read")
        if bool(request.get("pathology", False)) or bool(request.get("external", False)):
            raise PermissionError("pathology/external row rejected before expression read")
        try:
            selection_row = int(request["selection_row"])
        except (KeyError, TypeError, ValueError) as error:
            raise PermissionError("missing authenticated row locator") from error
        if selection_row not in by_row.index:
            raise PermissionError("row is outside authenticated reader-fit fixture")
        expected = by_row.loc[selection_row]
        if str(expected.donor_id) != donor or str(expected.canonical_cell_id) != str(
            request.get("canonical_cell_id", "")
        ):
            raise PermissionError("row identity/donor relabel rejected before expression read")
        if expected.reader_partition != "reader_fit" or expected.foundation_split != "foundation/train":
            raise PermissionError("authority row is not reader-fit TRAIN")
        resolved_rows.append(selection_row)
    payload = payload_loader()
    if set(payload) != {"normalized_values", "observation_states"}:
        raise RuntimeError("payload loader schema mismatch")
    values = np.asarray(payload["normalized_values"])
    states = np.asarray(payload["observation_states"])
    if values.shape != (84, 41_238) or states.shape != values.shape:
        raise RuntimeError("payload geometry mismatch")
    return values[resolved_rows].copy(), states[resolved_rows].copy(), by_row.loc[resolved_rows].reset_index(drop=True)
