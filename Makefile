.PHONY: format
format:
	ruff format

.PHONY: lint
lint:
	ruff check

.PHONY: mypy
mypy:
	mypy async_limiter

.PHONY: test
test:
	pytest

.PHONY: test-coverage
test-coverage:
	pytest --cov=async_limiter --cov-report=term --cov-report=html

.PHONY: qa
qa: format lint mypy test
