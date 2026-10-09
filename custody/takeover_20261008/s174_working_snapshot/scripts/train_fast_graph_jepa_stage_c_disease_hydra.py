from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import hydra
from omegaconf import DictConfig, OmegaConf

from scripts.train_fast_graph_jepa_stage_c_disease import build_parser, run


@hydra.main(
    version_base=None,
    config_path="../configs/train",
    config_name="fast_stage_c_supcon",
)
def main(cfg: DictConfig) -> None:
    parser = build_parser()
    defaults = parser.parse_args([])
    values = OmegaConf.to_container(cfg, resolve=True)
    if not isinstance(values, dict):
        raise TypeError("Hydra config must resolve to a mapping")
    for key, value in values.items():
        if key == "hydra":
            continue
        # Hydra uses underscores, argparse uses hyphens internally
        attr_name = key.replace("-", "_")
        if not hasattr(defaults, attr_name):
            raise KeyError(f"Unknown train_fast_graph_jepa_stage_c_disease argument in Hydra config: {key}")
        setattr(defaults, attr_name, value)
    print("Resolved Hydra training config:")
    print(OmegaConf.to_yaml(cfg, resolve=True))
    run(argparse.Namespace(**vars(defaults)))


if __name__ == "__main__":
    main()
