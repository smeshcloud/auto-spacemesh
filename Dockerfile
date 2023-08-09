FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    bash \
    build-essential \
    clinfo \
    curl \
    git \
    git-lfs \
    jq \
    intel-opencl-icd \
    libssl-dev \
    libffi-dev \
    nvidia-cuda-toolkit \
    nvidia-opencl-dev \
    python3-dev \
    python3-pip \
    python3-setuptools \
    python3-venv \
    python3-wheel \
    sudo \
    unzip \
    wget \
    && rm -rf /var/lib/apt/lists/*

RUN wget -q -O - https://raw.githubusercontent.com/canha/golang-tools-install-script/master/goinstall.sh | bash -s -- --version 1.19

WORKDIR /app

COPY . .

RUN pip3 install --trusted-host pypi.python.org -r requirements.txt

RUN git clone https://github.com/spacemeshos/go-spacemesh.git /go-spacemesh
RUN cd /go-spacemesh && PATH=~/.go/bin:$PATH GOPATH=~/.go make install
RUN cd /go-spacemesh && PATH=~/.go/bin:$PATH make build

ENV RUN_CHOICE 1

CMD ["bash", "auto-spacemesh.sh", "--run", "1"]
