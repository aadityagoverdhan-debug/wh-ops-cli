# WH-Ops CLI — Claude Code Instructions

## Quick Commands
When the user says these keywords, run the corresponding command:
- **"nf"** → `wh-ops nf` (or `python -m wh_ops.cli nf`)
- **"xb"** → `wh-ops xb`
- **"fm"** → `wh-ops fm`
- **"jit"** → `wh-ops jit`

## Setup (first time)
```bash
cd ~/Desktop/warehouse-dashboards/wh-ops-cli
pip install -e .
cp config.example.yaml config.yaml
# Edit config.yaml with correct spreadsheet IDs and paths
```

## NF Command Details
The `nf` command runs Tech NF + Tech Red + WH Red bucket analysis:
- Reads from Google Sheets: RAW, FC_DOD_RAW_NEW, New_Summary
- Computes 4 periods: Apr full, Apr MTD, May MTD (till cutoff), May L7 (last 7 days)
- Use `--date YYYY-MM-DD` to set MTD cutoff (default: yesterday)

### Key formulas (DO NOT CHANGE):
- **Tech NF** = nf_flag=1, excluding NOT_FOUND and AUDITED_SKU_NF
- **Tech_Red Others** = FC_DOD fulf formula (nf=0, ntf=0, early_rp=0, fulf=1, batch=0)
- **WH Red sub-buckets** = From RAW sheet columns (pick_miss, pack_miss, dispatch_miss)
- **Redispatch, SI/FR** = From RAW sheet columns (tech_redispatch, tech_si_fr_t)
- **EDD change** = From New_Summary sheet (small, stable values)
- **NEVER use rdp_flag** for Tech Red — wrong metric
- **NEVER use RAW tech_others column** — double counts

## Config
Config is loaded from (in order):
1. `--config` flag
2. `~/.wh-ops/config.yaml`
3. `./config.yaml`
