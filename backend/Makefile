.PHONY: install run build package deploy clean lint venv

VENV_DIR ?= .venv
PYTHON ?= python3

ifeq ($(OS),Windows_NT)
VENV_BIN := $(VENV_DIR)/Scripts
else
VENV_BIN := $(VENV_DIR)/bin
endif

VENV_PYTHON := $(VENV_BIN)/python
PIP := $(VENV_PYTHON) -m pip

venv: $(VENV_PYTHON)

$(VENV_PYTHON):
	$(PYTHON) -m venv $(VENV_DIR)

install: venv
	$(PIP) install -r requirements.txt

run: install
	$(VENV_PYTHON) lambda_function.py

build: venv
	mkdir -p build
	$(PIP) install --target build -r requirements.txt
	cp -r lambda_function.py utils build/

package: build
	cd build && zip -r ../lambda_package.zip .

deploy: package
	aws lambda update-function-code \
	--function-name mechanic-ai-lambda \
	--zip-file fileb://lambda_package.zip

clean:
	rm -rf build lambda_package.zip $(VENV_DIR)

lint: install
	$(VENV_PYTHON) -m compileall lambda_function.py utils
