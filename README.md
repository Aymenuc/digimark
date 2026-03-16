# 🌿 Wellness Profit Machine v3

An autonomous AI affiliate marketing engine. Gemini generates content, Google Cloud runs it, GitHub deploys it. You do nothing.

## How It Works

```
GitHub (your code)
   │
   ├── push to main
   │
   ▼
GitHub Actions (auto-deploy)
   │
   ├──▶ Google Cloud Functions (4 endpoints)
   ├──▶ Google Cloud Scheduler (3 cron jobs)
   ├──▶ Google Cloud Storage (dashboard + archive)
   └──▶ Google Firestore (self-learning DB)
         │
         ▼
   EVERY DAY AT 6 AM:
   Gemini AI → writes blog → publishes WordPress
             → creates 5 social posts → schedules Buffer
             → writes email → sends ConvertKit
             → generates YouTube script → archives
             → creates Pinterest pins → archives
             → builds landing page → archives
             → scores quality, interlinks, A/B tests
             → logs everything → learns → repeats
```

## Setup (30 min, one time)

### Step 1: Fork or clone this repo

```bash
git clone https://github.com/YOUR_USERNAME/wellness-profit-machine.git
cd wellness-profit-machine
```

### Step 2: Create a Google Cloud project

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Create new project (e.g. `wellness-profit-machine`)
3. Enable billing (required for Cloud Functions — won't charge you within free tier)

### Step 3: Create a service account for GitHub

```bash
# In Google Cloud Console → IAM → Service Accounts
# Create service account: "github-deploy"
# Grant roles:
#   - Cloud Functions Admin
#   - Cloud Scheduler Admin
#   - Storage Admin
#   - Firestore User
#   - Service Account User
#   - Cloud Build Editor

# Create JSON key → download it
```

### Step 4: Add GitHub Secrets

Go to your repo → Settings → Secrets and Variables → Actions → New repository secret

Add ALL of these:

| Secret Name | Value | Required? |
|---|---|---|
| `GCP_CREDENTIALS` | Paste entire JSON key file content | ✅ Yes |
| `GCP_PROJECT_ID` | Your GCP project ID | ✅ Yes |
| `GCP_REGION` | `us-central1` | ✅ Yes |
| `GCS_BUCKET` | `wellness-profit-v3` (pick any name) | ✅ Yes |
| `GEMINI_KEY` | From [aistudio.google.com/apikey](https://aistudio.google.com/apikey) | ✅ Yes |
| `AFF_TAG` | Your Amazon affiliate tag (e.g. `wellnessreset-20`) | ✅ Yes |
| `WP_URL` | `https://yourblog.com` | ✅ Yes |
| `WP_USER` | WordPress username | ✅ Yes |
| `WP_APP_PASS` | WordPress → Users → Application Passwords | ✅ Yes |
| `BUFFER_TOKEN` | Buffer API access token | Recommended |
| `BUFFER_PROFILES` | Buffer profile IDs (comma-separated) | Recommended |
| `CONVERTKIT_KEY` | ConvertKit API key | Recommended |
| `CONVERTKIT_SECRET` | ConvertKit API secret | Recommended |
| `NOTIFY_EMAIL` | Your email for daily reports | Recommended |
| `SENDGRID_KEY` | SendGrid API key (free 100 emails/day) | Recommended |
| `MEDIUM_TOKEN` | Medium integration token | Optional |

### Step 5: Push to deploy

```bash
git add .
git commit -m "Deploy wellness profit machine"
git push origin main
```

GitHub Actions automatically:
1. Authenticates to Google Cloud
2. Deploys 4 Cloud Functions
3. Creates 3 Cloud Scheduler cron jobs
4. Uploads dashboard to Cloud Storage
5. Prints your live URLs

**That's it. The machine is live.**

### Step 6: Open your dashboard

```
https://storage.googleapis.com/YOUR_BUCKET-site/index.html
```

Paste your Cloud Function base URL, hit Connect, and you can monitor everything.

## What runs automatically

| Schedule | What | Output |
|---|---|---|
| Daily 6 AM | Full content pipeline | 1 blog + 5 social + 1 email + 1 YT script + 5 pins + 1 landing page |
| Monday 8 AM | AI analytics | Trends + competitor gaps + performance review |
| 1st of month | SEO optimizer | Rewrites underperforming posts |

**Monthly output: ~30 blogs, ~150 social posts, ~8 emails, ~30 YT scripts, ~150 pins, ~30 landing pages**

## Updating the machine

Just push to GitHub. It auto-redeploys:

```bash
# Edit main.py (add topics, tweak prompts, add affiliates)
git add . && git commit -m "Added new topics" && git push
# → GitHub Actions auto-deploys to Google Cloud
```

## Monitoring

```bash
# Dashboard (browser)
https://storage.googleapis.com/YOUR_BUCKET-site/index.html

# Status API
curl https://REGION-PROJECT.cloudfunctions.net/status

# Run pipeline now
curl -X POST https://REGION-PROJECT.cloudfunctions.net/daily_pipeline

# View logs
gcloud functions logs read daily_pipeline --limit=30
```

## Join affiliate programs (all free)

| Program | Commission | Sign up |
|---|---|---|
| Market Health | Up to 60% | markethealth.com/affiliates |
| Wolfson Brands | 40% lifetime recurring | wolfsonbrands.com/affiliate |
| Physician's Choice | 25%/mo recurring | ShareASale |
| Organifi | 30% + recurring | organifi.com/affiliates |
| Four Sigmatic | 10-20% | foursigmatic.com/affiliate |
| Smart Nora | $40/sale | smartnora.com/affiliate |
| Calm | 25-40% | Impact.com |

After joining, update the URLs in `main.py` → `AFFILIATES` dict.

## File structure

```
wellness-profit-machine/
├── main.py              # 700-line AI engine (37 functions)
├── requirements.txt     # Python dependencies
├── dashboard.html       # Live control panel (hosted on GCS)
├── .gitignore
├── README.md
└── .github/
    └── workflows/
        └── deploy.yml   # Auto-deploys on push to main
```

## Cost

**$0/month.** Everything within Google Cloud free tier:
- Cloud Functions: 2M invocations/mo free
- Cloud Scheduler: 3 jobs free
- Firestore: 1GB free
- Cloud Storage: 5GB free
- Gemini API: 60 req/min free

Only cost: WordPress hosting ($4-25/mo) if you use WordPress.

## Revenue timeline

| Period | Est. Revenue |
|---|---|
| Month 1-3 | $0-$500 |
| Month 4-6 | $200-$2,000 |
| Month 7-12 | $1,000-$8,000 |
| Year 2 | $3,000-$30,000/mo |

---

Push to main. Walk away. Let the machine work.
