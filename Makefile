.DEFAULT_GOAL := build

.PHONY: all, run

build:
	docker-compose --file Docker/docker-compose.yml build

report:
	docker run -it docker_stakingrewards python -m stakingrewards.cli report --plot
