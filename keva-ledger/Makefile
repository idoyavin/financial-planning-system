PYTHON ?= python3
VENV   := .venv
BIN    := $(VENV)/bin

.PHONY: help venv install test lint fmt serve summary json clean

help:
	@echo "make install   create .venv and install dev dependencies"
	@echo "make test      run the test suite"
	@echo "make lint      ruff check"
	@echo "make fmt       ruff format"
	@echo "make serve     dashboard on http://127.0.0.1:8000"
	@echo "make summary   headline figures in the terminal"
	@echo "make json      every computed figure as JSON"

$(BIN)/python:
	$(PYTHON) -m venv $(VENV)
	$(BIN)/pip install --quiet --upgrade pip

venv: $(BIN)/python

install: venv
	$(BIN)/pip install --quiet -r requirements-dev.txt

# Run whatever pytest is to hand: the venv's if `make install` has been
# run, otherwise the ambient one. Keeps `make test` working straight out
# of the box.
PYTEST := $(shell [ -x $(BIN)/pytest ] && echo $(BIN)/pytest || echo pytest)
RUNPY  := $(shell [ -x $(BIN)/python ] && echo $(BIN)/python || echo $(PYTHON))

test:
	$(PYTEST)

lint:
	$(RUNPY) -m ruff check src tests

fmt:
	$(RUNPY) -m ruff format src tests

serve:
	PYTHONPATH=src $(RUNPY) -m keva_ledger serve

summary:
	@PYTHONPATH=src $(RUNPY) -m keva_ledger summary

json:
	@PYTHONPATH=src $(RUNPY) -m keva_ledger json

clean:
	rm -rf $(VENV) .pytest_cache
	find . -name __pycache__ -type d -exec rm -rf {} +
