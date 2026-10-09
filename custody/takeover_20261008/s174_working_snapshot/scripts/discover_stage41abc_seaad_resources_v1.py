from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from run_stage41abc_seaad_safe_feature_download_analyze_benchmark_v1 import discover_resources, load_cfg, write_csv


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    cfg = load_cfg(args.config)
    pages, links = discover_resources(cfg)
    write_csv(pages, cfg["outputs"]["resource_page_inventory"])
    write_csv(links, cfg["outputs"]["discovered_download_links"])
    print(f"resource_pages_fetched={int(pages['fetch_success'].sum())}/{len(pages)}")
    print(f"download_links_discovered={len(links)}")


if __name__ == "__main__":
    main()
