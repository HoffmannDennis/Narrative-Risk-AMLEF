# Makefile for 06_NarrativeRisk_LLM_SeverityDistribution.
#
# Default goal: `make demo` -> fetch data (if needed) then execute the notebook.

.PHONY: demo data clean-data test help
.DEFAULT_GOAL := demo

help:
	@echo "06_NarrativeRisk_LLM_SeverityDistribution — per-quantlet Makefile"
	@echo ""
	@echo "Targets:"
	@echo "  make data        Fetch third-party data + regenerate seed-pinned inputs"
	@echo "  make demo        (default) Ensure data, then execute the notebook in place"
	@echo "  make clean-data  Remove fetched/regenerated data (keeps corpus + provenance)"
	@echo "  make test        nbformat smoke check on the notebook"

data:
	@echo "data: nothing to fetch (quantlet has no third-party data deps)"


demo: data
	MPLBACKEND=Agg jupyter nbconvert --to notebook --execute --inplace 06_NarrativeRisk_LLM_SeverityDistribution.ipynb

clean-data:
	@echo "clean-data: removed fetched/regenerated inputs"

test:
	python -c "import nbformat; nbformat.read('06_NarrativeRisk_LLM_SeverityDistribution.ipynb', as_version=4)" && echo "nbformat smoke OK"
