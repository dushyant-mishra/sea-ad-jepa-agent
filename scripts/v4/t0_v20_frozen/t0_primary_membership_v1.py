from __future__ import annotations
import hashlib
import sqlite3
from pathlib import Path
from typing import Iterable
import pandas as pd
import numpy as np

from t0_stable_cell_key_v1 import (
    MATRIX_ID, NATIVE_CLASS, OPERATOR_INDEX, PARTITION, SOURCE,
    parse_stable_key_exact, stable_key_from_parts,
)

COLUMNS = [
    "source","matrix_id","operator_index","local_row","donor_id","partition",
    "cell_id","native_class","broad_class","stable_key",
]
SQL = f"""SELECT {','.join(COLUMNS)} FROM cells
WHERE source='{SOURCE}' AND matrix_id='{MATRIX_ID}' AND operator_index={OPERATOR_INDEX}
  AND partition='{PARTITION}' AND native_class='{NATIVE_CLASS}'
ORDER BY local_row ASC"""
EXPECTED_ROWS = 20_804
EXPECTED_DONORS = 46
EXPECTED_SQLITE_SHA256 = "a771f08be31a840b5472448c438a153fbca7de93ba2ed31fe692eaeda02e6913"
EXPECTED_CSV_SHA256 = "d471499836118ddaf963ae9241f612d2e9a78bff4add62834347fc0ca06a3529"


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def generate_membership(sqlite_path: str | Path, output_csv: str | Path) -> pd.DataFrame:
    sqlite_path = Path(sqlite_path)
    output_csv = Path(output_csv)
    if sha256_file(sqlite_path) != EXPECTED_SQLITE_SHA256:
        raise ValueError("canonical metadata SQLite hash mismatch")
    con = sqlite3.connect(sqlite_path)
    try:
        frame = pd.read_sql_query(SQL, con)
    finally:
        con.close()
    validate_membership_frame(frame)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(output_csv, index=False, lineterminator="\n")
    if sha256_file(output_csv) != EXPECTED_CSV_SHA256:
        raise AssertionError("generated membership bytes do not match frozen authority")
    return frame


def validate_membership_frame(frame: pd.DataFrame) -> None:
    if list(frame.columns) != COLUMNS:
        raise ValueError("membership schema mismatch")
    if len(frame) != EXPECTED_ROWS:
        raise ValueError("membership row count mismatch")
    if frame["donor_id"].nunique(dropna=False) != EXPECTED_DONORS:
        raise ValueError("membership donor count mismatch")
    if frame["local_row"].duplicated().any() or frame["stable_key"].duplicated().any():
        raise ValueError("membership local_row/stable_key must be unique")
    if not frame["local_row"].is_monotonic_increasing:
        raise ValueError("membership rows must be ordered by local_row")
    for col, expected in [
        ("source", SOURCE), ("matrix_id", MATRIX_ID), ("operator_index", OPERATOR_INDEX),
        ("partition", PARTITION), ("native_class", NATIVE_CLASS),
    ]:
        if not frame[col].eq(expected).all():
            raise ValueError(f"membership {col} mismatch")
    for row in frame.itertuples(index=False):
        if not isinstance(row.donor_id, str) or not row.donor_id:
            raise ValueError("empty donor_id")
        if not isinstance(row.cell_id, str) or not row.cell_id:
            raise ValueError("empty cell_id")
        key = parse_stable_key_exact(row.stable_key)
        expected = stable_key_from_parts(str(row.matrix_id), int(row.local_row), str(row.cell_id))
        if key != expected:
            raise ValueError("stable_key formula mismatch")


def load_membership(csv_path: str | Path, *, require_frozen_hash: bool = True) -> pd.DataFrame:
    csv_path = Path(csv_path)
    if require_frozen_hash and sha256_file(csv_path) != EXPECTED_CSV_SHA256:
        raise ValueError("membership CSV hash mismatch")
    frame = pd.read_csv(csv_path, dtype={"stable_key":"string"})
    # Preserve exact integers without float conversion.
    frame["stable_key"] = frame["stable_key"].map(parse_stable_key_exact)
    validate_membership_frame(frame)
    return frame


def validate_cells_against_membership(
    membership: pd.DataFrame,
    *,
    matrix_id: Iterable[str], local_row: Iterable[int], cell_id: Iterable[str],
    donor_id: Iterable[str], stable_key: Iterable[object],
) -> None:
    inp = pd.DataFrame({
        "matrix_id": list(matrix_id), "local_row": list(local_row), "cell_id": list(cell_id),
        "donor_id": list(donor_id), "stable_key": list(stable_key),
    })
    if inp.empty:
        raise ValueError("no cells supplied")
    if inp["local_row"].duplicated().any() or inp["stable_key"].duplicated().any():
        raise ValueError("input cell identities must be unique")
    inp["stable_key"] = inp["stable_key"].map(parse_stable_key_exact)
    ref = membership[["matrix_id","local_row","cell_id","donor_id","stable_key"]]
    merged = inp.merge(ref, on=["matrix_id","local_row","cell_id"], how="left", suffixes=("_in","_ref"), validate="one_to_one")
    if merged["donor_id_ref"].isna().any():
        raise ValueError("cell absent from frozen primary membership")
    if not (merged["donor_id_in"] == merged["donor_id_ref"]).all():
        raise ValueError("donor_id does not match frozen membership")
    if not (merged["stable_key_in"] == merged["stable_key_ref"]).all():
        raise ValueError("stable_key does not match frozen membership")


def validate_complete_role_cell_set(membership: pd.DataFrame, *, expected_donors: Iterable[str], donor_id: Iterable[str], stable_key: Iterable[object]) -> None:
    """Require exactly all frozen membership cells for exactly the expected donor set."""
    donors=[str(x) for x in expected_donors]
    if not donors or len(set(donors))!=len(donors) or any(not d for d in donors):
        raise ValueError('expected donor set invalid')
    expected_order=sorted(donors,key=lambda x:x.encode('utf-8'))
    if donors!=expected_order:
        raise ValueError('expected donor set must be canonical UTF-8 order')
    supplied_d=np.asarray([str(x) for x in donor_id],dtype=object)
    supplied_k=[parse_stable_key_exact(x) for x in stable_key]
    if len(supplied_d)!=len(supplied_k) or len(supplied_d)==0:
        raise ValueError('role cell arrays invalid')
    if sorted(set(supplied_d),key=lambda x:x.encode('utf-8'))!=expected_order:
        raise ValueError('supplied donor set does not equal expected role donors')
    if len(set(supplied_k))!=len(supplied_k):
        raise ValueError('duplicate role stable keys')
    ref=membership[membership['donor_id'].astype(str).isin(expected_order)]
    expected_keys={parse_stable_key_exact(x) for x in ref['stable_key'].tolist()}
    if len(ref)==0 or set(supplied_k)!=expected_keys or len(supplied_k)!=len(expected_keys):
        raise ValueError('supplied cells are not the complete frozen membership set for role donors')
