FROM mambaorg/micromamba:latest

USER root

RUN apt-get update && apt-get install -y --no-install-recommends \
    ant \
    build-essential \
    ca-certificates \
    curl \
    gfortran \
    git \
    libcurl4-openssl-dev \
    libfftw3-dev \
    libgl1 \
    libhdf5-dev \
    libopenblas-dev \
    libsm6 \
    libxext6 \
    libxml2-dev \
    libxrender1 \
    libxslt1-dev \
    openjdk-11-jdk \
    pkg-config \
    procps \
    swig \
    wget \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

USER $MAMBA_USER

RUN micromamba install -y -n base \
    -c conda-forge \
    -c bioconda \
    bedtools \
    ipykernel \
    jupyterlab \
    macs2=2.2.9.1 \
    meme=5.5.9 \
    pip \
    python=3.11.8 \
    samtools \
    && micromamba clean --all --yes

USER root

RUN git clone --depth 1 https://github.com/mimno/Mallet.git /opt/mallet \
    && cd /opt/mallet \
    && ant

ENV MALLET_HOME=/opt/mallet
ENV PATH="/opt/mallet/bin:${PATH}"

USER $MAMBA_USER

ARG SCENICPLUS_REF=v1.0a2

RUN git clone --depth 1 --branch ${SCENICPLUS_REF} https://github.com/aertslab/scenicplus.git /tmp/scenicplus \
    && micromamba run -n base python -m pip install --upgrade pip setuptools wheel \
    && micromamba run -n base python -m pip install /tmp/scenicplus \
    && rm -rf /tmp/scenicplus

RUN micromamba run -n base python - <<'PY'
import anndata
import pycisTopic
import pycistarget
import pyscenic
import scanpy
import scenicplus

print("SCENIC+ container import test passed")
PY

RUN micromamba run -n base scenicplus --help >/dev/null

WORKDIR /workspace

CMD ["/bin/bash"]
