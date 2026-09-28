test:
	python3 -m pytest -q

bench:
	python3 -m pytest benchmarks/ --benchmark-only -q
	python3 -m pytest tests/test_bench_gate.py -q

lint:
	ruff check .
	mypy fix_engine/

ci: lint test bench
