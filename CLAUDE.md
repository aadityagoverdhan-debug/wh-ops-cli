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
- Header values come DIRECTLY from New_Summary rows (fractions, multiply by 100)
- Cancellation reason drilldowns from FC_DOD_RAW_NEW, shown till 95% cumulative coverage
- Computes 4 periods: Apr full, Apr MTD, May MTD (till cutoff), May L7 (last 7 days)
- Use `--date YYYY-MM-DD` to set MTD cutoff (default: yesterday)

### Output format (MANDATORY):
Right-aligned labels with 4 value columns. Structure:
```
                                                    Apr-26      Apr_MTD      May_MTD       May_L7
───────────────────────────────────────────────────────────────────────────────────────────────
                                  Overall Red        x.xx%        x.xx%        x.xx%        x.xx%
                                     Tech Red        x.xx%        x.xx%        x.xx%        x.xx%
                                      Tech NF        x.xx%        x.xx%        x.xx%        x.xx%
                         INVENTORY_SYNC_ERROR        ...
                   REDISPATCHED_INVENTORY_OOS        ...
                                       Others        ...
                   Tech NF Others (till 95%):  (cancellation reasons)
                                     Tech_Red        x.xx%        x.xx%        x.xx%        x.xx%
EDD changed - w/o batch generation - Tech Led        ...
                                   Redispatch        ...
                       REPROCESS_WH_MH_CHANGE        ...
                 Tech_Red Others (till 95%):   (cancellation reasons)
                                       WH Red        x.xx%        x.xx%        x.xx%        x.xx%
  EDD changed - w/o batch generation - WH Led        ...
                                    Pick Miss        ...
                                    Pack Miss        ...
                        Dispatch Miss_Overall        ...
───────────────────────────────────────────────────────────────────────────────────────────────
```

### New_Summary key rows (0-indexed in array):
- Overall_RED: 85, WH_Red: 93, Tech_Red_sub: 133
- INV_SYNC: 52, REDISP_OOS: 60, STN_ADMIN_NF: 68, NF_Others: 76
- EDD_Tech: 141, SI_FR: 149, Redispatch: 157, TR_Others: 165, REPROCESS: 173
- EDD_WH: 101, Pick: 109, Pack: 117, Dispatch: 125
- Columns: col2=Apr full, col3=Apr_MTD, col4=May_MTD, cols5-11=last 7 daily (avg for L7)
- Values are fractions — multiply by 100 for %

### Key formulas (DO NOT CHANGE):
- **Tech NF** = INV_SYNC + REDISP_OOS + STN + NF_Others (no direct row)
- **Tech Red** = Tech NF + Tech_Red_sub (no direct row)
- **NF Others reasons** (FC_DOD): nf_flag=1, exclude NOT_FOUND/AUDITED_SKU_NF/INVENTORY_SYNC_ERROR/REDISPATCHED_INVENTORY_OOS
- **Tech_Red Others reasons** (FC_DOD): nf=0, ntf=0, early_rp=0, fulf=1, batch=0, reason!='UPDATE_EDD_FOR_UNPACKED_ORDERS'
- **NEVER use rdp_flag** for Tech Red — wrong metric
- **NEVER use RAW tech_others column** — double counts

## Config
Config is loaded from (in order):
1. `--config` flag
2. `~/.wh-ops/config.yaml`
3. `./config.yaml`
