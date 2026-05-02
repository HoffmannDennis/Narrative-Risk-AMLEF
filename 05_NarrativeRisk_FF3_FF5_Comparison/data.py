"""Self-contained I/O + on-demand fetchers for the 05_NarrativeRisk_FF3_FF5_Comparison quantlet.

Single-file module: the notebook does `from data import load_corpus, …`.
Each `load_*` checks for the local CSV; if absent, it fetches from upstream
(or regenerates the seed-pinned synthetic outputs) before parsing. Heavy
deps (`yfinance`, `numpy`) are imported INSIDE the fetcher bodies so that
`from data import …` stays cheap when the files are already present.

Run as a CLI from inside the quantlet folder:

    python data.py            # fetch / regenerate only what's missing
    python data.py --force    # re-download / re-generate everything

LICENSE NOTES (for the third-party files this quantlet depends on):

  - prices.csv (Yahoo Finance via yfinance):
      Yahoo's terms of service forbid bulk redistribution of their price
      data; this fetcher re-downloads the data locally on first run so we
      never bundle it. Academic / personal research use only. See
      https://policies.yahoo.com/us/en/yahoo/terms/index.htm.

  - ff_factors.csv (Ken French Data Library, FF5 + UMD monthly):
      Distributed by Prof. Kenneth French at Tuck, free for academic /
      research use.
      Source URLs are stable: https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/.

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
PRICES_PATH = HERE / "prices.csv"
FF_FACTORS_PATH = HERE / "ff_factors.csv"


# ---------------------------------------------------------------------------
# Yahoo Finance prices
# ---------------------------------------------------------------------------

_PRICES_START = "2015-01-01"
_PRICES_END = "2024-12-31"

# Tickers from the top-30 S&P 500 snapshot 2014-12-31.
TICKERS: list[str] = ["AAPL", "XOM", "MSFT", "BRK.B", "GOOGL", "JNJ", "WFC", "WMT", "GE", "PG", "JPM", "META", "CVX", "ORCL", "PFE", "VZ", "BAC", "KO", "INTC", "T", "C", "V", "MRK", "DIS", "IBM", "CMCSA", "GILD", "HD", "CSCO", "MO"]


def _to_yahoo_symbol(ticker: str) -> str:
    """Yahoo uses '-' for share-class suffixes where SEC uses '.' (BRK.B -> BRK-B)."""
    return ticker.replace(".", "-")


def _fetch_prices_df(tickers: list[str], start: str, end: str) -> pd.DataFrame:
    """Download monthly (month-end) adjusted close prices using yfinance."""
    import yfinance as yf  # type: ignore[import]  -- lazy: only loaded when actually fetching

    yahoo_symbols = [_to_yahoo_symbol(t) for t in tickers]
    yahoo_to_canonical = dict(zip(yahoo_symbols, tickers))

    df = yf.download(
        tickers=yahoo_symbols,
        start=start,
        end=end,
        auto_adjust=True,
        progress=False,
        threads=True,
    )

    if hasattr(df.columns, "levels"):
        close = df["Close"].copy()
    else:
        close = df[["Close"]].copy()
        close.columns = yahoo_symbols

    close = close.dropna(how="all")
    close = close.resample("ME").last()
    close = close.rename(columns=yahoo_to_canonical)
    close = close.reindex(columns=tickers)
    return close


def _write_prices_csv(target: Path) -> None:
    """Fetch prices and write to *target* in the canonical wide-form layout."""
    print(f"  fetching {len(TICKERS)} tickers ({_PRICES_START} to {_PRICES_END})...")
    prices_df = _fetch_prices_df(TICKERS, _PRICES_START, _PRICES_END)
    with target.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["date"] + TICKERS)
        for idx, row in prices_df.iterrows():
            date_str = idx.strftime("%Y-%m-%d")
            values = [
                "" if (v != v) else f"{v:.6f}"  # NaN check without importing math
                for v in (row[t] for t in TICKERS)
            ]
            writer.writerow([date_str] + values)
    print(f"  wrote {len(prices_df):,} rows x {len(TICKERS)} tickers -> {target.name}")

# ---------------------------------------------------------------------------
# Ken French FF5+UMD factors
# ---------------------------------------------------------------------------

_FF5_URL = (
    "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/"
    "F-F_Research_Data_5_Factors_2x3_CSV.zip"
)
_UMD_URL = (
    "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/"
    "F-F_Momentum_Factor_CSV.zip"
)
_FF_FILTER_START = 201501  # YYYYMM inclusive
_FF_FILTER_END = 202412    # YYYYMM inclusive


def _download_bytes(url: str, timeout: int = 60) -> bytes:
    """Fetch *url* and return the response body as bytes."""
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "AMLEF-Narratives-Quantlet/1.0 (academic research)"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return response.read()


def _parse_ken_french_csv(zip_bytes: bytes) -> dict[int, dict[str, float]]:
    """Parse a Ken French data ZIP (in-memory bytes) and return monthly factor rows."""
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        csv_name = next(n for n in zf.namelist() if n.endswith(".CSV") or n.endswith(".csv"))
        raw_bytes = zf.read(csv_name)

    text = raw_bytes.decode("latin-1")
    lines = text.splitlines()

    header_idx = None
    col_names: list[str] = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped and not stripped.startswith(";") and "," in stripped:
            parts = [p.strip() for p in stripped.split(",")]
            if parts[0] == "" or parts[0].lower() in ("", "date", "yyyymm"):
                header_idx = i
                col_names = [p for p in parts[1:] if p]
                break

    if header_idx is None:
        raise ValueError("Could not locate header row in Ken French CSV bundle.")

    result: dict[int, dict[str, float]] = {}
    for line in lines[header_idx + 1:]:
        stripped = line.strip()
        if not stripped or stripped.startswith(";"):
            continue
        parts = [p.strip() for p in stripped.split(",")]
        if not parts[0].isdigit():
            continue
        date_int = int(parts[0])
        if date_int < 10000:
            continue
        if date_int < _FF_FILTER_START or date_int > _FF_FILTER_END:
            continue
        values: dict[str, float] = {}
        for name, raw_val in zip(col_names, parts[1:]):
            try:
                values[name.lower()] = float(raw_val) / 100.0
            except ValueError:
                continue
        if values:
            result[date_int] = values

    return result


def _write_ff_factors_csv(target: Path) -> None:
    """Download FF5 + UMD factor zips and write the merged canonical CSV."""
    print(f"  downloading FF5 factors from {_FF5_URL}")
    ff5_data = _parse_ken_french_csv(_download_bytes(_FF5_URL))
    print(f"  downloading UMD (momentum) factors from {_UMD_URL}")
    umd_data = _parse_ken_french_csv(_download_bytes(_UMD_URL))

    months = sorted(set(ff5_data) & set(umd_data))
    if not months:
        raise SystemExit("No overlapping months found between FF5 and UMD data.")

    with target.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["month", "mkt_rf", "smb", "hml", "rmw", "cma", "umd", "rf"])
        for yyyymm in months:
            ff5 = ff5_data[yyyymm]
            umd = umd_data[yyyymm]
            writer.writerow([
                str(yyyymm),
                f"{ff5.get('mkt-rf', float('nan')):.6f}",
                f"{ff5.get('smb', float('nan')):.6f}",
                f"{ff5.get('hml', float('nan')):.6f}",
                f"{ff5.get('rmw', float('nan')):.6f}",
                f"{ff5.get('cma', float('nan')):.6f}",
                f"{umd.get('mom', umd.get('umd', float('nan'))):.6f}",
                f"{ff5.get('rf', float('nan')):.6f}",
            ])
    print(f"  wrote {len(months)} monthly rows -> {target.name}")


# ---------------------------------------------------------------------------
# ensure_*: make sure each input file is on disk (auto-fetch if missing)
# ---------------------------------------------------------------------------


def _ensure_ff_factors(path: Path = FF_FACTORS_PATH) -> None:
    if not path.exists():
        print(f"[ff_factors] {path.name} missing; fetching from Ken French ...")
        _write_ff_factors_csv(path)

def _ensure_prices(path: Path = PRICES_PATH) -> None:
    if not path.exists():
        print(f"[prices] {path.name} missing; fetching from Yahoo Finance ...")
        _write_prices_csv(path)


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


def load_prices(path: Path = PRICES_PATH) -> pd.DataFrame:
    """Load wide-form daily prices, return monthly compounded simple returns long-form: date, firm, ret_m.

    Auto-fetches from Yahoo Finance on first call if prices.csv is missing.
    """
    _ensure_prices(path)
    df = pd.read_csv(path, parse_dates=["date"]).set_index("date").sort_index()
    monthly_close = df.resample("ME").last()
    monthly_ret = monthly_close.pct_change().dropna(how="all")
    long = monthly_ret.reset_index().melt(id_vars="date", var_name="firm", value_name="ret_m")
    return long.dropna()


def load_ff_factors(path: Path = FF_FACTORS_PATH) -> pd.DataFrame:
    """Load Ken French FF5 + UMD monthly factors. Columns: month (period), mkt_rf, smb, hml, rmw, cma, umd, rf.

    Auto-fetches from the Ken French Data Library on first call if the file is missing.
    """
    _ensure_ff_factors(path)
    df = pd.read_csv(path)
    if "month" in df.columns:
        df["month"] = pd.PeriodIndex(df["month"], freq="M")
    return df


# ---------------------------------------------------------------------------
# CLI entry-point: `python data.py [--force]`
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch third-party data + regenerate seed-pinned inputs for "
                    "05_NarrativeRisk_FF3_FF5_Comparison.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="re-fetch / re-generate even if target files already exist",
    )
    args = parser.parse_args()

    print(f"data.py for 05_NarrativeRisk_FF3_FF5_Comparison (writing to {HERE})")

    ff_target = HERE / "ff_factors.csv"
    if args.force or not ff_target.exists():
        print("[ff_factors]")
        _write_ff_factors_csv(ff_target)
    else:
        print(f"[ff_factors] {ff_target.name} present; skipping (use --force to re-fetch)")

    prices_target = HERE / "prices.csv"
    if args.force or not prices_target.exists():
        print("[prices]")
        _write_prices_csv(prices_target)
    else:
        print(f"[prices] {prices_target.name} present; skipping (use --force to re-fetch)")

    print("data.py: done.")


if __name__ == "__main__":
    sys.exit(main())
