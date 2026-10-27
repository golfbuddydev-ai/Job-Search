"""
Step 2 -- the interview loop. Runs every 2 days automatically, or any time
from the Actions tab ("2 - Interview round" -> Run workflow).

Each run:
  1. Reads any answers you've typed into the Answer column of the
     Interview Log tab, and adds them to your Master Profile.
  2. Adds the next few questions to the Interview Log for you to answer.

Skipped a round? No problem. It only tops up to QUESTIONS_PER_ROUND
unanswered questions, so they never pile up.
"""

import os
import json
import datetime

from anthropic import Anthropic

import config
import sheets_helper
from claude_helper import extract_text

PROFILE_HEADER = ["Section", "Content", "Last Updated", "Source"]
INTERVIEW_HEADER = ["Date Asked", "Question", "Answer", "Folded In"]


def summarize_answer(client, question, answer):
    """Turn a raw Q&A pair into a clean profile entry."""
    system_prompt = """Turn this interview question and answer into a concise, \
well-written addition to a professional master profile document. Use only what the \
answer says -- do not add or embellish. Respond with ONLY a JSON object, no other \
text: {"section": "<short section label>", "content": "<clean write-up>"}"""

    response = client.messages.create(
        model=config.CLAUDE_MODEL,
        max_tokens=800,
        system=system_prompt,
        messages=[{"role": "user", "content": f"Q: {question}\nA: {answer}"}],
    )
    raw = extract_text(response).replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"  [warn] Couldn't read Claude's summary ({e}). Will retry this answer next run.")
        return None


def ingest_answers(client, interview_tab, profile_tab):
    rows = interview_tab.get_all_records()
    header = interview_tab.row_values(1)
    folded_col = header.index("Folded In") + 1
    ingested = 0

    for i, row in enumerate(rows, start=2):  # row 1 is the header
        answer = str(row.get("Answer", "")).strip()
        folded = str(row.get("Folded In", "")).strip().upper()
        if not answer or folded == "Y":
            continue
        entry = summarize_answer(client, row.get("Question", ""), answer)
        if entry is None:
            continue
        today = datetime.date.today().isoformat()
        profile_tab.append_row([entry.get("section", ""), entry.get("content", ""), today, "Interview"])
        interview_tab.update_cell(i, folded_col, "Y")
        ingested += 1

    return ingested


def unanswered_count(interview_tab):
    return sum(
        1 for r in interview_tab.get_all_records()
        if str(r.get("Question", "")).strip() and not str(r.get("Answer", "")).strip()
    )


def generate_questions(client, profile, past_questions, count):
    past_q_text = "\n".join(f"- {q}" for q in past_questions) or "(none yet)"

    system_prompt = f"""You are building out a candidate's master profile for job \
search purposes, through periodic short interviews. Here is the profile so far:

{profile}

Questions already asked previously (do not repeat these or close variants):
{past_q_text}

Generate {count} new question(s) that would surface useful, \
specific detail not yet captured -- concrete metrics, scope of ownership, tools \
used, notable outcomes, or context that would help tailor CVs and match roles. \
Prioritize gaps you can see in the profile above. Keep questions short and \
specific, not generic ("tell me about your experience" is too vague).

Respond with ONLY a JSON array of strings, no other text."""

    response = client.messages.create(
        model=config.CLAUDE_MODEL,
        max_tokens=1500,
        system=system_prompt,
        messages=[{"role": "user", "content": "Generate the questions."}],
    )
    raw = extract_text(response).replace("```json", "").replace("```", "").strip()
    try:
        questions = json.loads(raw)
        return [q for q in questions if isinstance(q, str) and q.strip()]
    except json.JSONDecodeError as e:
        print(f"  [warn] Couldn't read Claude's questions ({e}). Skipping this round.")
        return []


def main():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise SystemExit("ANTHROPIC_API_KEY is not set. See SETUP.md, step 5.")
    client = Anthropic(api_key=api_key)

    gc = sheets_helper.get_client()
    profile_tab = sheets_helper.open_tab(gc, config.PROFILE_TAB, PROFILE_HEADER)
    interview_tab = sheets_helper.open_tab(gc, config.INTERVIEW_TAB, INTERVIEW_HEADER)

    profile_rows = profile_tab.get_all_records()
    if not profile_rows:
        print("Your Master Profile is empty -- run '1 - Build profile from CV' first.")
        return

    print("Checking for new answers to add to your profile...")
    n = ingest_answers(client, interview_tab, profile_tab)
    print(f"  Added {n} answer(s).")

    waiting = unanswered_count(interview_tab)
    needed = config.QUESTIONS_PER_ROUND - waiting
    if needed <= 0:
        print(f"  {waiting} question(s) still waiting for answers -- not adding more this round.")
        return

    past_questions = [r["Question"] for r in interview_tab.get_all_records() if r.get("Question")]
    print(f"Writing {needed} new question(s)...")
    questions = generate_questions(
        client, sheets_helper.profile_text(profile_tab.get_all_records()), past_questions, needed
    )[:needed]

    today = datetime.date.today().isoformat()
    rows = [[today, q, "", ""] for q in questions]
    if rows:
        interview_tab.append_rows(rows)
    print(f"Added {len(rows)} new question(s) to the '{config.INTERVIEW_TAB}' tab.")


if __name__ == "__main__":
    main()
