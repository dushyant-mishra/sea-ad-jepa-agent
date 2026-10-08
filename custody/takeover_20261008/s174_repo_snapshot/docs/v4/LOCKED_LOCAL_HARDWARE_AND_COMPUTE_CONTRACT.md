# Locked Local Hardware and Compute Contract

This contract supersedes earlier speculative hardware assumptions for SEA-AD
MRA-JEPA v4. The machine and CUDA-enabled PyTorch runtime are already
validated. No additional hardware preflight or speculative package
replacement is authorized.

The machine-readable authority is
`configs/v4/locked_local_compute_contract.yaml`.

## Fixed Production Envelope

v4 uses one 4,096-gene vocabulary, one donor split, one production seed, one
RNA foundation trajectory, and one active checkpoint lineage. Exact gene
identities are frozen once during Stage81A2. The model uses Perceiver-style
gene-token-to-latent cross-attention with a 48-dimensional gene identity, width
160, 24 latent slots, two latent blocks, four attention heads, a 160-dimensional
cell latent, and dropout 0.10. Full gene-to-gene attention and dimension
searches are forbidden.

Training begins with mixed fp16, microbatch 8, and gradient accumulation to an
effective batch of 256. A CUDA out-of-memory failure permits only the ordered
fallback 8 to 4 to 2 to 1, followed by increased accumulation and then
activation checkpointing. Model dimensions and feature count remain fixed
unless microbatch 1 still fails.

## One Production Trajectory

There is no disposable pilot model. The first 300 optimizer steps belong to
the production run. They check numerical finiteness, gradient boundaries, EMA
behavior, hashes, memory, loading, atomic checkpointing, and successful resume.
At step 300, the same run saves a checkpoint, records throughput and projected
runtime, and continues automatically if every hard check passes. Pathology,
diagnosis, and downstream biological performance cannot enter this gate.

## Runtime Protection

The validated runtime is Python 3.11.15 with PyTorch 2.7.0+cu128 and its CUDA
12.8 runtime. CUDA is available. The driver-reported CUDA capability does not
need to match the PyTorch runtime label. PyTorch, CUDA, AnnData, Scanpy, Zarr,
NumPy, PyTorch Lightning, and PyTorch Geometric may change only after a
concrete reproduced failure demonstrates the need.

Cloud and distributed training are unavailable. Full architecture, feature,
split, and seed sweeps are forbidden. Later graph and spatial controls should
reuse the frozen backbone and train lightweight adapters where required.

## exFAT Safety

The large-data volume uses exFAT. Downloads use temporary `.part` files and
are renamed only after size and SHA-256 verification. A different existing
hash is never overwritten. Prefer relatively few large HDF5 or Parquet shards,
or Zarr with consolidated metadata; avoid millions of small chunks. Source
files remain immutable. Checkpoints are replaced atomically on one volume,
with the latest valid checkpoint and one previous valid checkpoint retained.
Every frozen artifact is verified after writing.

Tracked scientific outputs must use repository-relative logical paths and may
not contain machine-specific absolute paths.

## Data Authority

Downloading the complete required official processed SEA-AD portfolio is
authorized, including MTG and A9/DLPFC snRNA-seq, multiome, snATAC and relevant
fragments, MERFISH expression and coordinates, taxonomy and donor/specimen
metadata, documentation, checksums, and sealed pathology metadata or processed
masks. Raw FASTQ, BAM, and raw optical-image stacks require later explicit
approval.

Acquisition does not assign scientific roles. One approved regional dataset
must remain reserved for frozen replication. The current inventory/acquisition
phase does not authorize model training.
