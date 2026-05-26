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

## NF Command Details
5 columns: Apr-26, Apr_MTD, May_MTD, May_L7, Last Day (col5 from New_Summary)

### Section order (MANDATORY):
1. Overall Red (computed)
2. WH Red + sub-buckets (EDD WH, Pick, Pack, Dispatch)
3. Tech Red (computed)
4. Tech NF + sub-buckets (INV_SYNC, REDISP_OOS, Others) + NF Others reasons (95%)
5. Tech_Red + sub-buckets (EDD Tech, Redispatch, Others) + Tech_Red Others reasons (95%)
6. Verification line

### Output format:
```
                                                    Apr-26      Apr_MTD      May_MTD       May_L7       May DD
───────────────────────────────────────────────────────────────────────────────────────────────────────────
                                  Overall Red        (COMPUTED)

                                       WH Red        (row 93)
  EDD changed - w/o batch generation - WH Led        (row 101)
                                    Pick Miss        (row 109)
                                    Pack Miss        (row 117)
                        Dispatch Miss_Overall        (row 125)

                                     Tech Red        (COMPUTED)

                                      Tech NF        (COMPUTED)
                         INVENTORY_SYNC_ERROR        (row 52)
                   REDISPATCHED_INVENTORY_OOS        (row 60)
                                       Others        (row 76)
                   Tech NF Others (till 95%):        (FC_DOD, SCALED)

                                     Tech_Red        (row 133)
EDD changed - w/o batch generation - Tech Led        (row 141)
                                   Redispatch        (row 157)
                                       Others        (row 165)
                  Tech_Red Others (till 95%):        (FC_DOD, SCALED)
───────────────────────────────────────────────────────────────────────────────────────────────────────────
Verification
```

### Computation rules:
- **Overall Red** = Tech Red + WH Red (COMPUTED)
- **Tech Red** = Tech NF + Tech_Red (COMPUTED)
- **Tech NF** = INV_SYNC + REDISP_OOS + STN + NF_Others (COMPUTED)
- **Reason scaling**: `reason_scaled = (reason_gmv / total_fc_others_gmv) × sheet_Others_value`
- **NEVER use rdp_flag** — wrong metric
- **NEVER use RAW tech_others column** — double counts

### New_Summary key rows (0-indexed):
- WH_Red: 93, Tech_Red_sub: 133
- INV_SYNC: 52, REDISP_OOS: 60, STN: 68, NF_Others: 76
- EDD_Tech: 141, Redispatch: 157, TR_Others: 165
- EDD_WH: 101, Pick: 109, Pack: 117, Dispatch: 125
- Columns: col2=Apr, col3=Apr_MTD, col4=May_MTD, col5=Last Day, cols5-11 avg=L7
- Values are fractions — multiply by 100

### FC_DOD filters:
- NF Others: nf_flag=1, exclude NOT_FOUND/AUDITED_SKU_NF/INVENTORY_SYNC_ERROR/REDISPATCHED_INVENTORY_OOS
- Tech_Red Others: nf=0, ntf=0, early_rp=0, fulf=1, batch=0, reason≠UPDATE_EDD_FOR_UNPACKED_ORDERS

## Config
Config is loaded from: `--config` flag → `~/.wh-ops/config.yaml` → `./config.yaml`
