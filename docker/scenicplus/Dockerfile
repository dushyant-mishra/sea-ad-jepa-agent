FROM mambaorg/micromamba:latest

USER root

RUN apt-get update && apt-get install -y --no-install-recommends \
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
    default-jdk \
    pkg-config \
    procps \
    swig \
    unzip \
    wget \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

USER $MAMBA_USER

RUN micromamba install -y -n base \
    -c conda-forge \
    -c bioconda \
    bedtools \
    cython=0.29.37 \
    ipykernel \
    jupyterlab \
    macs2=2.2.9.1 \
    meme=5.5.9 \
    numpy=1.26.4 \
    pip=24.3.1 \
    python=3.11.8 \
    samtools \
    "setuptools<81" \
    setuptools-scm \
    wheel \
    && micromamba clean --all --yes

USER root

ARG MALLET_VERSION=2.1.0

RUN wget -q -O /tmp/mallet.zip "https://github.com/mimno/Mallet/releases/download/v${MALLET_VERSION}/mallet-${MALLET_VERSION}-bin.zip" \
    && unzip -q /tmp/mallet.zip -d /opt \
    && ln -s /opt/mallet-${MALLET_VERSION} /opt/mallet \
    && rm /tmp/mallet.zip \
    && test -x /opt/mallet/bin/mallet

ENV MALLET_HOME=/opt/mallet
ENV PATH="/opt/mallet/bin:${PATH}"

USER $MAMBA_USER

ARG SCENICPLUS_REF=v1.0a2

RUN git clone --depth 1 --branch ${SCENICPLUS_REF} https://github.com/aertslab/scenicplus.git /tmp/scenicplus \
    && micromamba run -n base python -c "import setuptools, pkg_resources; print('setuptools', setuptools.__version__); print('pkg_resources OK')" \
    && micromamba run -n base python -m pip install --no-cache-dir pysam==0.22.0 \
    && micromamba run -n base python -m pip install --no-build-isolation --no-cache-dir pybedtools==0.9.1 \
    && micromamba run -n base python -m pip install --no-cache-dir "poetry<1.2" poetry-core hatchling packaging \
    && micromamba run -n base python -m pip install --no-build-isolation --no-cache-dir /tmp/scenicplus \
    && rm -rf /tmp/scenicplus

RUN micromamba run -n base python - <<'PY'
import anndata
import pybedtools
import pycisTopic
import pycistarget
import pyscenic
import pysam
import scanpy
import scenicplus
import setuptools

print("setuptools:", setuptools.__version__)
print("scenicplus:", getattr(scenicplus, "__version__", "version unavailable"))
print("pybedtools:", pybedtools.__version__)
print("pysam:", pysam.__version__)
print("SCENIC+ container import test passed")
PY

RUN micromamba run -n base bedtools --version \
    && micromamba run -n base macs2 --version \
    && micromamba run -n base scenicplus --help >/dev/null \
    && /opt/mallet/bin/mallet --help >/dev/null

WORKDIR /workspace

CMD ["/bin/bash"]
