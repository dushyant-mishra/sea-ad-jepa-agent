#!/usr/bin/env bash
# V69: PROSPECTIVE proof fixture for cross-route score reuse.
#
# QUESTION. Is the cisTarget CRM score of a region for a motif independent of which
# OTHER regions are present in the same FASTA? If it is, Route A and Route B regions
# can be scored ONCE over their union and each route's rows selected afterwards,
# cutting the dominant cost roughly in half. If it is not, the optimisation is void.
#
# WHY IT IS PLAUSIBLE BUT MUST BE PROVEN. Cluster-Buster is invoked once per motif as
#   cbust -f 4 -c 0.0 -r 10000 -b <bg_padding> -t 1 <motif> <fasta>
# with a PER-SEQUENCE padded background, and no global normalisation flag. That makes
# independence likely. "Likely" is not a proof, and a wrong assumption here would be
# baked into every downstream eRegulon claim.
#
# DESIGN, frozen before the first run.
#   A  = deterministic slice of the Route-A region universe        (N regions)
#   B  = a DISJOINT deterministic slice of the same universe       (N regions)
#   U  = A union B, in a DIFFERENT order from either               (2N regions)
#   Score the SAME motif batch on A, on B and on U.
#   Subset U's scores back to A's region names and to B's.
#   REQUIRE: subset(U -> A) equals the independent A run, matched BY REGION NAME, and
#   likewise for B.
#
# PASS CRITERION, declared in advance: exact bitwise equality of the score matrices
# after aligning on region name and motif name. Scores are deterministic; only the
# RANKINGS step takes a seed, and rankings are deliberately NOT part of this claim --
# ranking is a cross-region operation and is therefore expected to be route-dependent.
#
# U is deliberately ordered differently from A and B so that an implementation which
# happened to be position-dependent cannot pass by accident.
set -euo pipefail

N="${1:-2000}"
NMOTIFS="${2:-8}"
OUT="${3:-/scratch/union_equivalence}"
RES=/data/resources
FASTA="$RES/hg38.analysisSet.fa"
MOTIF_DIR="$RES/v10nr_clust_public/singletons"
BED="/data/routeA/V69_ROUTE_A_SUBMITTED_PEAKS_REGION_UNIVERSE.bed"
BG_PADDING=1000

mkdir -p "$OUT"
cd "$OUT"

echo "=== [1/5] deterministic disjoint region slices (N=$N each) ==="
# A = rows 1..N ; B = rows (N+1)..2N  -- disjoint by construction.
head -n "$N"            "$BED" > A.bed
sed -n "$((N+1)),$((2*N))p" "$BED" > B.bed
# U = A + B, then REVERSED, so U's order matches neither A nor B.
cat A.bed B.bed | tac > U.bed
wc -l A.bed B.bed U.bed
# prove disjointness rather than assume it
OVERLAP=$(comm -12 <(cut -f4 A.bed | sort) <(cut -f4 B.bed | sort) | wc -l)
echo "A/B shared region names: $OVERLAP"
if [ "$OVERLAP" -ne 0 ]; then
  echo "FAIL__SLICES_NOT_DISJOINT" >&2; exit 3
fi

echo "=== [2/5] motif batch (identical for all three runs) ==="
# Materialise the full sorted list first. Piping into `head` under `set -o pipefail`
# kills the upstream `sort` with SIGPIPE and aborts the script (exit 141).
ls "$MOTIF_DIR" | sed 's/\.cb$//' | sort > motifs.all.lst
head -n "$NMOTIFS" motifs.all.lst > motifs.lst
sha256sum motifs.lst | tee motifs.lst.sha256

echo "=== [3/5] region FASTAs ==="
for s in A B U; do
  micromamba run -n base bash \
    /opt/create_cisTarget_databases/create_fasta_with_padded_bg_from_bed.sh \
    "$FASTA" "$RES/hg38.analysisSet.chrom.sizes" "$s.bed" "$s.fa" "$BG_PADDING" 1
  echo "$s: $(grep -c '^>' "$s.fa") sequences from $(wc -l < "$s.bed") regions"
done

echo "=== [4/5] score each set with the SAME motifs and parameters ==="
for s in A B U; do
  micromamba run -n base python \
    /opt/create_cisTarget_databases/create_cistarget_motif_databases.py \
    -f "$s.fa" -M "$MOTIF_DIR" -m motifs.lst -o "DB_$s" \
    -c /usr/local/bin/cbust -t 4 > "score_$s.log" 2>&1
  echo "$s scored"
done

echo "=== [5/5] equivalence test ==="
micromamba run -n base python - <<'PY'
import glob, hashlib, json, sys
import pandas as pd

def load(prefix):
    hits = glob.glob(f"{prefix}.motifs_vs_regions.scores.feather")
    if not hits:
        hits = glob.glob(f"{prefix}*motifs_vs_regions.scores.feather")
    df = pd.read_feather(hits[0])
    # rows = motifs, columns = regions (plus an index column)
    idx = df.columns[-1] if df.columns[-1].startswith("motif") else df.columns[0]
    df = df.set_index(idx)
    return df.sort_index()

A, B, U = load("DB_A"), load("DB_B"), load("DB_U")
out = {"schema": "V69_UNION_REGION_SCORE_EQUIVALENCE_V1"}
out["shapes"] = {"A": list(A.shape), "B": list(B.shape), "U": list(U.shape)}
out["motif_axis_identical_A_U"] = bool(list(A.index) == list(U.index))
out["motif_axis_identical_B_U"] = bool(list(B.index) == list(U.index))

res = {}
ok = True
for name, df in (("A", A), ("B", B)):
    cols = [c for c in df.columns]
    missing = [c for c in cols if c not in U.columns]
    if missing:
        res[name] = {"status": "FAIL__REGIONS_MISSING_FROM_UNION",
                     "n_missing": len(missing), "examples": missing[:5]}
        ok = False
        continue
    sub = U.loc[df.index, cols]          # align on BOTH axes by NAME
    equal = bool(sub.equals(df))
    maxabs = float((sub.to_numpy() - df.to_numpy()).__abs__().max())
    res[name] = {
        "status": "PASS__BITWISE_IDENTICAL" if equal else "FAIL__SCORES_DIFFER",
        "bitwise_identical": equal,
        "max_abs_difference": maxabs,
        "n_regions_compared": len(cols),
        "n_motifs_compared": int(df.shape[0]),
        "independent_run_sha256": hashlib.sha256(
            pd.util.hash_pandas_object(df, index=True).values.tobytes()).hexdigest(),
        "union_subset_sha256": hashlib.sha256(
            pd.util.hash_pandas_object(sub, index=True).values.tobytes()).hexdigest(),
    }
    ok = ok and equal

out["per_set"] = res
out["verdict"] = ("UNION_SCORING_IS_SAFE__SCORES_ARE_REGION_SET_INDEPENDENT" if ok
                  else "UNION_SCORING_REJECTED__SCORES_DEPEND_ON_REGION_SET")
out["scope_of_claim"] = ("This proves SCORE independence only. RANKINGS are a "
                         "cross-region operation and are expected to be route-"
                         "dependent; they are built per route and are NOT covered.")
print(json.dumps(out, indent=2))
open("V69_UNION_REGION_SCORE_EQUIVALENCE_V1.json", "w").write(json.dumps(out, indent=2) + "\n")
sys.exit(0 if ok else 4)
PY
echo "=== EQUIVALENCE FIXTURE FINISHED ==="
