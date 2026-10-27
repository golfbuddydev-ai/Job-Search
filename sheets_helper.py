"""Shared helpers for the Google Sheet and Google Doc the agent uses.

Everything lives in YOUR Google Drive:
  - one spreadsheet (config.SPREADSHEET_NAME) with three tabs that are
    created automatically: Master Profile, Interview Log, Matches
  - one Google Doc with your CV pasted in (config.CV_DOC_NAME)

Both must be shared with your Google service account's email address
(Editor access) -- see SETUP.md.
"""

import os

import gspread
from google.auth.transport.requests import AuthorizedSession
from google.oauth2.service_account import Credentials

import config

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

SHARE_HINT = (
    "Check that (1) the name in config.py matches exactly, including capitals, "
    "and (2) you shared it with your service account's email address as Editor. "
    "See SETUP.md, step 3."
)


def get_creds():
    creds_path = os.environ.get("GOOGLE_SERVICE_ACCOUNT_FILE", "service_account.json")
    if not os.path.exists(creds_path):
        raise SystemExit(
            f"Google service account file not found at '{creds_path}'. "
            "Did you add the GOOGLE_SERVICE_ACCOUNT_JSON secret? See SETUP.md, step 5."
        )
    return Credentials.from_service_account_file(creds_path, scopes=SCOPES)


def get_client():
    return gspread.authorize(get_creds())


def open_spreadsheet(gc):
    try:
        return gc.open(config.SPREADSHEET_NAME)
    except gspread.SpreadsheetNotFound:
        raise SystemExit(
            f"Couldn't find a Google Sheet called '{config.SPREADSHEET_NAME}'. {SHARE_HINT}"
        )


def open_tab(gc, tab_name, header_row):
    """Open a tab inside the agent's spreadsheet, creating it (with its
    header row) if it doesn't exist yet. Also adds any header columns that
    are missing from an existing tab, so older sheets keep working."""
    spreadsheet = open_spreadsheet(gc)
    try:
        tab = spreadsheet.worksheet(tab_name)
    except gspread.WorksheetNotFound:
        tab = spreadsheet.add_worksheet(title=tab_name, rows=1000, cols=max(len(header_row), 10))
        tab.append_row(header_row)
        return tab

    existing = tab.row_values(1)
    if not existing:
        tab.append_row(header_row)
        return tab

    missing = [h for h in header_row if h not in existing]
    if missing:
        start_col = len(existing) + 1
        if tab.col_count < len(existing) + len(missing):
            tab.add_cols(len(existing) + len(missing) - tab.col_count)
        for offset, name in enumerate(missing):
            tab.update_cell(1, start_col + offset, name)
    return tab


def read_cv_doc():
    """Return the plain text of the Google Doc named config.CV_DOC_NAME."""
    session = AuthorizedSession(get_creds())

    safe_name = config.CV_DOC_NAME.replace("'", "\\'")
    query = (
        f"name = '{safe_name}' "
        "and mimeType = 'application/vnd.google-apps.document' and trashed = false"
    )
    r = session.get(
        "https://www.googleapis.com/drive/v3/files",
        params={"q": query, "fields": "files(id,name)", "pageSize": 5},
        timeout=30,
    )
    r.raise_for_status()
    files = r.json().get("files", [])
    if not files:
        raise SystemExit(f"Couldn't find a Google Doc called '{config.CV_DOC_NAME}'. {SHARE_HINT}")

    r = session.get(
        f"https://www.googleapis.com/drive/v3/files/{files[0]['id']}/export",
        params={"mimeType": "text/plain"},
        timeout=60,
    )
    r.raise_for_status()
    return r.content.decode("utf-8-sig", errors="replace")


def profile_text(profile_rows):
    """Flatten the Master Profile tab into one block of text for Claude."""
    return "\n".join(f"[{r.get('Section', '')}] {r.get('Content', '')}" for r in profile_rows)
