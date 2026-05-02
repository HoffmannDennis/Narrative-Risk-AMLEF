---
prompt_id: extract_v1
prompt_version: 1.0.0
schema_version: 1.0.0
target_model: claude-sonnet-4-6
expected_severity_range: 0-5
expected_themes: 10
---

# Risk Disclosure Extraction Prompt

## Task

You are a financial-disclosure analyst. You will receive a single passage from a 10-K filing (Item 1A, "Risk Factors"). Your job is to score the passage against a fixed 10-theme taxonomy and return a single JSON object. No prose. No explanation. JSON only.

---

## Input

A verbatim excerpt from a 10-K Item 1A "Risk Factors" section. The text discusses operational, financial, legal, and strategic risks as disclosed to shareholders.

---

## Theme Taxonomy (fixed — do not add, remove, or rename themes)

Score the passage against exactly these 10 themes:

| theme_id | theme_label     | What counts as evidence                                                                                      |
|----------|-----------------|--------------------------------------------------------------------------------------------------------------|
| T01      | supply-chain    | Risks tied to procurement, supplier concentration, logistics disruption, inventory management, or sourcing.  |
| T02      | regulatory      | Risks from government regulation, licensing, compliance obligations, enforcement actions, or policy changes. |
| T03      | cyber           | Risks from data breaches, information-security failures, ransomware, IT outages, or privacy violations.      |
| T04      | macroeconomic   | Risks from recessions, interest-rate changes, inflation, foreign-exchange exposure, or broad economic cycles. |
| T05      | climate         | Risks from physical climate events, transition to low-carbon economy, ESG disclosure requirements, or natural disasters. |
| T06      | competition     | Risks from competitive intensity, market-share loss, pricing pressure, new entrants, or technological substitution by rivals. |
| T07      | litigation      | Risks from pending or threatened lawsuits, regulatory investigations, intellectual-property disputes, or class-action exposure. |
| T08      | talent          | Risks from employee recruitment, retention, key-person dependency, labor relations, or workforce shortages.  |
| T09      | input-cost      | Risks from raw-material price volatility, energy costs, commodity exposure, or supplier price increases.     |
| T10      | technology      | Risks from rapid technological change, product obsolescence, R&D investment uncertainty, or failure to innovate. |

---

## Severity Scale (0-5)

Assign an integer severity score in the range 0-5 (that is, 0 through 5) for each theme:

| Score | Meaning                                                               |
|-------|-----------------------------------------------------------------------|
| 0     | Not mentioned or explicitly disclaimed in the passage.                |
| 1     | Minor or boilerplate language only; no firm-specific detail.          |
| 2     | Routine acknowledgment with limited disclosure; generic but present.  |
| 3     | Substantive discussion with named exposures, specific risk factors.   |
| 4     | Detailed quantification or explicitly flagged as a material concern.  |
| 5     | Highlighted as a top-tier risk with sustained, detailed discussion.   |

The scale is 0-5 inclusive (zero through five). Do not use fractional scores. Zero is a valid and required score when a theme is absent.

---

## Evidence Quote Rules

- When severity > 0: provide a verbatim substring from the input passage (copy exact wording, do not paraphrase). Truncate at 200 characters.
- When severity = 0: set `evidence_quote` to the empty string `""`.

---

## Output Schema

Return exactly one JSON object with this structure. No text before or after the JSON.

```json
{
  "firm": "<TICKER>",
  "year": <YYYY>,
  "themes": [
    {"theme_id": "T01", "theme_label": "supply-chain",  "severity_0_5": 0, "evidence_quote": ""},
    {"theme_id": "T02", "theme_label": "regulatory",    "severity_0_5": 0, "evidence_quote": ""},
    {"theme_id": "T03", "theme_label": "cyber",         "severity_0_5": 0, "evidence_quote": ""},
    {"theme_id": "T04", "theme_label": "macroeconomic", "severity_0_5": 0, "evidence_quote": ""},
    {"theme_id": "T05", "theme_label": "climate",       "severity_0_5": 0, "evidence_quote": ""},
    {"theme_id": "T06", "theme_label": "competition",   "severity_0_5": 0, "evidence_quote": ""},
    {"theme_id": "T07", "theme_label": "litigation",    "severity_0_5": 0, "evidence_quote": ""},
    {"theme_id": "T08", "theme_label": "talent",        "severity_0_5": 0, "evidence_quote": ""},
    {"theme_id": "T09", "theme_label": "input-cost",    "severity_0_5": 0, "evidence_quote": ""},
    {"theme_id": "T10", "theme_label": "technology",    "severity_0_5": 0, "evidence_quote": ""}
  ]
}
```

### Constraints on the output

- `themes` must contain all 10 entries, one per theme, in the order T01 through T10.
- `severity_0_5` must be an integer in 0-5.
- `evidence_quote` must be a verbatim substring of the input (or `""` for severity 0).
- `evidence_quote` must not exceed 200 characters.
- `firm` is the company ticker (e.g., `"AAPL"`).
- `year` is the fiscal year as a four-digit integer (e.g., `2023`).

### Example (non-authoritative — illustrates format only)

```json
{
  "firm": "AAPL",
  "year": 2023,
  "themes": [
    {"theme_id": "T01", "theme_label": "supply-chain",  "severity_0_5": 4, "evidence_quote": "substantially all of our manufacturing is performed in whole or in part by outsourcing partners located primarily in China"},
    {"theme_id": "T02", "theme_label": "regulatory",    "severity_0_5": 3, "evidence_quote": "we are subject to complex and changing laws and regulations worldwide"},
    {"theme_id": "T03", "theme_label": "cyber",         "severity_0_5": 3, "evidence_quote": "a breach of our security systems could expose our customers' data"},
    {"theme_id": "T04", "theme_label": "macroeconomic", "severity_0_5": 2, "evidence_quote": "global economic conditions could adversely affect our business"},
    {"theme_id": "T05", "theme_label": "climate",       "severity_0_5": 1, "evidence_quote": "climate change may increase the frequency and severity of extreme weather"},
    {"theme_id": "T06", "theme_label": "competition",   "severity_0_5": 4, "evidence_quote": "the markets for our products and services are highly competitive"},
    {"theme_id": "T07", "theme_label": "litigation",    "severity_0_5": 2, "evidence_quote": "we are subject to various claims and litigation"},
    {"theme_id": "T08", "theme_label": "talent",        "severity_0_5": 3, "evidence_quote": "our success depends on attracting and retaining qualified personnel"},
    {"theme_id": "T09", "theme_label": "input-cost",    "severity_0_5": 0, "evidence_quote": ""},
    {"theme_id": "T10", "theme_label": "technology",    "severity_0_5": 5, "evidence_quote": "rapid technological change and the introduction of new products and services could render our existing products obsolete"}
  ]
}
```

---

## Scoring Rules

1. Read the entire passage before scoring any theme.
2. Score only what is stated in the passage. Do not infer risks not discussed.
3. Themes that are clearly absent receive severity 0 and an empty evidence_quote.
4. A theme receives severity 1 only if the passage contains at least one sentence referencing it, even if boilerplate.
5. Severity 3 or above requires named or firm-specific exposure (not generic industry language alone).
6. Severity 5 requires the theme to appear in multiple paragraphs or to be explicitly called out as a primary or leading risk.
7. Do not average across themes. Score each independently.
8. Return exactly one JSON object. No markdown fences, no prose. Begin your response with `{` and end with `}`.
