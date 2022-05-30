.PHONY: install

SHELL := /bin/bash

install:
	python3 -m venv lib
	source lib/bin/activate
	pip install -r requirements.txt
