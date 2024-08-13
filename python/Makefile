MAKEFLAGS += -j4 -O
.DEFAULT_GOAL := lint

.PHONY: lint
lint: pylint mypy ruff-format ruff

.PHONY: pylint
pylint:
	pylint .
	@echo ""

.PHONY: mypy
mypy:
	mypy . --config-file pyproject.toml
	@echo ""

.PHONY: ruff-format
ruff-format:
	ruff format --check --diff
	@echo ""

.PHONY: ruff
ruff:
	ruff check
	@echo ""

.PHONY: lint-fix
fix: ruff-fix ruff-format-fix

.PHONY: ruff-fix
ruff-fix:
	ruff check --fix
	@echo ""

.PHONY: ruff-format-fix
ruff-format-fix:
	ruff format
	@echo ""
