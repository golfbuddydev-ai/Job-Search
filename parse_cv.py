"""
Step 1 -- build your Master Profile from your CV. Run this once.

Default: reads the Google Doc named in config.CV_DOC_NAME. Run it from
GitHub: Actions tab -> "1 - Build profile from CV" -> Run workflow.

Optional, if you run things on your own computer instead:
    python parse_cv.py path/to/your_cv.pdf      (or .docx / .txt)

It won't run twice by accident: if your Master Profile tab already has
content from a CV, it stops. To start over with a new CV, delete every row
except the header row in the Master Profile tab, then run it again.
"""

import os
import sys
import json
import datetime

from anthropic import Anthropic

import config
import sheets_helper
from claude_helper import extract_text

PROFILE_HEADER = ["Section", "Content", "Last Updated", "Source"]


def extract_file_text(path):
    ext = os.path.splitext(path)[1].lower()
    if ext == ".txt":
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    if ext == ".pdf":
        from pypdf import PdfReader
        reader = PdfReader(path)
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    if ext == ".docx":
        import docx
        doc = docx.Document(path)
        return "\n".join(p.text for p in doc.paragraphs)
    raise SystemExit(f"Unsupported file type: {ext}. Use .pdf, .docx or .txt")


def structure_cv(client, cv_text):
    """Ask Claude to turn raw CV text into structured profile sections."""
    system_prompt = """You are helping build a structured "master profile" from a CV, \
to be used later for job matching and CV tailoring. Extract the information into \
clear sections. Do not invent or embellish anything not in the source text.

Respond with ONLY a JSON array, no other text, in this shape:
[
  {"section": "Contact", "content": "..."},
  {"section": "Summary", "content": "..."},
  {"section": "Experience - <Company/Role>", "content": "..."},
  {"section": "Skills", "content": "..."},
  {"section": "Education", "content": "..."}
]
Create one "Experience - ..." entry per role held, with dates, scope, and any \
metrics/achievements mentioned. Keep each content field concise but complete."""

    response = client.messages.create(
        model=config.CLAUDE_MODEL,
        max_tokens=4000,
        system=system_prompt,
        messages=[{"role": "user", "content": cv_text}],
    )
    raw = extract_text(response).replace("```json", "").replace("```", "").strip()
    return json.loads(raw)


def main():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise SystemExit("ANTHROPIC_API_KEY is not set. See SETUP.md, step 5.")

    gc = sheets_helper.get_client()
    profile_tab = sheets_helper.open_tab(gc, config.PROFILE_TAB, PROFILE_HEADER)

    already_seeded = any(
        str(r.get("Source", "")).strip() == "CV upload" for r in profile_tab.get_all_records()
    )
    if already_seeded:
        print(
            f"Your '{config.PROFILE_TAB}' tab already has your CV in it, so nothing was changed.\n"
            "To start over with a new CV: delete every row except the header row in that tab, "
            "then run this again."
        )
        return

    if len(sys.argv) > 1:
        print(f"Reading {sys.argv[1]}...")
        cv_text = extract_file_text(sys.argv[1])
    else:
        print(f"Reading your CV from the Google Doc '{config.CV_DOC_NAME}'...")
        cv_text = sheets_helper.read_cv_doc()

    if len(cv_text.strip()) < 200:
        raise SystemExit(
            "Your CV came back empty or very short. Check the Google Doc has your full CV "
            "pasted in as text (not an image or an attached PDF)."
        )

    client = Anthropic(api_key=api_key)
    print("Organising your CV into profile sections with Claude...")
    sections = structure_cv(client, cv_text)
    print(f"  Found {len(sections)} sections.")

    today = datetime.date.today().isoformat()
    rows = [[s.get("section", ""), s.get("content", ""), today, "CV upload"] for s in sections]
    profile_tab.append_rows(rows)
    print(f"Done. Wrote {len(rows)} sections to the '{config.PROFILE_TAB}' tab.")
    print("Next: run '2 - Interview round' to get your first questions.")


if __name__ == "__main__":
    main()
