import json
import os

def get_sheets_service(token_path):
    """Build Google Sheets API service from OAuth token."""
    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
    except ImportError:
        raise SystemExit(
            "Missing dependencies. Run:\n"
            "  pip install google-auth google-auth-oauthlib google-api-python-client"
        )

    token_path = os.path.expanduser(token_path)
    if not os.path.exists(token_path):
        raise SystemExit(
            f"Google token not found at {token_path}\n"
            "Set up Google Sheets API access first.\n"
            "See README.md for instructions."
        )

    with open(token_path) as f:
        token_data = json.load(f)

    creds = Credentials(
        token=token_data.get('access_token'),
        refresh_token=token_data.get('refresh_token'),
        token_uri=token_data.get('token_uri', 'https://oauth2.googleapis.com/token'),
        client_id=token_data.get('client_id'),
        client_secret=token_data.get('client_secret'),
    )

    return build('sheets', 'v4', credentials=creds)
