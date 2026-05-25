"""Tech NF + Tech Red + WH Red bucket analysis with cancellation reason breakdown."""

import os
from datetime import datetime, date
from wh_ops.utils import serial_to_date, fmt_pct, fmt_gmv, arrow, sf, si, print_row
from wh_ops.config import load_config
from wh_ops.auth import get_sheets_service
from wh_ops.sheets import read_sheet, read_sheet_chunked

WH_NF_REASONS = {'NOT_FOUND', 'AUDITED_SKU_NF'}
NF_KNOWN_SUB = {'INVENTORY_SYNC_ERROR', 'REDISPATCHED_INVENTORY_OOS', 'INVENTORY_MISSING_REDISPATCH'}
PERIODS = ['Apr-26', 'Apr_MTD', 'May_MTD', 'May_L7']


def filter_by_date(rows, month, min_day=1, max_day=31):
    out = []
    for r in rows:
        dt = serial_to_date(r[0])
        if dt and dt.year == 2026 and dt.month == month and min_day <= dt.day <= max_day:
            out.append(r)
    return out


def compute_from_raw(raw_rows):
    """Compute WH Red sub-buckets and Tech_Red sub-buckets from RAW sheet."""
    base = sum(sf(r[6]) for r in raw_rows)
    if base == 0:
        return None
    return {
        'base': base,
        'pick': sum(sf(r[11]) for r in raw_rows) / base * 100,
        'pack': sum(sf(r[12]) for r in raw_rows) / base * 100,
        'dispatch': sum(sf(r[13]) for r in raw_rows) / base * 100,
        'si_fr': sum(sf(r[14]) for r in raw_rows) / base * 100,
        'redispatch': sum(sf(r[17]) for r in raw_rows) / base * 100,
    }


def compute_from_fc(fc_rows, base):
    """Compute Tech NF reasons + Tech Red Others from FC_DOD_RAW_NEW."""
    tech_nf_by_r = {}
    tr_others_by_r = {}

    for r in fc_rows:
        while len(r) < 27:
            r.append('')
        gmv = sf(r[24])
        reason = r[2]

        # Tech NF: nf_flag=1, exclude WH NF reasons
        if si(r[4]) == 1 and reason not in WH_NF_REASONS:
            tech_nf_by_r[reason] = tech_nf_by_r.get(reason, 0) + gmv

        # Tech Red Others (fulf formula):
        # nf=0, ntf=0, early_rp=0, fulf=1, batch=0, reason!=UPDATE_EDD
        if (si(r[4]) == 0 and si(r[5]) == 0 and si(r[7]) == 0 and
                si(r[10]) == 1 and si(r[12]) == 0 and
                reason != 'UPDATE_EDD_FOR_UNPACKED_ORDERS'):
            tr_others_by_r[reason] = tr_others_by_r.get(reason, 0) + gmv

    tech_nf_total = sum(tech_nf_by_r.values())
    inv_sync = tech_nf_by_r.get('INVENTORY_SYNC_ERROR', 0)
    redisp_oos = sum(tech_nf_by_r.get(r, 0) for r in
                     ['REDISPATCHED_INVENTORY_OOS', 'INVENTORY_MISSING_REDISPATCH'])
    others_nf = tech_nf_total - inv_sync - redisp_oos
    tr_others_total = sum(tr_others_by_r.values())

    nf_oth = {k: v / base * 100 for k, v in tech_nf_by_r.items() if k not in NF_KNOWN_SUB}
    tr_oth = {k: v / base * 100 for k, v in tr_others_by_r.items()}

    return {
        'tech_nf': tech_nf_total / base * 100,
        'inv_sync': inv_sync / base * 100,
        'redisp_oos': redisp_oos / base * 100,
        'others_nf': others_nf / base * 100,
        'tr_others': tr_others_total / base * 100,
        'nf_oth_reasons': nf_oth,
        'tr_oth_reasons': tr_oth,
    }


def get_edd_from_sheet(service, spreadsheet_id):
    """Read EDD change values from New_Summary (small, stable)."""
    try:
        ns = read_sheet(service, spreadsheet_id, 'New_Summary!A20:Y213')
        def pv(v):
            try: return float(str(v).replace('%', ''))
            except: return 0.0
        def get_ns(idx):
            if idx >= len(ns):
                return {p: 0 for p in PERIODS}
            row = ns[idx]
            apr = pv(row[2]) if len(row) > 2 else 0
            apr_mtd = pv(row[3]) if len(row) > 3 else 0
            may_mtd = pv(row[4]) if len(row) > 4 else 0
            l7_vals = [pv(row[i]) if len(row) > i else 0 for i in range(6, 13)]
            l7 = sum(l7_vals) / len(l7_vals) if l7_vals else 0
            return {'Apr-26': apr, 'Apr_MTD': apr_mtd, 'May_MTD': may_mtd, 'May_L7': l7}
        return get_ns(122), get_ns(82)  # EDD Tech (row 142), EDD WH (row 102)
    except Exception:
        # Fallback: small values
        z = {p: 0 for p in PERIODS}
        return z, z


def run(args):
    config = load_config(getattr(args, 'config', None))
    sid = config['spreadsheets']['delivery_rate']

    # Determine cutoff date
    if hasattr(args, 'date') and args.date:
        cutoff = datetime.strptime(args.date, '%Y-%m-%d').date()
    else:
        cutoff = date.today() - __import__('datetime').timedelta(days=1)

    cutoff_day = cutoff.day
    cutoff_month = cutoff.month
    print(f"Running Tech NF + Red analysis till {cutoff.strftime('%Y-%m-%d')}...")
    print(f"Cutoff: May 1-{cutoff_day}, L7 = May {cutoff_day-6}-{cutoff_day}")

    # Auth
    service = get_sheets_service(config['google_auth']['token_path'])

    # Read RAW sheet (1595 rows)
    print("Reading RAW sheet...")
    raw_all = read_sheet(service, sid, 'RAW!A1:W1595', 'UNFORMATTED_VALUE')
    raw_header = raw_all[0] if raw_all else []
    raw_data = raw_all[1:] if len(raw_all) > 1 else []
    # Pad rows
    for r in raw_data:
        while len(r) < 23: r.append('')
    print(f"  RAW: {len(raw_data)} rows")

    # Read FC_DOD_RAW_NEW in chunks
    print("Reading FC_DOD_RAW_NEW sheet (chunked)...")
    fc_data = read_sheet_chunked(service, sid, 'FC_DOD_RAW_NEW', 24026, cols='A:AA')
    for r in fc_data:
        while len(r) < 27: r.append('')
    print(f"  FC_DOD: {len(fc_data)} rows")

    # Read EDD values from New_Summary
    print("Reading EDD change values from New_Summary...")
    edd_tech, edd_wh = get_edd_from_sheet(service, sid)

    # Filter periods
    l7_start = max(1, cutoff_day - 6)
    raw_periods = [
        filter_by_date(raw_data, 4),                          # Apr full
        filter_by_date(raw_data, 4, max_day=cutoff_day),      # Apr MTD
        filter_by_date(raw_data, cutoff_month, max_day=cutoff_day),  # May MTD
        filter_by_date(raw_data, cutoff_month, min_day=l7_start, max_day=cutoff_day),  # L7
    ]
    fc_periods = [
        filter_by_date(fc_data, 4),
        filter_by_date(fc_data, 4, max_day=cutoff_day),
        filter_by_date(fc_data, cutoff_month, max_day=cutoff_day),
        filter_by_date(fc_data, cutoff_month, min_day=l7_start, max_day=cutoff_day),
    ]

    # Compute
    raw_results = [compute_from_raw(rp) for rp in raw_periods]
    fc_results = [compute_from_fc(fp, raw_results[i]['base']) for i, fp in enumerate(fc_periods)]

    def v(key, source='raw'):
        data = raw_results if source == 'raw' else fc_results
        return {p: data[i][key] for i, p in enumerate(PERIODS)}

    # Build buckets
    pick_v = v('pick'); pack_v = v('pack'); dispatch_v = v('dispatch')
    si_fr_v = v('si_fr'); redispatch_v = v('redispatch')
    tech_nf_v = v('tech_nf', 'fc'); inv_sync_v = v('inv_sync', 'fc')
    redisp_oos_v = v('redisp_oos', 'fc'); others_nf_v = v('others_nf', 'fc')
    tr_others_v = v('tr_others', 'fc')

    tech_red_sub = {p: edd_tech[p] + si_fr_v[p] + redispatch_v[p] + tr_others_v[p] for p in PERIODS}
    tech_red_full = {p: tech_nf_v[p] + tech_red_sub[p] for p in PERIODS}
    wh_red = {p: edd_wh[p] + pick_v[p] + pack_v[p] + dispatch_v[p] for p in PERIODS}
    overall_red = {p: tech_red_full[p] + wh_red[p] for p in PERIODS}

    # Print
    output_lines = []
    def p(s=""):
        print(s)
        output_lines.append(s)

    p("=" * 100)
    p(f"TECH NF + TECH RED + WH RED — Bucket Analysis")
    p(f"MTD till {cutoff.strftime('%b %d')} | L7 = {cutoff.strftime('%b')} {l7_start}-{cutoff_day}")
    p("=" * 100)
    hdr = " ".join(f"{p_:>10s}" for p_ in PERIODS)
    p(f"\n  {'':55s} {hdr}")
    p("  " + "─" * 95)

    def row(label, d, indent=0):
        pfx = "  " * indent; name = f"{pfx}{label}"
        vals = " ".join(f"{fmt_pct(d[p_]):>10s}" for p_ in PERIODS)
        p(f"  {name:55s} {vals}")

    row("Overall Red", overall_red)
    p()
    row("Tech Red", tech_red_full)
    p()
    row("Tech NF", tech_nf_v, indent=1)
    row("INVENTORY_SYNC_ERROR", inv_sync_v, indent=2)
    row("REDISPATCHED_INVENTORY_OOS", redisp_oos_v, indent=2)
    row("Others", others_nf_v, indent=2)
    p()
    p("      Tech NF 'Others' — cancellation reason split:")
    all_nf_r = set()
    for i in range(4):
        all_nf_r.update(fc_results[i]['nf_oth_reasons'].keys())
    for reason in sorted(all_nf_r, key=lambda r: -(fc_results[2]['nf_oth_reasons'].get(r, 0))):
        vals = {per: fc_results[i]['nf_oth_reasons'].get(reason, 0) for i, per in enumerate(PERIODS)}
        if max(vals.values()) >= 0.004:
            row(reason, vals, indent=3)
    p()

    row("Tech_Red", tech_red_sub, indent=1)
    row("EDD changed - w/o batch generation - Tech Led", edd_tech, indent=2)
    row("Redispatch", redispatch_v, indent=2)
    row("Others (fulf formula)", tr_others_v, indent=2)
    row("Soft Inventory / Fill rate", si_fr_v, indent=2)
    p()
    p("      Tech_Red 'Others' — cancellation reason split:")
    all_tr_r = set()
    for i in range(4):
        all_tr_r.update(fc_results[i]['tr_oth_reasons'].keys())
    for reason in sorted(all_tr_r, key=lambda r: -(fc_results[2]['tr_oth_reasons'].get(r, 0))):
        vals = {per: fc_results[i]['tr_oth_reasons'].get(reason, 0) for i, per in enumerate(PERIODS)}
        if max(vals.values()) >= 0.003:
            row(reason, vals, indent=3)
    p()

    row("WH Red", wh_red)
    row("EDD changed - w/o batch generation - WH Led", edd_wh, indent=1)
    row("Pick Miss", pick_v, indent=1)
    row("Pack Miss", pack_v, indent=1)
    row("Dispatch Miss_Overall", dispatch_v, indent=1)

    p()
    p("  " + "─" * 95)
    p(f"\n  Verification ({PERIODS[2]}):")
    p(f"  Overall Red ({fmt_pct(overall_red[PERIODS[2]])}) = Tech Red ({fmt_pct(tech_red_full[PERIODS[2]])}) + WH Red ({fmt_pct(wh_red[PERIODS[2]])})")
    p(f"  Tech Red ({fmt_pct(tech_red_full[PERIODS[2]])}) = Tech NF ({fmt_pct(tech_nf_v[PERIODS[2]])}) + Tech_Red ({fmt_pct(tech_red_sub[PERIODS[2]])})")

    # Save to file
    outdir = config['output_dir']
    os.makedirs(outdir, exist_ok=True)
    outfile = os.path.join(outdir, f"tech_nf_red_analysis_{cutoff.strftime('%b%d').lower()}.txt")
    with open(outfile, 'w') as f:
        f.write('\n'.join(output_lines) + '\n')
    p(f"\n  Saved to: {outfile}")
