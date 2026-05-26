# WH-Ops CLI — Claude Code Instructions

## Quick Commands
When the user says these keywords, run the corresponding command:
- **"nf"** → `wh-ops nf` (or `python -m wh_ops.cli nf`)
- **"xb"** → `wh-ops xb`
- **"fm"** → `wh-ops fm`
- **"jit"** → `wh-ops jit`

## CRITICAL: Always share the summary table in chat
After running `nf`, do NOT just say "saved to file". ALWAYS print the full summary table in the chat response.

## Setup (first time)
```bash
cd ~/Desktop/warehouse-dashboards/wh-ops-cli
pip install -e .
cp config.example.yaml config.yaml
# Edit config.yaml with correct spreadsheet IDs and paths
```

## NF Command Details
The `nf` command runs Tech NF + Tech Red + WH Red bucket analysis:
- Reads from Google Sheets: New_Summary (header row values), FC_DOD_RAW_NEW (cancellation reasons), RAW (base_gmv for FC_DOD %)
- Sub-bucket values come DIRECTLY from New_Summary rows (fractions, multiply by 100)
- **Overall Red and Tech Red are COMPUTED from sub-buckets** (never read from sheet rows)
  - Tech NF = INV_SYNC + REDISP_OOS + STN + NF_Others
  - Tech Red = Tech NF + Tech_Red
  - Overall Red = Tech Red + WH Red
- Cancellation reason drilldowns from FC_DOD_RAW_NEW, shown till 95% cumulative coverage
- Computes 4 periods: Apr full, Apr MTD, May MTD (till cutoff), May L7 (last 7 days)
- Use `--date YYYY-MM-DD` to set MTD cutoff (default: yesterday)

### Output format (MANDATORY):
Right-aligned labels with 4 value columns. Structure:
```
                                                    Apr-26      Apr_MTD      May_MTD       May_L7
───────────────────────────────────────────────────────────────────────────────────────────────
                                  Overall Red   (= Tech Red + WH Red, COMPUTED)
                                     Tech Red   (= Tech NF + Tech_Red, COMPUTED)
                                      Tech NF   (= INV_SYNC + REDISP_OOS + STN + Others)
                         INVENTORY_SYNC_ERROR   (from New_Summary row 52)
                   REDISPATCHED_INVENTORY_OOS   (from New_Summary row 60)
                                       Others   (from New_Summary row 76)
                   Tech NF Others (till 95%):   (from FC_DOD_RAW_NEW)
                                     Tech_Red   (from New_Summary row 133)
EDD changed - w/o batch generation - Tech Led   (from New_Summary row 141)
                                   Redispatch   (from New_Summary row 157)
                       REPROCESS_WH_MH_CHANGE   (from New_Summary row 173)
                 Tech_Red Others (till 95%):    (from FC_DOD_RAW_NEW)
                                       WH Red   (from New_Summary row 93)
  EDD changed - w/o batch generation - WH Led   (from New_Summary row 101)
                                    Pick Miss   (from New_Summary row 109)
                                    Pack Miss   (from New_Summary row 117)
                        Dispatch Miss_Overall   (from New_Summary row 125)
───────────────────────────────────────────────────────────────────────────────────────────────
```

### Key formulas (DO NOT CHANGE):
- **Overall Red** = Tech Red + WH Red (COMPUTED, never from sheet row 85)
- **Tech Red** = Tech NF + Tech_Red (COMPUTED, never from sheet)
- **Tech NF** = INV_SYNC + REDISP_OOS + STN + NF_Others (COMPUTED)
- **NF Others reasons** (FC_DOD): nf_flag=1, exclude NOT_FOUND/AUDITED_SKU_NF/INVENTORY_SYNC_ERROR/REDISPATCHED_INVENTORY_OOS
- **Tech_Red Others reasons** (FC_DOD): nf=0, ntf=0, early_rp=0, fulf=1, batch=0, reason!='UPDATE_EDD_FOR_UNPACKED_ORDERS'
- **NEVER use rdp_flag** for Tech Red — wrong metric
- **NEVER use RAW tech_others column** — double counts

## Config
Config is loaded from (in order):
1. `--config` flag
2. `~/.wh-ops/config.yaml`
3. `./config.yaml`
