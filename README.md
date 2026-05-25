# wh-ops — Warehouse Operations CLI

A command-line tool for warehouse operations analysis — Tech NF/Red bucket analysis, cost dashboards, B2B billing intelligence, and delivery performance tracking.

## Commands

| Command | Description |
|---------|-------------|
| `wh-ops nf` | Tech NF + Tech Red + WH Red bucket analysis with cancellation reason breakdown |
| `wh-ops xb` | XB CDC Warehouse Cost & SLA Dashboard refresh |
| `wh-ops fm` | Open B2B Billing Intelligence Dashboard |
| `wh-ops jit` | Non-Essentials Delivery Dashboard refresh |

## Installation

```bash
git clone <this-repo>
cd wh-ops-cli
pip install -e .
```

## Setup

### 1. Google Sheets API Access

You need a Google OAuth token to read spreadsheet data. If you use [google-docs-mcp](https://github.com/nicholasq/google-docs-mcp), the token is already at `~/.config/google-docs-mcp/token.json`.

Otherwise, set up OAuth credentials:
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Enable the Google Sheets API
3. Create OAuth 2.0 credentials
4. Download the token and save to `~/.config/google-docs-mcp/token.json`

### 2. Configuration

```bash
cp config.example.yaml config.yaml
# Or copy to ~/.wh-ops/config.yaml for global config
```

Edit `config.yaml` with your spreadsheet IDs and script paths:

```yaml
google_auth:
  token_path: "~/.config/google-docs-mcp/token.json"

spreadsheets:
  delivery_rate: "YOUR_SPREADSHEET_ID"

output_dir: "~/Desktop/warehouse-dashboards/"

scripts:
  xb: "path/to/refresh_xb_cost_dashboard.py"
  jit: "path/to/refresh_delivery_dashboard.py"
  fm_html: "path/to/b2b-billing-model.html"
```

## Usage

### Tech NF + Red Analysis

```bash
# Run with yesterday as cutoff (default)
wh-ops nf

# Run with specific date
wh-ops nf --date 2026-05-24

# Use custom config
wh-ops nf --config /path/to/config.yaml
```

**Output:**
```
                                                       Apr-26    Apr_MTD    May_MTD     May_L7
  ─────────────────────────────────────────────────────────────────────────────────────────
  Overall Red                                           1.33%      1.33%      0.81%      0.51%

  Tech Red                                              0.94%      0.87%      0.55%      0.24%

    Tech NF                                             0.29%      0.30%      0.26%      0.18%
      INVENTORY_SYNC_ERROR                              0.15%      0.15%      0.14%      0.10%
      REDISPATCHED_INVENTORY_OOS                        0.06%      0.06%      0.03%      0.02%
      Others                                            0.08%      0.09%      0.09%      0.06%
        SOFT_INV_FORCE_NF                               0.05%      0.06%      0.07%      0.02%
        ...

    Tech_Red                                            0.66%      0.57%      0.28%      0.06%
      EDD changed - Tech Led                            0.42%      0.49%      0.10%      0.04%
      Redispatch                                        0.06%      0.06%      0.03%      0.02%
      Others (fulf formula)                             0.17%      0.01%      0.15%      0.00%
        REPROCESS_WH_MH_CHANGE                          0.16%      0.00%      0.15%      0.00%

  WH Red                                                0.39%      0.46%      0.26%      0.27%
    EDD changed - WH Led                                0.28%      0.33%      0.03%      0.05%
    Pick Miss                                           0.02%      0.02%      0.01%      0.01%
    Pack Miss                                           0.02%      0.02%      0.05%      0.05%
    Dispatch Miss                                       0.08%      0.08%      0.17%      0.16%
```

### Other Commands

```bash
wh-ops xb      # Refresh XB cost dashboard
wh-ops fm      # Open B2B billing dashboard in browser
wh-ops jit     # Refresh delivery dashboard
```

## Data Sources

| Bucket | Source | Sheet/Column |
|--------|--------|-------------|
| Tech NF | FC_DOD_RAW_NEW | nf_flag=1, excl NOT_FOUND/AUDITED_SKU_NF |
| Tech_Red Others | FC_DOD_RAW_NEW | fulf=1, nf=0, ntf=0, early_rp=0, batch=0 |
| Pick/Pack/Dispatch Miss | RAW | cols 11/12/13 |
| Redispatch | RAW | col 17 (tech_redispatch) |
| SI/Fill Rate | RAW | col 14 (tech_si_fr_t) |
| EDD Change (Tech/WH) | New_Summary | rows 122/82 (small, stable) |

## For Claude Code Users

See `CLAUDE.md` for integration instructions. Just say "nf", "xb", "fm", or "jit" and Claude will run the right command.

## License

Internal tool — Cmunity warehouse operations team.
