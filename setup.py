from setuptools import setup, find_packages

setup(
    name='wh-ops',
    version='1.0.0',
    description='Warehouse Operations CLI — NF/Red analysis, cost dashboards, billing intelligence',
    packages=find_packages(),
    python_requires='>=3.8',
    install_requires=[
        'google-auth',
        'google-auth-oauthlib',
        'google-api-python-client',
        'pyyaml',
    ],
    entry_points={
        'console_scripts': [
            'wh-ops=wh_ops.cli:main',
        ],
    },
)
