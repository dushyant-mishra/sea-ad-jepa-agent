# SCENIC+ v1.0a2 Docker Runtime

This directory contains a pinned Docker runtime for SCENIC+ v1.0a2. It is intended to avoid fragile mixed conda/pip installs for the binary-heavy SCENIC+ stack.

## Included Software

- Python 3.11.8
- SCENIC+ v1.0a2
- pycisTopic
- pycisTarget
- pySCENIC
- Scanpy and Anndata
- Snakemake 8.5.5
- MACS2 2.2.9.1
- MEME 5.5.9
- MALLET 2.1.0
- create_cisTarget_databases helper scripts
- Cluster-Buster `cbust`
- UCSC `liftOver` and `bigWigAverageOverBed`
- bedtools and samtools
- JupyterLab

## Not Included

Large reference resources are intentionally not bundled in the image:

- human cisTarget ranking and score databases
- motif annotation tables
- project datasets
- analysis outputs

Download those resources separately and mount them into the container at runtime.

## Build

```bash
docker build \
  --no-cache \
  --progress=plain \
  -t scenicplus:1.0a2 \
  -f docker/scenicplus/Dockerfile \
  docker/scenicplus
```

## Verify

```bash
docker run --rm scenicplus:1.0a2 \
  micromamba run -n base python -c \
  "import scenicplus, pycisTopic, pycistarget, pyscenic, scanpy; print('ALL IMPORTS OK')"

docker run --rm scenicplus:1.0a2 \
  micromamba run -n base scenicplus --help >/dev/null

docker run --rm scenicplus:1.0a2 \
  micromamba run -n base macs2 --version

docker run --rm scenicplus:1.0a2 \
  micromamba run -n base meme -version

docker run --rm scenicplus:1.0a2 \
  /opt/mallet/bin/mallet train-topics --help >/dev/null

docker run --rm scenicplus:1.0a2 \
  create_cistarget_motif_databases.py --help >/dev/null

docker run --rm scenicplus:1.0a2 \
  sh -lc 'cbust --help >/dev/null 2>&1 || test $? -eq 1'

docker run --rm scenicplus:1.0a2 \
  sh -lc 'liftOver 2>&1 | grep -q "liftOver" && bigWigAverageOverBed 2>&1 | grep -q "bigWigAverageOverBed"'
```

## Run Interactively

```bash
docker run --rm -it \
  --name scenicplus \
  --shm-size=16g \
  -v "$PWD":/workspace \
  -w /workspace \
  scenicplus:1.0a2
```

For larger datasets, add appropriate resource limits, for example:

```bash
docker run --rm -it \
  --name scenicplus \
  --shm-size=16g \
  --memory=96g \
  --cpus=20 \
  -v "$PWD":/workspace \
  -v "$HOME/scenicplus-resources/cistarget":/resources/cistarget:ro \
  -w /workspace \
  scenicplus:1.0a2
```

## Notes For Maintainers

- `setuptools<81` is pinned because `pybedtools==0.9.1` still imports `pkg_resources`.
- `pysam==0.22.0` is installed before `pybedtools==0.9.1`.
- `pybedtools==0.9.1` is installed with `--no-build-isolation`.
- `datrie==0.8.2` and `snakemake==8.5.5` are installed with micromamba to avoid fragile source builds.
- MALLET is installed from the official binary release ZIP; current source checkout layout is not assumed.
- `mallet train-topics --help` is used as the smoke test because `mallet --help` is not a valid top-level command.
- `create_cisTarget_databases`, `cbust`, `liftOver`, and `bigWigAverageOverBed` are included for custom cisTarget database creation, but motif collections, genome FASTA files, and precomputed ranking/score databases are external resources.
