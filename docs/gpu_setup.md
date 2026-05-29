# GPU Setup Notes

## What Is Global

The NVIDIA driver is installed globally on the machine.

Current machine status:

```text
GPU: NVIDIA GeForce RTX 3080 Laptop GPU
VRAM: 16 GB
Driver CUDA capability: 12.8
```

This global driver is what allows CUDA-enabled Python packages to talk to the GPU.

## What Is Environment-Specific

Python GPU libraries are usually installed per environment.

For this project, that means PyTorch must be installed inside:

```text
sea-ad-jepa
```

Even though the NVIDIA driver is global, a new conda environment will not automatically have GPU-enabled PyTorch unless PyTorch is installed into that environment.

## Recommended Pattern

Use the global NVIDIA driver plus per-project CUDA-enabled PyTorch wheels.

For this project:

```powershell
conda activate sea-ad-jepa
python -m pip install -r requirements-gpu.txt
python scripts/check_gpu.py
```

The `requirements-gpu.txt` file uses the official PyTorch CUDA 12.8 wheel index:

```text
https://download.pytorch.org/whl/cu128
```

## Why Not Install PyTorch Globally

Installing PyTorch globally into `base` can work, but it is not ideal.

Reasons:

- Different projects may need different PyTorch versions.
- CUDA wheel compatibility can change across versions.
- A broken global `base` environment can affect many projects.
- Reproducibility is easier when each project declares its own dependencies.

## Practical Reuse Across Projects

For future GPU projects, copy this file:

```text
requirements-gpu.txt
```

Then run:

```powershell
python -m pip install -r requirements-gpu.txt
```

inside the active environment.

## Scientific Python Stability

For this project, keep the scientific stack on stable pinned versions:

```text
numpy==1.26.4
scipy>=1.13,<1.14
pandas>=2.2,<2.3
scikit-learn>=1.5,<1.6
```

Very new NumPy/SciPy/scikit-learn builds can trigger native Windows crashes in correlation or linear algebra routines. If `python.exe - Application Error` popups appear, first check these versions:

```powershell
python -c "import numpy, scipy, pandas, sklearn; print(numpy.__version__, scipy.__version__, pandas.__version__, sklearn.__version__)"
```

## Validation

Run:

```powershell
python scripts/check_gpu.py
```

Expected success indicators:

```text
CUDA available: True
GPU: NVIDIA GeForce RTX 3080 Laptop GPU
Test matmul OK.
```
