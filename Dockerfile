FROM ubuntu:18.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt update && apt install -y --no-install-recommends \
    python3.7 \
    python3.7-distutils \
    gcc-7 \
    g++-7 \
    make \
    ca-certificates \
    gdb \
    && rm -rf /var/lib/apt/lists/*

# gcc 7 기본 설정
RUN update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-7 100 && \
    update-alternatives --install /usr/bin/g++ g++ /usr/bin/g++-7 100

# python 기본 설정
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.7 100

CMD ["/bin/bash"]