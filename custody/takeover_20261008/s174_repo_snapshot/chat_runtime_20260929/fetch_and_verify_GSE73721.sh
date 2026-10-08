#!/usr/bin/env bash
set -euo pipefail

URL="https://ftp.ncbi.nlm.nih.gov/geo/series/GSE73nnn/GSE73721/suppl/GSE73721_Human_and_mouse_table.csv.gz"
OUT="${1:-GSE73721_Human_and_mouse_table.csv.gz}"
EXPECTED="140f376a5162b4d739a0e4224ce5757e7399b24fb2fce1c5f9bf0eb438d2fcef"

curl --fail --location --retry 5 --output "$OUT" "$URL"
ACTUAL="$(sha256sum "$OUT" | awk '{print $1}')"
if [[ "$ACTUAL" != "$EXPECTED" ]]; then
  echo "SHA256 mismatch: expected $EXPECTED got $ACTUAL" >&2
  exit 1
fi
echo "OK $ACTUAL  $OUT"
