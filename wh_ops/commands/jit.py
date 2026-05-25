"""Non-Essentials Delivery Dashboard refresh."""
import os
import subprocess
from wh_ops.config import load_config

def run(args):
    config = load_config(getattr(args, 'config', None))
    script = os.path.expanduser(config['scripts']['jit'])
    if not os.path.exists(script):
        print(f"Script not found: {script}")
        print("Update config.yaml with the correct path to the delivery dashboard refresh script")
        return
    print("Running Non-Essentials Delivery Dashboard refresh...")
    result = subprocess.run(['python3', script], capture_output=False)
    return result.returncode
