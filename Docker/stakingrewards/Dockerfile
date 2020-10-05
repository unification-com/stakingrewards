FROM debian:stretch-slim

RUN apt-get update && \
    apt-get -y install \
        git \
        vim \
        telnet \
        make build-essential libssl-dev zlib1g-dev libbz2-dev libreadline-dev \
        libsqlite3-dev wget curl llvm libncurses5-dev libncursesw5-dev \
        xz-utils tk-dev unzip

RUN curl -L https://raw.githubusercontent.com/yyuu/pyenv-installer/master/bin/pyenv-installer | bash && \
    /root/.pyenv/bin/pyenv install 3.8.5

RUN mkdir /src
RUN mkdir -p /data/genesis
RUN mkdir -p /data/beacon
RUN mkdir -p /data/register_beacon
RUN mkdir -p /data/register_wrkchain
RUN mkdir -p /data/wrkchain

COPY requirements.txt /src

WORKDIR /src

ENV PATH="/root/.pyenv/versions/3.8.5/bin:${PATH}"
ENV PYTHONPATH /haiku
ENV LC_ALL C.UTF-8
ENV LANG C.UTF-8

RUN pip install -r requirements.txt
RUN gdown https://drive.google.com/uc?id=1gJ9h1qSmUbzDU6xOpm0hw3uZ7_GyA09x -O /data/genesis/genesis.json.zip
RUN cd /data/genesis; unzip genesis.json.zip

COPY src3 /src

RUN echo "python -m stakingrewards.cli report --plot" >> /root/.bash_history && \
    echo "alias ll='ls -la'" >> /root/.bashrc
