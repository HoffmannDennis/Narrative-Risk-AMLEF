"""Self-contained I/O + on-demand fetchers for the 06_NarrativeRisk_LLM_SeverityDistribution quantlet.

Single-file module: the notebook does `from data import load_corpus, …`.
Each `load_*` checks for the local CSV; if absent, it fetches from upstream
(or regenerates the seed-pinned synthetic outputs) before parsing. Heavy
deps (`yfinance`, `numpy`) are imported INSIDE the fetcher bodies so that
`from data import …` stays cheap when the files are already present.

Run as a CLI from inside the quantlet folder:

    python data.py            # fetch / regenerate only what's missing
    python data.py --force    # re-download / re-generate everything

LICENSE NOTES (for the third-party files this quantlet depends on):

"""
from __future__ import annotations

import argparse
import csv
import gzip
import io
import json
import sys
import urllib.request
import zipfile
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent

# ---------------------------------------------------------------------------
# Path constants
# ---------------------------------------------------------------------------
CORPUS_PATH = HERE / "corpus.ndjson.gz"



# ---------------------------------------------------------------------------
# ensure_*: make sure each input file is on disk (auto-fetch if missing)
# ---------------------------------------------------------------------------



# ---------------------------------------------------------------------------
# Public loaders (auto-fetch on miss)
# ---------------------------------------------------------------------------


def load_corpus(path: Path = CORPUS_PATH) -> pd.DataFrame:
    """Load corpus.ndjson.gz into a long-form DataFrame.

    Schema: firm, year, theme_id, theme_label, severity_0_5.
    The bundled corpus ships with the quantlet; this function just parses it.
    """
    with gzip.open(path, "rt", encoding="utf-8") as f:
        rows = [json.loads(line) for line in f if line.strip()]
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# CLI entry-point: `python data.py [--force]`
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch third-party data + regenerate seed-pinned inputs for "
                    "06_NarrativeRisk_LLM_SeverityDistribution.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="re-fetch / re-generate even if target files already exist",
    )
    args = parser.parse_args()

    print(f"data.py for 06_NarrativeRisk_LLM_SeverityDistribution (writing to {HERE})")

    print("data.py: done.")


if __name__ == "__main__":
    sys.exit(main())
