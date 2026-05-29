from __future__ import annotations

import platform

import torch


def main() -> None:
    print(f"Python: {platform.python_version()}")
    print(f"PyTorch: {torch.__version__}")
    print(f"PyTorch CUDA build: {torch.version.cuda}")
    print(f"CUDA available: {torch.cuda.is_available()}")

    if not torch.cuda.is_available():
        print("No CUDA GPU is visible to PyTorch.")
        return

    device = torch.device("cuda:0")
    props = torch.cuda.get_device_properties(device)
    total_gb = props.total_memory / 1024**3
    print(f"GPU: {props.name}")
    print(f"Compute capability: {props.major}.{props.minor}")
    print(f"Total VRAM: {total_gb:.2f} GB")

    x = torch.randn((2048, 2048), device=device)
    y = x @ x.T
    torch.cuda.synchronize()
    print(f"Test matmul OK. Result mean: {y.mean().item():.6f}")


if __name__ == "__main__":
    main()
