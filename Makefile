.DEFAULT_GOAL := build

.PHONY: all, run

build:
	docker-compose --file Docker/docker-compose.yml build

run:
	 docker run -it docker_stakingrewards /bin/bash

