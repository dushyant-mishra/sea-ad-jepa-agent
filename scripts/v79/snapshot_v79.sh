#!/usr/bin/env bash
# Freeze the V79 code and the small committed inputs it reads at commit <sha> into <dest> (git archive, so the
# snapshot is exactly the commit, never the live tree). Long runs launch from the snapshot; outputs are passed
# explicitly back to the worktree. Usage: snapshot_v79.sh <sha> <dest>
set -eu
SHA="$1"; DEST="$2"
mkdir -p "$DEST"
git archive "$SHA" scripts/v79 results/v78/V78_S174_SHARD_OPERATOR_BRIDGE_V1.json results/v79 \
  docs/agent/BAYESIAN_SYNTHETIC_GEOMETRY_CONTRACT_V1.json results/v77/s174_replay | tar -x -C "$DEST"
echo "$SHA" > "$DEST/SNAPSHOT_COMMIT.txt"
echo "snapshot $SHA -> $DEST"
