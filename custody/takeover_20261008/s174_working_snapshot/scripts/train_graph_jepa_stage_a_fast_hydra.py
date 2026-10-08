from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import hydra
from omegaconf import DictConfig, OmegaConf

from scripts.train_graph_jepa_stage_a_fast import build_parser, run


@hydra.main(
    version_base=None,
    config_path="../configs/train",
    config_name="graph_jepa_stage_a_fast",
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
        if not hasattr(defaults, key):
            raise KeyError(f"Unknown train_graph_jepa_stage_a_fast argument in Hydra config: {key}")
        setattr(defaults, key, value)
    print("Resolved Hydra training config:")
    print(OmegaConf.to_yaml(cfg, resolve=True))
    run(argparse.Namespace(**vars(defaults)))


if __name__ == "__main__":
    main()
