# =======================================================================
#  YOUR SETTINGS -- the only file you need to edit.
#
#  Everything personal lives here: what you're looking for, where, and
#  which companies to watch. The other .py files read from this file and
#  never need touching.
#
#  Not comfortable editing this by hand? See SETUP.md, step 6: paste the
#  ready-made prompt into Claude with your CV and it writes this whole
#  file for you.
#
#  The defaults below are set up for advertising / ad tech / marketing
#  roles. Change them for your own industry.
# =======================================================================


# -----------------------------------------------------------------------
# 1. GOOGLE NAMES
# These must match the names of the Google Sheet and Google Doc you
# created in SETUP.md (step 3), exactly -- including capitals.
# -----------------------------------------------------------------------

SPREADSHEET_NAME = "Job Search Agent"     # one Google Sheet; tabs are added automatically
CV_DOC_NAME = "Job Search - My CV"        # a Google Doc with your CV pasted in

# Tab names inside the spreadsheet (created automatically -- no need to change)
PROFILE_TAB = "Master Profile"
INTERVIEW_TAB = "Interview Log"
MATCHES_TAB = "Matches"
CHECKED_TAB = "All Checked"     # every listing scored, incl. near-misses


# -----------------------------------------------------------------------
# 2. WHERE YOU WANT TO WORK
# Two-letter country codes for the Adzuna job search.
# Adzuna covers: at au be br ca ch de es fr gb in it mx nl nz pl sg us za
# (gb = United Kingdom). It does NOT cover most of the Middle East, China,
# Thailand, Malaysia, Vietnam, Indonesia or the Philippines -- for those
# markets, add companies to CAREER_PAGES below instead.
# -----------------------------------------------------------------------

SEARCH_COUNTRIES = ["gb", "us", "au", "sg", "ca"]

# Also look for remote roles listed in each of those countries.
INCLUDE_REMOTE_SEARCH = True


# -----------------------------------------------------------------------
# 3. WHAT YOU'RE LOOKING FOR
# Use industry / function words rather than exact job titles -- it casts
# a wider net. Claude does the real judgement afterwards when it scores
# each listing against your profile.
# Every keyword is searched in every country, so more keywords = more
# results and a slightly bigger API bill. 5-10 is the sweet spot.
# -----------------------------------------------------------------------

SEARCH_KEYWORDS = [
    "programmatic",
    "ad tech",
    "martech",
    "performance marketing",
    "digital marketing",
    "media sales",
    "partnerships",
    "revenue",
]

# A free word filter that runs BEFORE any paid Claude call. A listing must
# contain at least one of these words, or it's dropped without costing
# you anything. Keep it loose -- it's a cost filter, not a quality filter.
RELEVANCE_KEYWORDS = SEARCH_KEYWORDS + [
    "marketing", "advertising", "media", "brand", "commercial",
    "client", "agency", "publisher", "growth", "sales",
]


# Free filter on the JOB TITLE: a listing whose title contains any of these
# words is dropped before any paid Claude call. Big companies post lots of
# roles you'd never apply for (engineering, HR, finance...), and this stops
# them eating your scoring budget. Matches whole words, so "intern" won't
# catch "international".
# The defaults suit commercial / marketing / sales roles. If you ARE an
# engineer, designer, etc., delete those words -- or empty the list:
#   EXCLUDE_TITLE_WORDS = []
EXCLUDE_TITLE_WORDS = [
    "engineer", "engineering", "developer", "software", "backend", "frontend",
    "full stack", "devops", "sre", "qa", "data scientist", "machine learning",
    "designer", "ux", "recruiter", "talent acquisition", "intern", "internship",
    "accountant", "accounting", "payroll", "legal counsel", "paralegal",
    "it support", "infrastructure",
]


# -----------------------------------------------------------------------
# 4. HOW PICKY TO BE
# -----------------------------------------------------------------------

# Only listings Claude scores at or above this (1-10) reach your Matches
# tab. Getting too many weak matches? Raise it. Too few? Lower it.
MIN_FIT_SCORE = 7

# Ignore listings older than this many days.
MAX_LISTING_AGE_DAYS = 14

# Max listings pulled per keyword-and-country search, and per remote board.
RESULTS_PER_SOURCE = 20

# HARD CAP on how many listings Claude scores in a single run. This is
# your safety net on cost: however many listings the search finds, the
# run never scores more than this. The most promising listings (your
# keywords in the job title) are scored first; the rest wait for the next
# run. Anything already scored is never scored again.
MAX_LISTINGS_TO_SCORE = 150


# -----------------------------------------------------------------------
# 5. THE INTERVIEW LOOP
# Every couple of days the agent adds a few questions about your
# experience to the Interview Log tab. Your answers make the job matching
# and tailored CVs sharper over time.
# -----------------------------------------------------------------------

QUESTIONS_PER_ROUND = 3


# -----------------------------------------------------------------------
# 6. TAILORED CV STYLE
# True:  bullets start with a bold skill label, e.g.
#        "Client Growth: Grew the top 10 accounts by 30% in a year..."
# False: plain bullets.
# -----------------------------------------------------------------------

CV_BULLET_LABELS = True


# -----------------------------------------------------------------------
# 7. COMPANIES TO WATCH DIRECTLY (optional)
#
# Many companies post jobs on Greenhouse, Lever, SmartRecruiters or
# Workable, which have free public feeds. Add (name, platform, slug).
#
# The "slug" is the company's ID in the web address, e.g. "thetradedesk"
# in boards.greenhouse.io/thetradedesk. To check one, open:
#   boards.greenhouse.io/<slug>        jobs.lever.co/<slug>
#   careers.smartrecruiters.com/<slug> apply.workable.com/<slug>
# A wrong slug is harmless -- the run just skips it and says so in the log.
#
# The list below is an ad tech / martech starter set. Not in ad tech?
# Delete it and add companies from your own industry, or leave it empty:
#   ATS_WATCHLIST = []
# -----------------------------------------------------------------------

ATS_WATCHLIST = [
    # -- Ad tech platforms --
    ("The Trade Desk", "greenhouse", "thetradedesk"),
    ("PubMatic", "greenhouse", "pubmatic"),
    ("DoubleVerify", "greenhouse", "doubleverify"),
    ("InMobi", "greenhouse", "inmobi"),
    ("AppsFlyer", "greenhouse", "appsflyer"),
    ("Smartly.io", "greenhouse", "smartlyio"),
    # -- Martech / CRM --
    ("Klaviyo", "greenhouse", "klaviyo"),
    ("Braze", "greenhouse", "braze"),
    ("Attentive", "greenhouse", "attentive"),
    # -- Agencies / regional --
    ("Memac Ogilvy MENA", "greenhouse", "ogilvymena"),
    ("Pikasso", "smartrecruiters", "Pikasso"),
    ("Mobvista", "workable", "mobvista"),
    ("Mediacorp", "workable", "mediacorp"),
    ("GoTo (Gojek Ads)", "lever", "GoToGroup"),
]


# -----------------------------------------------------------------------
# 8. COMPANY CAREERS PAGES (optional)
#
# For companies that don't use the platforms above -- common in the
# Middle East, Southeast Asia and China, and for big agency groups.
# The agent reads the page and Claude picks out the job listings.
#
# Each page costs one small Claude call per run, so only add companies
# you genuinely want.
#
# LIMITATION: this only works if the jobs are in the page's plain HTML.
# To check: open the careers page, right-click -> "View Page Source"
# (not "Inspect"). If you can see the job titles in that source, it'll
# work. If not, the run logs a warning and skips it.
#
# The list below is a MENA / Southeast Asia / China ad-industry starter
# set. Replace it with your own, or leave it empty:  CAREER_PAGES = []
# More ad-industry ideas: examples/adtech-company-ideas.md
# -----------------------------------------------------------------------

CAREER_PAGES = [
    # -- Middle East --
    ("Impact BBDO", "https://impactbbdo.com/careers/"),
    ("Extend The Ad Network", "https://extendad.com/careers/"),
    ("TIDAL Digital", "https://tidal.digital/about-us/jobs/"),
    ("Al Arabia Outdoor", "https://al-arabia.com/careers"),
    ("Hills Advertising", "https://hillsadvertising.com/jobs.php"),
    ("Push MENA", "https://www.pushgroup.ae/careers"),
    ("Chain Reaction", "https://www.chainreaction.ae/careers/"),
    # -- Southeast Asia --
    ("Redcomm", "https://redcomm.co.id/career"),
    ("CJ WORX", "https://www.cjworx.com/index.php/jobs/"),
    ("Hashmeta", "https://hashmeta.com/jobs/"),
    ("Krome", "https://www.krome.sg/careers/"),
    ("Primal", "https://www.primal.com.my/digital-marketing-jobs/"),
    ("Moving Walls", "https://www.movingwalls.com/careers/"),
    ("AlgoriX", "https://www.algorix.co/careers/"),
    ("VGI Global Media", "https://www.vgi.co.th/career/list-career/"),
    ("Big Tree Outdoor", "https://www.bigtree.com.my/careers/"),
    ("Plan B Media", "https://www.planbmedia.co.th/th/career/"),
    # -- China --
    ("Asiaray Media", "https://www.asiaray.com/en/job-opportunities/"),
    ("Nativex", "https://www.nativex.com/en/career"),
]


# -----------------------------------------------------------------------
# 9. CLAUDE MODEL
# Leave as-is unless you know you want a different model.
# -----------------------------------------------------------------------

CLAUDE_MODEL = "claude-sonnet-5"
