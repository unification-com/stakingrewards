FROM debian:stretch-slim

RUN apt-get update && \
    apt-get -y install \
        git \
        vim \
        telnet \
        make build-essential libssl-dev zlib1g-dev libbz2-dev libreadline-dev \
        libsqlite3-dev wget curl llvm libncurses5-dev libncursesw5-dev xz-utils tk-dev

RUN curl -L https://raw.githubusercontent.com/yyuu/pyenv-installer/master/bin/pyenv-installer | bash && \
    /root/.pyenv/bin/pyenv install 3.8.5

RUN mkdir /src
RUN mkdir -p /data/genesis
COPY requirements.txt /src

WORKDIR /src

ENV PATH="/root/.pyenv/versions/3.8.5/bin:${PATH}"

ENV LC_ALL C.UTF-8
ENV LANG C.UTF-8
ENV PYTHONPATH /haiku

RUN pip install -r requirements.txt
RUN gdown https://drive.google.com/uc?id=1TEzaiGT5lBvn6OOBXWX24lQy4mYhF528 -O /data/genesis/genesis.json.zip

RUN apt-get -y install unzip
RUN cd /data/genesis; unzip genesis.json.zip
RUN mkdir -p /data/register_beacon
RUN mkdir -p /data/register_wrkchain

COPY src3 /src

EXPOSE 8050

RUN echo "python -m stakingrewards.cli report" >> /root/.bash_history && \
    echo "alias ll='ls -la'" >> /root/.bashrc

