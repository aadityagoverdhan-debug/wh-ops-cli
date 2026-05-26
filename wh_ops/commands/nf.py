"""Tech NF + Tech Red + WH Red bucket analysis.

Reads sub-bucket values from New_Summary sheet rows.
Overall Red and Tech Red are COMPUTED from sub-buckets.
Reason drilldowns from FC_DOD_RAW_NEW, SCALED to parent Others bucket.
REPROCESS_WH_MH_CHANGE is inside Others — never standalone.
Always prints the summary table. Asks before saving.
"""

import os
from datetime import datetime, date, timedelta
from collections import defaultdict
from wh_ops.utils import serial_to_date, fmt_pct, sf, si
from wh_ops.config import load_config
from wh_ops.auth import get_sheets_service
from wh_ops.sheets import read_sheet, read_sheet_chunked

WH_NF_REASONS = {'NOT_FOUND', 'AUDITED_SKU_NF'}
MAIN_NF_BUCKETS = {'INVENTORY_SYNC_ERROR', 'REDISPATCHED_INVENTORY_OOS'}

ROWS = {
    'Tech_Red_sub': 133,
    'WH_Red': 93,
    'INV_SYNC': 52,
    'REDISP_OOS': 60,
    'STN': 68,
    'NF_Others': 76,
    'EDD_Tech': 141,
    'Redispatch': 157,
    'TR_Others': 165,
    'EDD_WH': 101,
    'Pick': 109,
    'Pack': 117,
    'Dispatch': 125,
}


def get_sheet_val(summary_rows, row_idx, col):
    if row_idx >= len(summary_rows):
        return 0
    row = summary_rows[row_idx]
    if col >= len(row):
        return 0
    try:
        return float(row[col]) * 100
    except (ValueError, TypeError):
        return 0


def get_4cols(summary_rows, row_idx):
    l7_vals = [get_sheet_val(summary_rows, row_idx, c) for c in range(5, 12)]
    return {
        'apr': get_sheet_val(summary_rows, row_idx, 2),
        'apr_mtd': get_sheet_val(summary_rows, row_idx, 3),
        'may': get_sheet_val(summary_rows, row_idx, 4),
        'may_l7': sum(l7_vals) / 7,
    }


def reasons_till_95(reason_dict):
    total = sum(reason_dict.values())
    if total == 0:
        return []
    sorted_r = sorted(reason_dict.items(), key=lambda x: x[1], reverse=True)
    result = []
    cumul = 0
    for r, g in sorted_r:
        result.append(r)
        cumul += g
        if cumul / total >= 0.95:
            break
    return result


def scaled_reason_val(reason_gmv, total_gmv, sheet_others_val):
    """Scale FC_DOD reason so all reasons sum to sheet's Others value."""
    if total_gmv == 0:
        return 0
    return (reason_gmv / total_gmv) * sheet_others_val


def run(args):
    config = load_config(getattr(args, 'config', None))
    sid = config['spreadsheets']['delivery_rate']

    cutoff = date.today() - timedelta(days=1)
    if hasattr(args, 'date') and args.date:
        cutoff = datetime.strptime(args.date, '%Y-%m-%d').date()

    cutoff_day = cutoff.day
    l7_start = max(1, cutoff_day - 6)
    print(f"Running Tech NF + Red analysis till {cutoff.strftime('%Y-%m-%d')}...")

    service = get_sheets_service(config['google_auth']['token_path'])

    # Read New_Summary
    print("Reading New_Summary...")
    summary_rows = read_sheet(service, sid, 'New_Summary!A1:AO200', 'UNFORMATTED_VALUE')
    print(f"  New_Summary: {len(summary_rows)} rows")

    periods = ['apr', 'apr_mtd', 'may', 'may_l7']
    d = {k: get_4cols(summary_rows, v) for k, v in ROWS.items()}

    # COMPUTED rows
    tech_nf = {p: d['INV_SYNC'][p] + d['REDISP_OOS'][p] + d['STN'][p] + d['NF_Others'][p] for p in periods}
    tech_red = {p: tech_nf[p] + d['Tech_Red_sub'][p] for p in periods}
    overall_red = {p: tech_red[p] + d['WH_Red'][p] for p in periods}

    # Read FC_DOD_RAW_NEW
    print("Reading FC_DOD_RAW_NEW (chunked)...")
    fc_data = read_sheet_chunked(service, sid, 'FC_DOD_RAW_NEW', 27000, cols='A:AA')
    for r in fc_data:
        while len(r) < 27:
            r.append('')
    print(f"  FC_DOD: {len(fc_data)} rows")

    # Date serials
    APR_START, APR_END, MAY_START = 46113, 46142, 46143
    TODAY_SERIAL = APR_START + (cutoff - date(2026, 4, 1)).days
    APR_MTD_END = APR_START + cutoff_day - 1
    MAY_L7_START = TODAY_SERIAL - 6

    def in_period(serial, p):
        if p == 'apr': return APR_START <= serial <= APR_END
        elif p == 'apr_mtd': return APR_START <= serial <= APR_MTD_END
        elif p == 'may': return MAY_START <= serial <= TODAY_SERIAL
        elif p == 'may_l7': return MAY_L7_START <= serial <= TODAY_SERIAL
        return False

    # FC_DOD reason aggregation
    nf_oth_gmv = defaultdict(lambda: defaultdict(float))
    nf_oth_total = defaultdict(float)
    tr_oth_gmv = defaultdict(lambda: defaultdict(float))
    tr_oth_total = defaultdict(float)

    for row in fc_data:
        try:
            serial = int(row[0])
        except (ValueError, TypeError):
            continue
        if serial < APR_START or serial > TODAY_SERIAL:
            continue

        reason = str(row[2]) if row[2] else ''
        nf_flag = si(row[4])
        ntf_flag = si(row[5])
        early_rp = si(row[7])
        fulf_flag = si(row[10])
        batch_flag = si(row[12])
        gmv = sf(row[24])

        for p in periods:
            if not in_period(serial, p):
                continue
            if nf_flag == 1 and reason not in WH_NF_REASONS and reason not in MAIN_NF_BUCKETS:
                nf_oth_gmv[p][reason] += gmv
                nf_oth_total[p] += gmv
            if (nf_flag == 0 and ntf_flag == 0 and early_rp == 0 and
                    fulf_flag == 1 and batch_flag == 0 and
                    reason != 'UPDATE_EDD_FOR_UNPACKED_ORDERS'):
                tr_oth_gmv[p][reason] += gmv
                tr_oth_total[p] += gmv

    nf_oth_reasons = reasons_till_95(nf_oth_gmv['may'])
    tr_oth_reasons = reasons_till_95(tr_oth_gmv['may'])

    # --- Output ---
    output = []
    def p(s=''):
        print(s)
        output.append(s)

    def fmt(val):
        return f"{val:.2f}%"

    def line(label, vals):
        return (f"{label:>45} {fmt(vals['apr']):>12} {fmt(vals['apr_mtd']):>12}"
                f" {fmt(vals['may']):>12} {fmt(vals['may_l7']):>12}")

    p('=' * 100)
    p('TECH NF + TECH RED + WH RED \u2014 Bucket Analysis')
    p(f'MTD till {cutoff.strftime("%b %d")} | L7 = {cutoff.strftime("%b")} {l7_start}-{cutoff_day}')
    p('=' * 100)
    p()
    p(f"{'':>45} {'Apr-26':>12} {'Apr_MTD':>12} {'May_MTD':>12} {'May_L7':>12}")
    sep = '\u2500' * 95
    p(sep)
    p(line('Overall Red', overall_red))
    p(line('Tech Red', tech_red))
    p(line('Tech NF', tech_nf))
    p(line('INVENTORY_SYNC_ERROR', d['INV_SYNC']))
    p(line('REDISPATCHED_INVENTORY_OOS', d['REDISP_OOS']))
    p(line('Others', d['NF_Others']))
    p()
    p(f"{'Tech NF Others (till 95%):':>45}")
    for r in nf_oth_reasons:
        vals = {pp: scaled_reason_val(nf_oth_gmv[pp].get(r, 0), nf_oth_total[pp], d['NF_Others'][pp]) for pp in periods}
        p(line(r, vals))
    p()
    p(line('Tech_Red', d['Tech_Red_sub']))
    p(line('EDD changed - w/o batch generation - Tech Led', d['EDD_Tech']))
    p(line('Redispatch', d['Redispatch']))
    p(line('Others', d['TR_Others']))
    p()
    p(f"{'Tech_Red Others (till 95%):':>45}")
    for r in tr_oth_reasons:
        vals = {pp: scaled_reason_val(tr_oth_gmv[pp].get(r, 0), tr_oth_total[pp], d['TR_Others'][pp]) for pp in periods}
        p(line(r, vals))
    p()
    p(line('WH Red', d['WH_Red']))
    p(line('EDD changed - w/o batch generation - WH Led', d['EDD_WH']))
    p(line('Pick Miss', d['Pick']))
    p(line('Pack Miss', d['Pack']))
    p(line('Dispatch Miss_Overall', d['Dispatch']))
    p(sep)

    # Save prompt
    outdir = config['output_dir']
    os.makedirs(outdir, exist_ok=True)
    outfile = os.path.join(outdir, f"tech_nf_red_analysis_{cutoff.strftime('%b%d').lower()}.txt")
    save = input(f"\nSave to {outfile}? (y/n): ").strip().lower()
    if save == 'y':
        with open(outfile, 'w') as f:
            f.write('\n'.join(output) + '\n')
        print(f"Saved to: {outfile}")
    else:
        print("Not saved.")
