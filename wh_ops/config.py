import os
import yaml

DEFAULT_CONFIG = {
    'google_auth': {
        'token_path': '~/.config/google-docs-mcp/token.json',
    },
    'spreadsheets': {
        'delivery_rate': '1c936V1WcrQGJsfd74ntFp3zXeHmgX0nKo3cq-3j-P4E',
    },
    'warehouses': [
        'GURGAON_WH', 'LUCKNOW_NEW_WH', 'SNP_WH', 'VARANASI_WH',
        'BAHADURGARH_WH', 'DADRI_WH', 'PATNA_WH',
    ],
    'output_dir': '~/Desktop/warehouse-dashboards/',
    'scripts': {
        'xb': '~/Desktop/warehouse-dashboards/refresh_xb_cost_dashboard.py',
        'jit': '~/Desktop/warehouse-dashboards/refresh_delivery_dashboard.py',
        'fm_html': '~/Desktop/warehouse-dashboards/b2b-billing-model.html',
    },
}

def load_config(path=None):
    config = DEFAULT_CONFIG.copy()
    search_paths = [
        path,
        os.path.expanduser('~/.wh-ops/config.yaml'),
        os.path.join(os.getcwd(), 'config.yaml'),
    ]
    for p in search_paths:
        if p and os.path.exists(os.path.expanduser(p)):
            with open(os.path.expanduser(p)) as f:
                user_cfg = yaml.safe_load(f) or {}
            _deep_merge(config, user_cfg)
            break
    config['output_dir'] = os.path.expanduser(config['output_dir'])
    config['google_auth']['token_path'] = os.path.expanduser(config['google_auth']['token_path'])
    return config

def _deep_merge(base, override):
    for k, v in override.items():
        if k in base and isinstance(base[k], dict) and isinstance(v, dict):
            _deep_merge(base[k], v)
        else:
            base[k] = v
