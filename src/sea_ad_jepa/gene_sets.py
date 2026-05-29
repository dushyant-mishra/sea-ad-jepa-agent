from __future__ import annotations


MICROGLIA_GENE_MODULES: dict[str, set[str]] = {
    "plaque_response": {
        "APOE",
        "TREM2",
        "TYROBP",
        "LPL",
        "CST7",
        "CTSD",
        "ITGAX",
        "CLEC7A",
        "AXL",
        "SPP1",
        "GPNMB",
        "LGALS3",
    },
    "complement": {
        "C1QA",
        "C1QB",
        "C1QC",
        "C3",
        "C4A",
        "C4B",
        "CFH",
        "SERPING1",
        "VSIG4",
    },
    "lipid_metabolism": {
        "APOE",
        "LPL",
        "ABCA1",
        "ABCA7",
        "CLU",
        "PLCG2",
        "SORL1",
        "TREM2",
        "MSR1",
    },
    "lysosome_phagocytosis": {
        "CTSD",
        "CTSB",
        "CTSS",
        "LAMP1",
        "LAMP2",
        "LAPTM5",
        "NPC2",
        "CD68",
        "FCGR3A",
        "MERTK",
    },
    "interferon_response": {
        "IFI27",
        "IFI44",
        "IFI44L",
        "IFIT1",
        "IFIT2",
        "IFIT3",
        "ISG15",
        "MX1",
        "OAS1",
        "STAT1",
    },
    "inflammatory_signaling": {
        "NFKBIA",
        "TNF",
        "IL1B",
        "IL6",
        "IL18",
        "IL27RA",
        "CXCL8",
        "CCL2",
        "CCL3",
        "CCL4",
        "TNFRSF11B",
    },
    "at8_associated_first_pass": {
        "PTPRG",
        "S100A4",
        "CHI3L1",
        "DRAM1",
        "TNFRSF11B",
        "IL27RA",
        "CTSD",
        "NFKBIA",
        "SLC6A12",
        "BSG",
    },
}


def module_indices(gene_names: list[str], min_genes: int = 2) -> dict[str, list[int]]:
    gene_to_idx = {gene.upper(): idx for idx, gene in enumerate(gene_names)}
    modules: dict[str, list[int]] = {}
    for name, genes in MICROGLIA_GENE_MODULES.items():
        idx = sorted({gene_to_idx[gene.upper()] for gene in genes if gene.upper() in gene_to_idx})
        if len(idx) >= min_genes:
            modules[name] = idx
    return modules
