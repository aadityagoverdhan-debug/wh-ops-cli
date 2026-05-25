from datetime import datetime, timedelta

EXCEL_BASE = datetime(1899, 12, 30)

def serial_to_date(serial):
    try:
        return EXCEL_BASE + timedelta(days=int(float(serial)))
    except:
        return None

def fmt_gmv(v):
    if v >= 10000000: return f"Rs{v/10000000:.2f}Cr"
    if v >= 100000: return f"Rs{v/100000:.2f}L"
    if v >= 1000: return f"Rs{v/1000:.1f}K"
    return f"Rs{v:.0f}"

def fmt_pct(v):
    return f"{v:.2f}%"

def arrow(fp, lp):
    if fp == 0 and lp == 0: return "→"
    if fp == 0 and lp > 0: return "↑↑"
    if lp > fp * 2: return "↑↑"
    if lp > fp * 1.2: return "↑"
    if lp < fp * 0.8: return "↓"
    return "→"

def sf(v):
    try: return float(str(v).replace(',', ''))
    except: return 0.0

def si(v):
    try: return int(float(str(v).replace(',', '')))
    except: return 0

def print_row(label, d, periods, indent=0):
    pfx = "  " * indent
    name = f"{pfx}{label}"
    vals = " ".join(f"{fmt_pct(d[p]):>10s}" for p in periods)
    print(f"  {name:55s} {vals}")
