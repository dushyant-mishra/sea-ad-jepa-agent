#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${PROJECT_DIR:-/mnt/c/Users/dushy/Desktop/Jepa project}"
IMAGE_TAG="${IMAGE_TAG:-scenicplus:1.0a2}"

cd "${PROJECT_DIR}"

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker CLI is not available. Enable Docker Desktop WSL integration for Ubuntu, then retry." >&2
  exit 1
fi

docker info >/dev/null

docker build \
  --no-cache \
  --progress=plain \
  -t "${IMAGE_TAG}" \
  -f docker/scenicplus/Dockerfile \
  docker/scenicplus

docker run --rm "${IMAGE_TAG}" \
  micromamba run -n base python -c \
  "import scenicplus, pycisTopic, pycistarget, pyscenic, scanpy; print('ALL IMPORTS OK')"

docker run --rm "${IMAGE_TAG}" \
  micromamba run -n base scenicplus --help >/dev/null

docker run --rm "${IMAGE_TAG}" \
  micromamba run -n base macs2 --version

docker run --rm "${IMAGE_TAG}" \
  micromamba run -n base meme -version

docker run --rm "${IMAGE_TAG}" sh -c '
  /opt/mallet/bin/mallet train-topics --help TRUE >/tmp/mallet-train-topics-help.txt 2>&1
  rc=$?
  grep -q -- "--num-topics" /tmp/mallet-train-topics-help.txt &&
    { [ "${rc}" -eq 0 ] || [ "${rc}" -eq 255 ]; }
'

docker run --rm "${IMAGE_TAG}" \
  create_cistarget_motif_databases.py --help >/dev/null

docker run --rm "${IMAGE_TAG}" \
  sh -lc 'cbust --help >/dev/null 2>&1 || test $? -eq 1'

docker run --rm "${IMAGE_TAG}" \
  sh -lc 'liftOver 2>&1 | grep -q "liftOver" && bigWigAverageOverBed 2>&1 | grep -q "bigWigAverageOverBed"'

cat <<'EOF'
Stage75E SCENIC+ container verification passed.

Run interactively from the project directory with:
docker run --rm -it --name scenicplus --shm-size=16g --memory=96g --cpus=20 -v "$PWD":/workspace -w /workspace scenicplus:1.0a2
EOF
