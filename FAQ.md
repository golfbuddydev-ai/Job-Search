# FAQ

**Jump to:** [Costs](#costs) · [Privacy and safety](#privacy-and-safety) · [Using it](#using-it) · [Changing what it looks for](#changing-what-it-looks-for) · [Troubleshooting](#troubleshooting) · [Getting help](#getting-help)

---

## Costs

### What does it cost?

The code is free. Running it uses three services, all on **your** accounts:

| Service | Cost |
|---|---|
| GitHub (runs the agent) | Free. A private repo's included Actions minutes on a free account are far more than this needs. |
| Google Sheets / Drive | Free |
| Adzuna (optional) | Free developer tier |
| **Claude API** | **Pay-as-you-go. This is the only real cost.** |

At the default settings we'd expect most people to spend **roughly US$5–10 a month** on Claude. Where it goes:

- **Job search** (twice a week): the biggest item. Each run scores up to 150 new listings in batches of 10, plus one small call per company careers page.
- **Interview round** (every 2 days): a few small calls. Pennies.
- **Tailored CV**: one call per CV, only when you mark a job **Y**.

Your actual cost depends on Claude's current prices (see Anthropic's pricing page) and your settings. More countries, keywords and careers pages means more listings to score.

### How do I make sure I never get a surprise bill?

Three layers of protection:

1. **Your monthly spend limit in the Claude Console** (Setup, Step 2). This is the real guarantee: if it's reached, calls stop until the next month. Set it.
2. **`MAX_LISTINGS_TO_SCORE`** in `config.py` (default 150) is a hard cap per job search run, however many listings are found.
3. **Nothing is paid for twice.** Free filters drop old listings and unrelated ones *before* Claude sees them, and every listing ever scored is logged in the **All Checked** tab and skipped on future runs.

### My Claude Pro / Max subscription doesn't cover it?

No. The Claude API is billed separately from Claude.ai subscriptions, through the Claude Console. You need API credit even if you pay for Claude.ai.

### How do I spend less?

In `config.py`:

- Use fewer `SEARCH_COUNTRIES` or `SEARCH_KEYWORDS`.
- Lower `MAX_LISTINGS_TO_SCORE` (e.g. to 60).
- Trim `CAREER_PAGES` to companies you genuinely want.
- Make `RELEVANCE_KEYWORDS` tighter, so the free filter drops more.

You can also run the job search once a week instead of twice: in `.github/workflows/3_job_search.yml`, change `1,4` in the cron line to just `1` (Mondays).

### Can this ever cost the person who shared it?

No. Your copy runs on your GitHub account, with your keys, billed to you. The original repo holds no keys and can't run anything on your behalf.

---

## Privacy and safety

### Where does my data go?

- **Your CV, profile, answers and matches** live in **your** Google Sheet and Doc.
- **Your settings** live in **your** GitHub repo. Keep it private.
- **To score jobs and write CVs**, your profile is sent to the Claude API under your account. Anthropic's API terms apply.
- **The person who shared this tool sees nothing.** There's no server, database or tracking.

### Can the robot (service account) see the rest of my Google Drive?

No. It can only open files you explicitly share with it. If you ever want to cut it off, unshare the Sheet and Doc, or delete the service account in Google Cloud.

### Is my API key safe?

Yes, if it only ever goes into **GitHub Secrets** (Setup, Step 5). GitHub encrypts secrets, hides them in logs, and won't show them again, even to you. Never paste a key into `config.py`, any other file, or an issue. If you think a key has leaked, delete it in the Claude Console and create a new one. It takes a minute.

### Does it scrape LinkedIn?

No. LinkedIn doesn't allow automated scraping. The agent uses Adzuna's official API, public job feeds from Greenhouse, Lever, SmartRecruiters and Workable, the RemoteOK and Remotive public APIs, and company careers pages you choose.

### Does it apply for jobs for me?

No, and it won't. It finds roles and drafts CVs. You decide, you check, and you apply.

---

## Using it

### How do I answer the interview questions?

Open your Google Sheet → **Interview Log** tab → type in the **Answer** column. Short, specific answers with numbers work best ("Grew programmatic revenue from $2M to $3.4M in 18 months, team of 4"). The next interview run adds them to your profile and marks them **Y** in "Folded In".

Can't or don't want to answer one? Skip it. The agent keeps no more than 3 unanswered questions waiting, so they won't pile up.

### How do I get a tailored CV?

In the **Matches** tab, type **Y** in the **Apply?** column next to a role. Then either wait for the daily run, or go to **Actions → 4 - Tailor CVs → Run workflow**. When it finishes, the **Tailored CV Link** column has a link to that run. Open it, scroll to **Artifacts** at the bottom, and download `tailored-cvs`. It's a zip containing the Word file(s). Downloads are kept for 30 days.

### Will the CV make things up?

It's instructed to use only what's in your profile: no invented jobs, numbers or skills. It rewords and reorders to fit the role. **Always read it before sending.** AI can still get a detail wrong, and it's your name on it.

### I updated my CV. How do I rebuild my profile?

Update your Google Doc. In the **Master Profile** tab, delete every row except the header row. Then run **1 - Build profile from CV** again. To keep your interview answers, delete only the rows where **Source** says `CV upload`, then re-run.

### Can I see the jobs that didn't make the cut?

Yes. The **All Checked** tab lists every listing that's been scored, with its score and a one-line reason. It's useful for seeing whether `MIN_FIT_SCORE` is set right.

### How do I turn the schedule off, or change it?

Open the workflow file in `.github/workflows/`, click the pencil icon, and put a `#` at the start of both the `schedule:` line and the `- cron:` line. Commit. You can still run it by hand from the Actions tab. Times in those files are UTC.

Also note that GitHub pauses scheduled runs in a repo after 60 days with no activity. If that happens, the Actions tab shows a button to turn them back on.

### How do I stop it completely?

Actions tab → click each workflow → **⋯** menu → **Disable workflow**. Or delete your copy of the repo. To be thorough, also delete the API key in the Claude Console and the service account in Google Cloud.

---

## Changing what it looks for

### I'm not in ad tech. Can I still use it?

Yes. It works for any industry. The starter settings are for advertising and marketing, so you'll want to change them. The easiest way is the Claude prompt in Setup, Step 6.

### Too many weak matches, or too few?

- **Too many:** raise `MIN_FIT_SCORE` (e.g. 7 → 8), or tighten your keywords.
- **Too few:** lower it (e.g. 7 → 6), add keywords, add countries, or add companies to watch.

Check the **All Checked** tab first. It shows what scored just below the line.

### Why doesn't it cover my country?

Adzuna covers 19 countries: Austria, Australia, Belgium, Brazil, Canada, Switzerland, Germany, Spain, France, the UK, India, Italy, Mexico, the Netherlands, New Zealand, Poland, Singapore, the US and South Africa. For everywhere else, including most of the Middle East and Southeast Asia, add companies you're interested in to `CAREER_PAGES` or `ATS_WATCHLIST`. Remote boards are always searched.

### How do I add a company?

If the company's jobs page is on `boards.greenhouse.io`, `jobs.lever.co`, `careers.smartrecruiters.com` or `apply.workable.com`, add it to `ATS_WATCHLIST` with the bit after the slash as the slug. Otherwise add its careers page URL to `CAREER_PAGES`. `config.py` explains both, including a quick check for whether a careers page will work.

---

## Troubleshooting

When a run fails (red ✗ in the Actions tab), click the run, then the failed step. The last few lines say what went wrong.

| Message says | Fix |
|---|---|
| `ANTHROPIC_API_KEY and/or GOOGLE_SERVICE_ACCOUNT_JSON secret is missing` | Add the secret in Settings → Secrets and variables → Actions. Names must match exactly (Setup, Step 5). |
| `Couldn't find a Google Sheet called ...` or `Couldn't find a Google Doc called ...` | Either the name in `config.py` doesn't match exactly (capitals and spaces count), or you haven't shared it with the service account email as **Editor** (Setup, Step 3c). |
| Something about `invalid_grant`, `JSON` or `private key` | The `GOOGLE_SERVICE_ACCOUNT_JSON` secret was pasted incompletely. Open the `.json` file, copy **all** of it, and update the secret. If you deleted the file, create a new key (Setup, Step 3a, point 5). |
| `Google Sheets API has not been used` or `... is disabled` | Enable both the Sheets API and the Drive API in Google Cloud (Setup, Step 3a, point 3). Wait a couple of minutes, then re-run. |
| `authentication_error` or `invalid x-api-key` | The Claude key is wrong or was deleted. Make a new one and update the `ANTHROPIC_API_KEY` secret. |
| `credit balance is too low` or a rate/limit error | Add credit or raise your spend limit in the Claude Console. |
| `Your CV came back empty or very short` | Your Doc has the CV as an image or an attached file. Paste it in as text. |
| `Your Master Profile is empty` | Run **1 - Build profile from CV** first. |
| Lots of `[skip] ... not found` lines | Normal. These are company slugs or pages that didn't resolve. The run carries on without them. Fix or remove them in `config.py` when you have time. |
| `[warn] ... page was nearly empty` | That company's careers page loads its jobs with JavaScript, which this tool can't read. Remove it from `CAREER_PAGES` and check that company by hand. |
| `Adzuna ...` errors | Usually a typo in the Adzuna secrets, or you've hit the free tier's usage limit. Fewer countries or keywords, or setting `INCLUDE_REMOTE_SEARCH = False`, means fewer Adzuna calls. |
| Google Cloud won't let you create a key | Work or school Google accounts sometimes block this. Use a personal Gmail account for Setup, Step 3. |

---

## Getting help

This is shared as-is, and I'm not able to offer one-to-one support. The quickest fix for almost anything is Claude itself:

1. Copy the error from the failed run (the last 20 or so lines).
2. Paste it into claude.ai with: *"I'm running an open-source job search agent on GitHub Actions. Here's the error. What's wrong and how do I fix it?"*
3. If it needs to see the code, attach the relevant `.py` file from your repo, or connect GitHub to Claude so it can read your repo directly.

**Never paste your API key or the Google `.json` key into a chat.** Claude doesn't need them to help.

### Can I change the code?

Yes, it's MIT-licensed, so do what you like with your copy. Claude, with GitHub connected, is a very good partner for that.
