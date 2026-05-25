"""B2B Billing Intelligence Dashboard."""
import os
import subprocess
import sys
from wh_ops.config import load_config

def run(args):
    config = load_config(getattr(args, 'config', None))
    html = os.path.expanduser(config['scripts']['fm_html'])
    if not os.path.exists(html):
        print(f"Dashboard not found: {html}")
        print("Update config.yaml with the correct path to b2b-billing-model.html")
        return
    print(f"Opening B2B Billing Dashboard: {html}")
    if sys.platform == 'darwin':
        subprocess.run(['open', html])
    elif sys.platform == 'linux':
        subprocess.run(['xdg-open', html])
    else:
        import webbrowser
        webbrowser.open(f'file://{html}')
