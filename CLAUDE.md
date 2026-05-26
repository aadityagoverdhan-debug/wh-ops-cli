# WH-Ops CLI — Claude Code Instructions

## Quick Commands
When the user says these keywords, run the corresponding command:
- **"nf"** → `wh-ops nf` (or `python -m wh_ops.cli nf`)
- **"xb"** → `wh-ops xb`
- **"fm"** → `wh-ops fm`
- **"jit"** → `wh-ops jit`

## CRITICAL RULES:
1. **Always share the summary table in chat** — do NOT just say "saved to file"
2. **Ask before saving** — do not auto-save to file
3. **Overall Red and Tech Red are COMPUTED** from sub-buckets, never read from sheet rows
4. **Reason drilldowns are SCALED** proportionally to match parent Others bucket
5. **REPROCESS_WH_MH_CHANGE is INSIDE Tech_Red Others** — never show as standalone row

## Setup (first time)
```bash
cd ~/Desktop/warehouse-dashboards/wh-ops-cli
pip install -e .
cp config.example.yaml config.yaml
```

## NF Command Details
The `nf` command runs Tech NF + Tech Red + WH Red bucket analysis:
- Reads from Google Sheets: New_Summary (header row values), FC_DOD_RAW_NEW (cancellation reasons)
- Sub-bucket values come DIRECTLY from New_Summary rows (fractions × 100)
- Cancellation reason drilldowns from FC_DOD_RAW_NEW, SCALED to parent Others bucket, till 95%
- 4 periods: Apr full, Apr MTD, May MTD (till cutoff), May L7 (last 7 days)

### Computation rules:
- **Overall Red** = Tech Red + WH Red (COMPUTED)
- **Tech Red** = Tech NF + Tech_Red (COMPUTED)
- **Tech NF** = INV_SYNC + REDISP_OOS + STN + NF_Others (COMPUTED)
- **NF Others reasons**: scaled so sub-reasons sum ≤ parent Others value
- **Tech_Red Others reasons**: scaled so sub-reasons sum ≤ parent Others value
- **NEVER use rdp_flag** — wrong metric
- **NEVER use RAW tech_others column** — double counts

### Output format (MANDATORY):
Right-aligned labels, 4 value columns:
```
                                                    Apr-26      Apr_MTD      May_MTD       May_L7
─────────────────────────────────────────────────────────────────────────────────────────────────
                                  Overall Red        x.xx%  (COMPUTED = Tech Red + WH Red)
                                     Tech Red        x.xx%  (COMPUTED = Tech NF + Tech_Red)
                                      Tech NF        x.xx%  (COMPUTED)
                         INVENTORY_SYNC_ERROR        x.xx%  (row 52)
                   REDISPATCHED_INVENTORY_OOS        x.xx%  (row 60)
                                       Others        x.xx%  (row 76)
                   Tech NF Others (till 95%):        (FC_DOD, SCALED to parent)
                                     Tech_Red        x.xx%  (row 133)
EDD changed - w/o batch generation - Tech Led        x.xx%  (row 141)
                                   Redispatch        x.xx%  (row 157)
                                       Others        x.xx%  (row 165)
                  Tech_Red Others (till 95%):        (FC_DOD, SCALED to parent)
                                       WH Red        x.xx%  (row 93)
  EDD changed - w/o batch generation - WH Led        x.xx%  (row 101)
                                    Pick Miss        x.xx%  (row 109)
                                    Pack Miss        x.xx%  (row 117)
                        Dispatch Miss_Overall        x.xx%  (row 125)
─────────────────────────────────────────────────────────────────────────────────────────────────
```

### New_Summary key rows (0-indexed):
- WH_Red: 93, Tech_Red_sub: 133
- INV_SYNC: 52, REDISP_OOS: 60, STN: 68, NF_Others: 76
- EDD_Tech: 141, Redispatch: 157, TR_Others: 165
- EDD_WH: 101, Pick: 109, Pack: 117, Dispatch: 125
- Columns: col2=Apr, col3=Apr_MTD, col4=May_MTD, cols5-11=daily (avg for L7)
- Values are fractions — multiply by 100

### Reason scaling formula:
```
reason_scaled = (reason_gmv / total_fc_others_gmv) × sheet_Others_value
```
This ensures sub-reasons sum ≤ parent Others bucket (95% coverage).

### FC_DOD filters:
- NF Others: nf_flag=1, exclude NOT_FOUND/AUDITED_SKU_NF/INVENTORY_SYNC_ERROR/REDISPATCHED_INVENTORY_OOS
- Tech_Red Others: nf_flag=0, ntf_flag=0, early_rp=0, fulf_flag=1, batch_flag=0, reason≠UPDATE_EDD_FOR_UNPACKED_ORDERS

## Config
Config is loaded from: `--config` flag → `~/.wh-ops/config.yaml` → `./config.yaml`
