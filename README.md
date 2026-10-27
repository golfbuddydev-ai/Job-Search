# Job Search Agent

A free, open-source job search assistant that runs on your own GitHub and Google accounts.

I built this to give something back to the industry. A lot of good people in ad tech and media are looking for work right now. If this saves you a few hours a week and helps you land your next role, it's done its job.

## What it does

1. **Learns your experience.** It reads your CV, then every couple of days asks you a few short questions in a Google Sheet ("What was the biggest account you grew, and by how much?"). Your answers build a richer profile than your CV alone.
2. **Finds jobs.** Twice a week it searches job boards, company career sites and remote boards in the countries you choose.
3. **Scores them honestly.** Claude rates each job 1–10 against your real experience. Only the good ones reach your Matches tab, each with a one-line reason.
4. **Tailors your CV.** Type **Y** next to a job you like, and it writes a Word CV aimed at that role, using only your real experience. No invented numbers.

Everything lands in one Google Sheet you own.

## What you need

- A free **GitHub** account
- A free **Google** account
- A **Claude API key** (pay-as-you-go; most people spend a few dollars a month, see the [FAQ](FAQ.md#what-does-it-cost))
- Optional: a free **Adzuna** API key for wider job board coverage
- About **30–45 minutes** for setup, once

No coding needed. You'll copy and paste a few things, and Claude can write your settings file for you.

## Get started

**→ [SETUP.md](SETUP.md)** has step-by-step instructions.

**→ [FAQ.md](FAQ.md)** covers questions, costs, privacy and fixing problems.

## Good to know

- **It runs entirely on your accounts.** Your CV, profile and matches live in your Google Drive. Your API usage is billed to you. Nothing passes through me, and I can't see any of it.
- **It doesn't scrape LinkedIn.** It uses official job feeds and public career pages.
- **Always read a tailored CV before you send it.** It's a strong first draft, not a finished one.
- **Provided as-is**, under the [MIT licence](LICENSE). I'm not offering support, but the FAQ covers the common problems, and Claude is very good at helping with the rest (FAQ explains how).

Built with Claude. Good luck out there.
