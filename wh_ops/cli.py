"""Main CLI entry point."""
import argparse
from wh_ops import __version__

def main():
    parser = argparse.ArgumentParser(
        prog='wh-ops',
        description='Warehouse Operations CLI — NF/Red analysis, cost dashboards, billing'
    )
    parser.add_argument('--version', action='version', version=f'wh-ops {__version__}')

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # nf
    nf_parser = subparsers.add_parser('nf', help='Tech NF + Tech Red + WH Red bucket analysis')
    nf_parser.add_argument('--date', help='MTD cutoff date (YYYY-MM-DD), default: yesterday')
    nf_parser.add_argument('--config', help='Path to config.yaml')

    # xb
    xb_parser = subparsers.add_parser('xb', help='XB CDC Cost & SLA Dashboard refresh')
    xb_parser.add_argument('--config', help='Path to config.yaml')

    # fm
    fm_parser = subparsers.add_parser('fm', help='B2B Billing Intelligence Dashboard')
    fm_parser.add_argument('--config', help='Path to config.yaml')

    # jit
    jit_parser = subparsers.add_parser('jit', help='Non-Essentials Delivery Dashboard refresh')
    jit_parser.add_argument('--config', help='Path to config.yaml')

    args = parser.parse_args()

    if args.command == 'nf':
        from wh_ops.commands import nf
        nf.run(args)
    elif args.command == 'xb':
        from wh_ops.commands import xb
        xb.run(args)
    elif args.command == 'fm':
        from wh_ops.commands import fm
        fm.run(args)
    elif args.command == 'jit':
        from wh_ops.commands import jit
        jit.run(args)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
