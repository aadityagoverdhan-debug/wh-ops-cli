"""XB CDC Warehouse Cost & SLA Dashboard refresh."""
import os
import subprocess
from wh_ops.config import load_config

def run(args):
    config = load_config(getattr(args, 'config', None))
    script = os.path.expanduser(config['scripts']['xb'])
    if not os.path.exists(script):
        print(f"Script not found: {script}")
        print("Update config.yaml with the correct path to refresh_xb_cost_dashboard.py")
        return
    print("Running XB CDC Cost Dashboard refresh...")
    result = subprocess.run(['python3', script], capture_output=False)
    return result.returncode
