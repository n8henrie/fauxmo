SHELL := /bin/bash
PYTHON = venv/bin/python3
PWD = $(shell pwd)
GREP := $(shell command -v ggrep || command -v grep)
SED := $(shell command -v gsed || command -v sed)

.PHONY: clean-pyc clean-build docs clean register release clean-docs

help:
	@echo "clean - remove all build, test, coverage and Python artifacts"
	@echo "clean-build - remove build artifacts"
	@echo "clean-pyc - remove Python file artifacts"
	@echo "clean-test - remove test and coverage artifacts"
	@echo "lint - check style with flake8"
	@echo "test - run tests quickly with the default Python"
	@echo "test-all - run tests on every Python version with tox"
	@echo "coverage - check code coverage quickly with the default Python"
	@echo "docs - generate Sphinx HTML documentation, including API docs"
	@echo "release - package and upload a release"
	@echo "dist - package"

clean: clean-build clean-pyc clean-test

clean-build:
	rm -fr build/
	rm -fr dist/
	rm -fr *.egg-info

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean-test:
	rm -fr .tox/
	rm -f .coverage
	rm -fr htmlcov/

lint:
	flake8 src/fauxmo tests

test:
	py.test tests

test-all:
	tox

coverage:
	coverage run --source fauxmo setup.py test
	coverage report -m
	coverage html
	open htmlcov/index.html

clean-docs:
	rm -f docs/fauxmo*.rst
	rm -f docs/modules.rst

docs: clean-docs
	source venv/bin/activate && sphinx-apidoc -o docs/ src/fauxmo
	$(MAKE) -C docs clean
	$(MAKE) -C docs html
	-open docs/_build/html/index.html

register: dist
	twine register dist/*.whl

release: test-all dist
	twine upload dist/*

dist: clean docs
	$(PYTHON) setup.py --long-description | rst2html.py --halt=2
	$(PYTHON) setup.py sdist
	$(PYTHON) setup.py bdist_wheel
	ls -l dist

update-reqs: requirements-test.txt
	@$(GREP) --invert-match --no-filename '^#' requirements*.txt | \
		$(SED) 's|==.*$$||g' | \
		xargs venv/bin/python -m pip install --upgrade; \
	for reqfile in requirements*.txt; do \
		echo "Updating $${reqfile}..."; \
		venv/bin/python -c 'print("\n{:#^80}".format("  Updated reqs below  "))' >> "$${reqfile}"; \
		for lib in $$(venv/bin/pip freeze --all --isolated --quiet | $(GREP) '=='); do \
			if $(GREP) "^$${lib%%=*}==" "$${reqfile}" >/dev/null; then \
				echo "$${lib}" >> "$${reqfile}"; \
			fi; \
		done; \
	done;
