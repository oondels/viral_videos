.PHONY: build run batch test lint clean help

# Default target
help:
	@echo "viral-videos — available make targets:"
	@echo ""
	@echo "  make build             Build the Docker image"
	@echo "  make run INPUT=<file>  Run single-job pipeline (e.g. INPUT=inputs/examples/job_001.json)"
	@echo "  make batch CSV=<file>  Run batch pipeline     (e.g. CSV=inputs/batch/jobs.csv)"
	@echo "  make test              Run all tests"
	@echo "  make test-unit         Run unit tests only"
	@echo "  make lint              Run ruff linter"
	@echo "  make clean             Remove temp/ files"
	@echo ""
	@echo "See README.md for full documentation."

build:
	docker build -t viral-videos .

run:
	@if [ -z "$(INPUT)" ]; then echo "Usage: make run INPUT=inputs/examples/job_001.json"; exit 1; fi
	docker-compose run --rm app python -m app.main --input $(INPUT)

batch:
	@if [ -z "$(CSV)" ]; then echo "Usage: make batch CSV=inputs/batch/jobs.csv"; exit 1; fi
	docker-compose run --rm app python -m app.main --batch $(CSV)

test:
	docker-compose run --rm app pytest

test-unit:
	docker-compose run --rm app pytest tests/unit/ -v

lint:
	docker-compose run --rm app ruff check app/

clean:
	./scripts/cleanup_temp.sh
