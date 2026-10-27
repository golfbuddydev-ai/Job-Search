# Setup

About 30–45 minutes, once. Do the steps in order. If you get stuck, see [FAQ.md](FAQ.md).

You'll go through seven steps:

1. Make your own copy of this repo
2. Get a Claude API key
3. Set up Google (one Sheet, one Doc, and a "robot" account that can edit them)
4. *(Optional)* Get a free Adzuna key
5. Add your keys to GitHub
6. Personalise your settings
7. Run it

---

## Step 1: Make your own copy

1. At the top of this repo's page, click the green **Use this template** button → **Create a new repository**.
2. Give it a name (e.g. `my-job-search`).
3. Choose **Private**. It will hold your search settings, so keep it to yourself.
4. Click **Create repository**.

From now on, everything happens in **your** copy, not this one.

---

## Step 2: Get a Claude API key

This is what lets the agent use Claude. It's billed separately from any Claude.ai subscription, so a Pro or Max plan doesn't cover it.

1. Sign in to the Claude Console at **console.anthropic.com**. It's a separate sign-up from Claude.ai.
2. Add a small amount of credit. US$10 is plenty to start.
3. **Set a monthly spend limit.** Something like US$15–20 is sensible. This is your guarantee of no surprise bills: if it's ever hit, the agent simply stops until next month.
4. Create an **API key**. Copy it somewhere safe for a few minutes. It starts with `sk-ant-` and you'll paste it into GitHub in Step 5.

Never paste this key into a file, an email or a chat. It only ever goes into GitHub's secret store (Step 5).

---

## Step 3: Set up Google

The agent keeps everything in one Google Sheet and reads your CV from one Google Doc. To let it edit them, you create a free **service account**, a robot Google user that only sees files you share with it.

### 3a. Create the robot account (about 10 minutes)

1. Go to **console.cloud.google.com** and sign in with your Google account.
2. At the top, click the project picker → **New project**. Name it `job-search-agent` → **Create**. Make sure the new project is selected.
3. Open the menu → **APIs & Services** → **Library**. Search for and **Enable** both of these:
   - **Google Sheets API**
   - **Google Drive API**
4. Open the menu → **IAM & Admin** → **Service accounts** → **Create service account**.
   - Name: `job-search-agent` → **Create and continue**.
   - Skip the optional role and access steps → **Done**.
5. Click the service account you just made → **Keys** tab → **Add key** → **Create new key** → **JSON** → **Create**. A `.json` file downloads. That's the robot's key. Keep it safe, and don't email it or put it in your repo.
6. Copy the service account's **email address**. It looks like `job-search-agent@your-project.iam.gserviceaccount.com`. You need it in 3c.

Google Cloud may ask you to accept terms or confirm billing details for the project. These two APIs are free at this level of use.

### 3b. Create your Sheet and your CV Doc

In Google Drive:

1. Create a **blank Google Sheet** named exactly: `Job Search Agent`
2. Create a **Google Doc** named exactly: `Job Search - My CV`
   Paste your full CV into it as text. Copy it out of Word or a PDF and paste; formatting doesn't matter.

You don't need to add anything to the Sheet. The agent creates its tabs (Master Profile, Interview Log, Matches, All Checked) automatically.

Want different names? That's fine. Just change `SPREADSHEET_NAME` and `CV_DOC_NAME` in `config.py` to match (Step 6).

### 3c. Share both with the robot

For **both** the Sheet and the Doc: click **Share**, paste the service account email from 3a, set it to **Editor**, untick "Notify people", and click **Share**.

This is the step people most often miss. If a run says it "couldn't find" your Sheet or Doc, check this first.

---

## Step 4 (optional): Get a free Adzuna key

Adzuna is a big job search engine with a free API, and it adds a lot of coverage in the UK, US, Australia, Singapore, Canada and about 14 other countries. The agent works without it, but finds more with it.

1. Sign up at **developer.adzuna.com**.
2. You'll get an **App ID** and an **App Key**. Keep them for Step 5.

---

## Step 5: Add your keys to GitHub

In **your** repo (from Step 1): **Settings** → **Secrets and variables** → **Actions** → **New repository secret**. Add each of these:

| Name (type it exactly) | Value |
|---|---|
| `ANTHROPIC_API_KEY` | Your Claude API key from Step 2 |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | Open the `.json` file from Step 3a in a text editor (Notepad, TextEdit), select **everything**, copy, paste |
| `ADZUNA_APP_ID` | *(optional)* From Step 4 |
| `ADZUNA_APP_KEY` | *(optional)* From Step 4 |

GitHub encrypts secrets. Once saved, nobody can read them back, not even you. Only your own workflow runs can use them.

Once these are saved, delete the `.json` key file from your Downloads folder. GitHub has it now.

---

## Step 6: Personalise your settings

All your preferences live in one file, **`config.py`**: countries, keywords, how picky to be, which companies to watch. Out of the box it's set up for advertising, ad tech and marketing roles.

**The easy way: let Claude write it.**

1. In your repo, open `config.py` and click the **copy** icon (top right of the file view) to copy the whole file.
2. Go to **claude.ai**, start a new chat, attach your CV, and paste in the prompt below, followed by the `config.py` you copied.
3. Answer Claude's questions. It will give you a complete new `config.py`.
4. Back in GitHub, open `config.py` → click the **pencil** icon (Edit) → select all → paste Claude's version → **Commit changes**.

```text
I'm setting up an open-source job search agent. Its settings live in a
Python file called config.py, which I'll paste below after my CV.

Please:
1. Read my CV.
2. Ask me questions, a few at a time, until you know: the roles and
   seniority I'm targeting, my industry or industries, the countries I'd
   work in (and whether I want remote roles), and any companies I'd
   especially like to work for.
3. Then give me a COMPLETE replacement config.py, in one code block,
   ready to paste. Keep every comment and the exact structure; change only
   the values.

Rules for the values:
- SEARCH_COUNTRIES: only Adzuna codes (at au be br ca ch de es fr gb in it
  mx nl nz pl sg us za). If I want a country Adzuna doesn't cover, tell me
  and suggest companies for CAREER_PAGES instead.
- SEARCH_KEYWORDS: 5-10 industry/function words, not exact job titles.
- RELEVANCE_KEYWORDS: keep it as SEARCH_KEYWORDS plus 8-12 broader words
  for my field.
- ATS_WATCHLIST: if I'm not in advertising/ad tech/marketing, replace the
  starter list. Only include companies whose Greenhouse/Lever/
  SmartRecruiters/Workable slug you're confident about, and list any you're
  unsure of separately so I can check them.
- CAREER_PAGES: if I'm not in advertising/media, empty it or replace it.
  Only use URLs you're confident are the company's own careers page.
- Leave CLAUDE_MODEL and the Google names as they are unless I ask.

Here's config.py:
```

**The hands-on way:** open `config.py`, click the pencil icon and edit it directly. Every setting has a plain-English explanation above it.

---

## Step 7: Run it

Go to your repo's **Actions** tab. You'll see four workflows, numbered in the order to run them. For each one: click it → **Run workflow** → **Run workflow**. Wait for a green tick before starting the next.

| Workflow | What it does | Then |
|---|---|---|
| **1 - Build profile from CV** | Reads your CV Doc and fills the Master Profile tab | Run once. Takes about 1 minute. |
| **2 - Interview round** | Adds 3 questions to the Interview Log tab | Answer them in the **Answer** column whenever you like |
| **3 - Job search** | Finds and scores jobs into the Matches tab | Takes 5–15 minutes. Browse your matches. |
| **4 - Tailor CVs** | Writes a CV for each match you marked **Y** in the **Apply?** column | Open the run → scroll to **Artifacts** → download |

After that, it runs itself:

- **Interview round**: every 2 days. Answer the questions when you can; it never stacks up more than 3 unanswered.
- **Job search**: Mondays and Thursdays.
- **Tailor CVs**: daily. It costs nothing on days you haven't marked any new jobs **Y**.

You can always run any of them by hand from the Actions tab.

**If a run shows a red ✗:** click it, then click the failed step to see the message. The messages are written in plain English and usually say exactly what to fix. The [FAQ](FAQ.md#troubleshooting) covers the common ones.

That's it. Good luck.
