# Makefile for 09_NarrativeRisk_LLM_RollingBeta.
#
# Default goal: `make demo` -> fetch data (if needed) then execute the notebook.

.PHONY: demo data clean-data test help
.DEFAULT_GOAL := demo

help:
	@echo "09_NarrativeRisk_LLM_RollingBeta — per-quantlet Makefile"
	@echo ""
	@echo "Targets:"
	@echo "  make data        Fetch third-party data + regenerate seed-pinned inputs"
	@echo "  make demo        (default) Ensure data, then execute the notebook in place"
	@echo "  make clean-data  Remove fetched/regenerated data (keeps corpus + provenance)"
	@echo "  make test        nbformat smoke check on the notebook"

data:
	python data.py


demo: data
	MPLBACKEND=Agg jupyter nbconvert --to notebook --execute --inplace 09_NarrativeRisk_LLM_RollingBeta.ipynb

clean-data:
	rm -f prices.csv
	rm -f ff_factors.csv
	@echo "clean-data: removed fetched/regenerated inputs"

test:
	python -c "import nbformat; nbformat.read('09_NarrativeRisk_LLM_RollingBeta.ipynb', as_version=4)" && echo "nbformat smoke OK"
