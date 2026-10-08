from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


STRICT_MODULES = {"homeostatic_microglia"}
ELASTIC_MODULES = {
    "at8_associated_first_pass",
    "complement",
    "disease_associated_microglia",
    "inflammatory_signaling",
    "lipid_metabolism",
    "lysosome_phagocytosis",
    "plaque_response",
    "senescence_stress",
    "synapse_pruning",
    "vascular_barrier_myeloid",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a latent-dimension elasticity policy from JEPA latent-module annotations."
    )
    parser.add_argument("--rankings", default="results/tables/all_jepa_umap_variance_rankings.csv")
    parser.add_argument("--representation", default="jepa_latent_umap")
    parser.add_argument("--latent-dim", type=int, default=128)
    parser.add_argument("--default-margin", type=float, default=0.95)
    parser.add_argument("--default-weight", type=float, default=1.0)
    parser.add_argument("--strict-margin", type=float, default=0.985)
    parser.add_argument("--strict-weight", type=float, default=1.5)
    parser.add_argument("--elastic-margin", type=float, default=0.90)
    parser.add_argument("--elastic-weight", type=float, default=0.5)
    parser.add_argument("--out", default="results/tables/latent_elasticity_policy_v1.csv")
    return parser.parse_args()


def annotation_modules(text: str) -> set[str]:
    modules = set()
    for chunk in str(text).split(";"):
        name = chunk.strip().split(" ", 1)[0]
        if name:
            modules.add(name)
    return modules


def main() -> None:
    args = parse_args()
    rankings = pd.read_csv(args.rankings)
    if "representation" in rankings:
        rankings = rankings[rankings["representation"].eq(args.representation)].copy()

    policy = pd.DataFrame(
        {
            "latent_id": list(range(args.latent_dim)),
            "latent_factor": [f"jepa_{idx}" for idx in range(args.latent_dim)],
            "margin": args.default_margin,
            "weight": args.default_weight,
            "policy": "default",
            "top_module_annotations": "",
        }
    )

    for row in rankings.itertuples(index=False):
        latent_id = int(getattr(row, "latent_id"))
        if latent_id < 0 or latent_id >= args.latent_dim:
            continue
        annotations = str(getattr(row, "top_module_annotations", ""))
        modules = annotation_modules(annotations)
        policy.loc[policy["latent_id"].eq(latent_id), "top_module_annotations"] = annotations
        if modules & STRICT_MODULES:
            policy.loc[policy["latent_id"].eq(latent_id), ["margin", "weight", "policy"]] = [
                args.strict_margin,
                args.strict_weight,
                "strict_homeostatic",
            ]
        elif modules & ELASTIC_MODULES:
            policy.loc[policy["latent_id"].eq(latent_id), ["margin", "weight", "policy"]] = [
                args.elastic_margin,
                args.elastic_weight,
                "elastic_reactive",
            ]

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    policy.to_csv(out_path, index=False)
    print(f"Wrote {out_path}")
    print(policy["policy"].value_counts().to_string())


if __name__ == "__main__":
    main()
