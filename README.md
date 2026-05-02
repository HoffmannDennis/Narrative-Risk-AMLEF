# Narrative-Risk-AMLEF

10-quantlet QuantLet family demonstrating LLM-extracted narrative-risk factor methodology on a frozen 30-firm × 10-year × 10-theme corpus of US large-cap 10-K Item 1A risk disclosures (fiscal years 2015-2024).

Headline numbers are **indicative not inferential** at N=30 firms.

## Quantlets

| # | Name | Methodological axis |
|---|------|---------------------|
| 01 | `01_NarrativeRisk_LLM_DisclosureScoring` | Tercile-sort spread + FF5+UMD alpha |
| 02 | `02_NarrativeRisk_LM_DisclosureScoring` | Loughran-McDonald dictionary baseline |
| 03 | `03_NarrativeRisk_LLM_DecileSort` | Decile vs tercile granularity |
| 04 | `04_NarrativeRisk_DeltaSeverity` | Year-over-year change in composite severity |
| 05 | `05_NarrativeRisk_FF3_FF5_Comparison` | FF3 vs FF5+UMD risk model |
| 06 | `06_NarrativeRisk_LLM_SeverityDistribution` | Corpus inspection (no portfolio) |
| 07 | `07_NarrativeRisk_LLM_PostFormation` | One-month skip-formation lag |
| 08 | `08_NarrativeRisk_LLM_IndustryNeutral` | Within-sector demean |
| 09 | `09_NarrativeRisk_LLM_RollingBeta` | 36-month rolling FF5+UMD beta |
| 10 | `10_NarrativeRisk_LLM_LongOnly` | Long-only T3 portfolio (drop short leg) |

## Run any quantlet

Each quantlet is self-contained per the QuantLet self-containment convention (clone → run → done).

```bash
conda env create -f environment.yml
conda activate applied-ml-finance
cd 01_NarrativeRisk_LLM_DisclosureScoring
make demo
```

`make data` fetches Yahoo monthly prices + Ken French FF5+UMD factors (gitignored, never bundled). `make demo` runs `make data` then executes the notebook in place, writing the headline figure and summary CSV.

## Data and provenance

Each quantlet ships:
- `corpus.ndjson.gz` — frozen LLM-extracted severity panel (30 firms × 10 years × 10 themes)
- `provenance.json` — model version, prompt SHA, extraction date, corpus checksum
- `extraction_prompt.md` — verbatim LLM prompt used to produce the corpus
- `Metainfo.txt` — QuantLet metadata

Quantlet 02 additionally bundles two third-party files redistributed under their respective open-access terms:
- the **Loughran-McDonald master dictionary** (`lm_dictionary.csv`), authored by Loughran & McDonald (2011) and distributed via the SRAF resource at the University of Notre Dame, which permits academic use
- the **cached Item 1A texts** (`all_texts_v2.json.gz`), sourced from public SEC EDGAR filings

## License

MIT (see LICENSE).
