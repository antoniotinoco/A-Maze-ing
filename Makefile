PYTHON = python3
MAIN   = a_maze_ing.py
CONFIG = config.txt

.PHONY: install run debug clean lint lint-strict

install:
	python -m pip install -e ".[dev]"

run:
	$(PYTHON) $(MAIN) $(CONFIG)

debug:
	$(PYTHON) -m pdb $(MAIN) $(CONFIG)

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name "dist"       -exec rm -rf {} +

lint:
	flake8 . --exclude=.venv,dist,build
	mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports \
	        --disallow-untyped-defs --check-untyped-defs

lint-strict:
	flake8 . --exclude=.venv,dist,build
	mypy . --strict