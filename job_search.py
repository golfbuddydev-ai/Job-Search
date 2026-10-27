"""
Step 3 -- find jobs and score them against your profile.

Run from the Actions tab ("3 - Job search" -> Run workflow), or let it run
on its schedule (twice a week by default).

Where it looks:
  - Adzuna: keyword search across your countries (free API key needed)
  - Companies on Greenhouse / Lever / SmartRecruiters / Workable
    (config.ATS_WATCHLIST)
  - Remote job boards: RemoteOK and Remotive
  - Company careers pages you list (config.CAREER_PAGES)

How it keeps cost down, in order:
  1. Drops listings older than MAX_LISTING_AGE_DAYS        (free)
  2. Drops listings with none of your RELEVANCE_KEYWORDS    (free)
  3. Drops anything it has already scored before            (free)
  4. Scores at most MAX_LISTINGS_TO_SCORE listings          (paid, capped)
Listings scoring MIN_FIT_SCORE or higher go to the Matches tab. Every
listing scored, good or bad, is logged in the All Checked tab, so nothing
is ever paid for twice -- and you can browse the near-misses there.
"""

import os
import re
import json
import datetime
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from anthropic import Anthropic

import config
import sheets_helper
from claude_helper import extract_text

PROFILE_HEADER = ["Section", "Content", "Last Updated", "Source"]
MATCHES_HEADER = [
    "Date Found", "Fit Score", "Title", "Company", "Location",
    "Work Type", "Source", "Link", "Why It Fits", "Apply?", "Tailored CV Link",
]

CHECKED_HEADER = ["Date Checked", "Fit Score", "Title", "Company", "Link", "Why"]

ATS_ENDPOINTS = {
    "greenhouse": "https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true",
    "lever": "https://api.lever.co/v0/postings/{slug}?mode=json",
    "smartrecruiters": "https://api.smartrecruiters.com/v1/companies/{slug}/postings",
    "workable": "https://apply.workable.com/api/v1/widget/accounts/{slug}",
}


def strip_html(text):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", text or "")).strip()


def classify_work_type(listing):
    """Best guess at Remote / Hybrid / Unspecified from the listing text.
    Many postings don't say, so 'Unspecified' is common and not a guess."""
    text = f"{listing.get('title', '')} {listing.get('location', '')} {listing.get('description', '')}".lower()
    if "hybrid" in text:
        return "Hybrid"
    if "remote" in text or "work from home" in text or "wfh" in text or listing.get("remote") is True:
        return "Remote"
    return "Unspecified"


# --- Source 1: Adzuna --------------------------------------------------------

def _adzuna_listing(job, country, remote_search):
    return {
        "title": job.get("title", ""),
        "company": (job.get("company") or {}).get("display_name", ""),
        "location": "Remote" if remote_search else (job.get("location") or {}).get("display_name", ""),
        "remote": remote_search or "remote" in (job.get("title", "") + job.get("description", "")).lower(),
        "source": f"Adzuna ({country}{', remote' if remote_search else ''})",
        "link": job.get("redirect_url", ""),
        "description": strip_html(job.get("description", ""))[:800],
        "posted_date": job.get("created", ""),
    }


def fetch_adzuna(app_id, app_key):
    listings = []
    for country in config.SEARCH_COUNTRIES:
        url = f"https://api.adzuna.com/v1/api/jobs/{country}/search/1"
        for keyword in config.SEARCH_KEYWORDS:
            params = {
                "app_id": app_id,
                "app_key": app_key,
                "results_per_page": config.RESULTS_PER_SOURCE,
                "what": keyword,
                "content-type": "application/json",
                "max_days_old": config.MAX_LISTING_AGE_DAYS,
            }
            searches = [(params, False)]
            if config.INCLUDE_REMOTE_SEARCH:
                searches.append(({**params, "where": "remote"}, True))

            for p, remote_search in searches:
                try:
                    r = requests.get(url, params=p, timeout=15)
                    r.raise_for_status()
                    results = r.json().get("results", [])
                except Exception as e:
                    print(f"  [skip] Adzuna {country}/{keyword}{' (remote)' if remote_search else ''}: {e}")
                    continue
                listings += [_adzuna_listing(job, country, remote_search) for job in results]
    return listings


# --- Source 2: Company ATS feeds ---------------------------------------------

def _parse_ats_response(ats, data):
    jobs = []
    if ats == "greenhouse":
        for j in data.get("jobs", []):
            jobs.append({
                "title": j.get("title", ""),
                "location": (j.get("location") or {}).get("name", ""),
                "remote": "remote" in ((j.get("location") or {}).get("name", "") or "").lower(),
                "link": j.get("absolute_url", ""),
                "description": strip_html(j.get("content", ""))[:800],
                "posted_date": j.get("updated_at", ""),
            })
    elif ats == "lever":
        for j in data if isinstance(data, list) else []:
            posted = ""
            if j.get("createdAt"):
                try:
                    posted = datetime.datetime.utcfromtimestamp(j["createdAt"] / 1000).isoformat()
                except Exception:
                    posted = ""
            location = (j.get("categories") or {}).get("location", "") or ""
            jobs.append({
                "title": j.get("text", ""),
                "location": location,
                "remote": "remote" in location.lower(),
                "link": j.get("hostedUrl", ""),
                "description": strip_html(j.get("descriptionPlain", ""))[:800],
                "posted_date": posted,
            })
    elif ats == "smartrecruiters":
        for j in data.get("content", []):
            jobs.append({
                "title": j.get("name", ""),
                "location": (j.get("location") or {}).get("city", ""),
                "remote": bool((j.get("location") or {}).get("remote")),
                "link": j.get("applyUrl", "") or j.get("ref", ""),
                "description": "",
                "posted_date": j.get("releasedDate", ""),
            })
    elif ats == "workable":
        for j in data.get("jobs", []):
            loc = j.get("location")
            jobs.append({
                "title": j.get("title", ""),
                "location": loc.get("city", "") if isinstance(loc, dict) else (j.get("city") or ""),
                "remote": bool(j.get("telecommuting")),
                "link": j.get("url", ""),
                "description": strip_html(j.get("description", ""))[:800],
                "posted_date": j.get("published_on", ""),
            })
    return jobs


def fetch_ats_watchlist():
    listings = []
    for company_name, ats, slug in config.ATS_WATCHLIST:
        url_template = ATS_ENDPOINTS.get(ats.lower())
        if not url_template:
            print(f"  [skip] {company_name}: unknown platform '{ats}' "
                  f"(use greenhouse, lever, smartrecruiters or workable)")
            continue
        try:
            r = requests.get(url_template.format(slug=slug), timeout=15)
            if r.status_code == 404:
                print(f"  [skip] {company_name}: '{slug}' not found on {ats} -- check it in config.py")
                continue
            r.raise_for_status()
            jobs = _parse_ats_response(ats.lower(), r.json())
        except Exception as e:
            print(f"  [skip] {company_name} ({ats}): {e}")
            continue

        for job in jobs:
            job["company"] = company_name
            job["source"] = f"{company_name} ({ats})"
            listings.append(job)
    return listings


# --- Source 3: Remote boards -------------------------------------------------

def fetch_remote_boards():
    listings = []

    try:
        r = requests.get("https://remoteok.com/api", timeout=15, headers={"User-Agent": "job-search-agent"})
        r.raise_for_status()
        for job in r.json()[1:]:  # first item is metadata, not a job
            listings.append({
                "title": job.get("position", ""),
                "company": job.get("company", ""),
                "location": "Remote",
                "remote": True,
                "source": "RemoteOK",
                "link": job.get("url", ""),
                "description": strip_html(job.get("description", ""))[:800],
                "posted_date": job.get("date", ""),
            })
    except Exception as e:
        print(f"  [skip] RemoteOK: {e}")

    for keyword in config.SEARCH_KEYWORDS:
        try:
            r = requests.get(
                "https://remotive.com/api/remote-jobs",
                params={"search": keyword, "limit": config.RESULTS_PER_SOURCE},
                timeout=15,
            )
            r.raise_for_status()
            for job in r.json().get("jobs", []):
                listings.append({
                    "title": job.get("title", ""),
                    "company": job.get("company_name", ""),
                    "location": job.get("candidate_required_location") or "Remote",
                    "remote": True,
                    "source": "Remotive",
                    "link": job.get("url", ""),
                    "description": strip_html(job.get("description", ""))[:800],
                    "posted_date": job.get("publication_date", ""),
                })
        except Exception as e:
            print(f"  [skip] Remotive/{keyword}: {e}")

    return listings


# --- Source 4: Company careers pages -----------------------------------------

def fetch_career_pages(client):
    """Read each careers page in config.CAREER_PAGES and have Claude pull
    out the job listings. Only works for pages whose jobs are in the plain
    HTML -- see the note in config.py."""
    listings = []
    for company_name, url in config.CAREER_PAGES:
        try:
            r = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0 (job-search-agent)"})
            r.raise_for_status()
        except Exception as e:
            print(f"  [skip] {company_name}: couldn't load page ({e})")
            continue

        soup = BeautifulSoup(r.text, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        for a in soup.find_all("a", href=True):
            href = urljoin(url, a["href"])
            if href.startswith("http"):
                a.replace_with(f"{a.get_text(strip=True)} [LINK: {href}]")

        page_text = "\n".join(
            line for line in soup.get_text(separator="\n", strip=True).split("\n") if line.strip()
        )[:8000]

        if len(page_text) < 200:
            print(f"  [warn] {company_name}: page was nearly empty -- probably loads its jobs with "
                  f"JavaScript, which this can't read. Check it by hand: {url}")
            continue

        system_prompt = """Extract job listings from this careers page text. The text may include \
[LINK: url] annotations after link text -- use those as the apply/listing URL when present. \
If this page clearly has no job listings visible in the text (e.g. it's just navigation/marketing \
copy with no actual roles listed), respond with an empty array -- don't guess or invent listings.

Respond with ONLY a JSON array, no other text:
[{"title": "...", "location": "...", "link": "... or empty string if none found"}]"""

        try:
            response = client.messages.create(
                model=config.CLAUDE_MODEL,
                max_tokens=1500,
                system=system_prompt,
                messages=[{"role": "user", "content": page_text}],
            )
            raw = extract_text(response).replace("```json", "").replace("```", "").strip()
            jobs = json.loads(raw)
        except Exception as e:
            print(f"  [warn] {company_name}: couldn't extract listings ({e})")
            continue

        found = 0
        for j in jobs if isinstance(jobs, list) else []:
            if isinstance(j, str):
                j = {"title": j}
            elif not isinstance(j, dict):
                continue
            listings.append({
                "title": j.get("title", ""),
                "company": company_name,
                "location": j.get("location", ""),
                "remote": "remote" in (j.get("location", "") or "").lower(),
                "source": f"{company_name} (careers page)",
                "link": j.get("link") or url,
                "description": "",
            })
            found += 1
        if found:
            print(f"  {company_name}: {found} listing(s).")
    return listings


# --- Free filters (run before any paid scoring) -------------------------------

def parse_posted_date(value):
    """Best-effort date parse. None means 'unknown', not 'too old' -- several
    sources don't give a reliable date, and those listings are kept."""
    if not value:
        return None
    value = str(value)
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.datetime.strptime(value[:19].rstrip("Z"), fmt).date()
        except ValueError:
            continue
    try:
        return datetime.datetime.fromisoformat(value.replace("Z", "+00:00")).date()
    except ValueError:
        return None


def filter_by_age(listings):
    today = datetime.date.today()
    kept = []
    for l in listings:
        posted = parse_posted_date(l.get("posted_date"))
        if posted is None or (today - posted).days <= config.MAX_LISTING_AGE_DAYS:
            kept.append(l)
    if len(kept) < len(listings):
        print(f"  Age filter: dropped {len(listings) - len(kept)} older than {config.MAX_LISTING_AGE_DAYS} days.")
    return kept


def filter_relevant(listings):
    keywords = [kw.lower() for kw in config.RELEVANCE_KEYWORDS]
    kept = [
        l for l in listings
        if any(kw in f"{l.get('title', '')} {l.get('description', '')}".lower() for kw in keywords)
    ]
    if len(kept) < len(listings):
        print(f"  Keyword filter: dropped {len(listings) - len(kept)} clearly unrelated listings.")
    return kept


def _norm(text):
    return re.sub(r"[^a-z0-9]+", " ", (text or "").lower()).strip()


def listing_key(listing):
    """Two keys per listing: its link, and its title+company. A listing
    matching either one is treated as a duplicate."""
    return listing.get("link", "").strip(), f"{_norm(listing.get('title'))}|{_norm(listing.get('company'))}"


def remove_duplicates(listings, existing_rows):
    """Drop repeats within this run, and anything already scored in an
    earlier run (Matches + All Checked tabs), so nothing is paid for twice."""
    seen_links, seen_names = set(), set()
    for row in existing_rows:
        link, name = listing_key({
            "link": str(row.get("Link", "")), "title": str(row.get("Title", "")),
            "company": str(row.get("Company", "")),
        })
        if link:
            seen_links.add(link)
        seen_names.add(name)

    kept = []
    for l in listings:
        link, name = listing_key(l)
        if (link and link in seen_links) or name in seen_names:
            continue
        if link:
            seen_links.add(link)
        seen_names.add(name)
        kept.append(l)
    if len(kept) < len(listings):
        print(f"  Duplicate filter: dropped {len(listings) - len(kept)} repeats or already-seen listings.")
    return kept


# --- Scoring against your Master Profile --------------------------------------

def score_listings(client, profile, listings):
    """Score listings in batches of 10. Returns every listing that was
    scored successfully, with fit_score and why_it_fits added, best first.
    Listings in a batch that failed are left out, so they're retried next run."""
    scored = []
    batch_size = 10
    for i in range(0, len(listings), batch_size):
        batch = listings[i:i + batch_size]
        listing_text = "\n\n".join(
            f"[{j}] {l['title']} at {l['company']} ({l['location']})\n{l.get('description', '')[:400]}"
            for j, l in enumerate(batch)
        )
        system_prompt = f"""Here is a candidate's master profile:

{profile}

Score each numbered job listing below for fit against this candidate's actual \
experience, on a scale of 1-10. Be honest -- most listings should NOT score highly. \
Respond with ONLY a JSON array, no other text:
[{{"index": <int>, "fit_score": <int 1-10>, "why_it_fits": "<1 sentence, or why it doesn't if scoring low>"}}]"""

        try:
            response = client.messages.create(
                model=config.CLAUDE_MODEL,
                max_tokens=1500,
                system=system_prompt,
                messages=[{"role": "user", "content": listing_text}],
            )
            raw = extract_text(response).replace("```json", "").replace("```", "").strip()
            results = json.loads(raw)
        except Exception as e:
            print(f"  [warn] a scoring batch failed ({e}) -- those listings will be retried next run.")
            continue

        for res in results if isinstance(results, list) else []:
            try:
                idx = int(res.get("index"))
                score = int(res.get("fit_score", 0))
            except (TypeError, ValueError):
                continue
            if 0 <= idx < len(batch):
                scored.append({**batch[idx], "fit_score": score, "why_it_fits": res.get("why_it_fits", "")})

    return sorted(scored, key=lambda s: s["fit_score"], reverse=True)


def main():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise SystemExit("ANTHROPIC_API_KEY is not set. See SETUP.md, step 5.")
    adzuna_id = os.environ.get("ADZUNA_APP_ID")
    adzuna_key = os.environ.get("ADZUNA_APP_KEY")

    client = Anthropic(api_key=api_key)
    gc = sheets_helper.get_client()

    profile_rows = sheets_helper.open_tab(gc, config.PROFILE_TAB, PROFILE_HEADER).get_all_records()
    if not profile_rows:
        raise SystemExit("Your Master Profile is empty -- run '1 - Build profile from CV' first.")
    profile = sheets_helper.profile_text(profile_rows)

    matches_tab = sheets_helper.open_tab(gc, config.MATCHES_TAB, MATCHES_HEADER)
    checked_tab = sheets_helper.open_tab(gc, config.CHECKED_TAB, CHECKED_HEADER)
    already_scored = matches_tab.get_all_records() + checked_tab.get_all_records()

    all_listings = []

    if adzuna_id and adzuna_key:
        print("Searching Adzuna...")
        found = fetch_adzuna(adzuna_id, adzuna_key)
        print(f"  {len(found)} listings.")
        all_listings += found
    else:
        print("[note] No Adzuna keys set, so skipping Adzuna. See SETUP.md, step 5 (optional).")

    if config.ATS_WATCHLIST:
        print("Checking watched companies...")
        found = fetch_ats_watchlist()
        print(f"  {len(found)} listings.")
        all_listings += found

    print("Checking remote job boards...")
    found = fetch_remote_boards()
    print(f"  {len(found)} listings.")
    all_listings += found

    # Free filters first, so careers-page reading (which uses Claude) is the
    # only paid step before scoring.
    all_listings = filter_by_age(all_listings)
    all_listings = filter_relevant(all_listings)

    if config.CAREER_PAGES:
        print("Reading company careers pages...")
        found = fetch_career_pages(client)
        print(f"  {len(found)} listings.")
        all_listings += filter_relevant(found)

    all_listings = remove_duplicates(all_listings, already_scored)

    if len(all_listings) > config.MAX_LISTINGS_TO_SCORE:
        print(f"  Cost cap: scoring the first {config.MAX_LISTINGS_TO_SCORE} of {len(all_listings)} "
              f"(raise MAX_LISTINGS_TO_SCORE in config.py to score more).")
        all_listings = all_listings[:config.MAX_LISTINGS_TO_SCORE]

    print(f"Scoring {len(all_listings)} new listing(s) against your profile...")
    scored = score_listings(client, profile, all_listings)
    good = [s for s in scored if s["fit_score"] >= config.MIN_FIT_SCORE]
    print(f"  {len(good)} scored {config.MIN_FIT_SCORE} or higher.")

    today = datetime.date.today().isoformat()
    if scored:
        checked_tab.append_rows([
            [today, s["fit_score"], s["title"], s["company"], s["link"], s["why_it_fits"]]
            for s in scored
        ])
    rows = [
        [today, s["fit_score"], s["title"], s["company"], s["location"],
         classify_work_type(s), s["source"], s["link"], s["why_it_fits"], "", ""]
        for s in good
    ]
    if rows:
        matches_tab.append_rows(rows)
    print(f"Done. Added {len(rows)} match(es) to the '{config.MATCHES_TAB}' tab.")
    if rows:
        print("To get a tailored CV for any of them, type Y in its 'Apply?' column.")


if __name__ == "__main__":
    main()
