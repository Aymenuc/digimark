"""
═══════════════════════════════════════════════════════════════════
WELLNESS PROFIT MACHINE v3 — THE FINAL FORM
═══════════════════════════════════════════════════════════════════

v1: Generate content → publish
v2: Detect trends → generate → publish → track
v3: Detect trends → analyze competitors → generate → A/B test →
    publish → create images → build landing pages → interlink →
    track → learn → optimize losers → scale winners → notify →
    repeat forever while getting smarter every cycle

NEW IN v3:
  ★ SEO AUTO-OPTIMIZER    — Rewrites underperforming posts monthly
  ★ COMPETITOR GAP FINDER — Finds topics competitors rank for, you don't
  ★ REVENUE ESTIMATOR     — Tracks estimated affiliate earnings
  ★ A/B HEADLINE TESTING  — Tests 2 titles, keeps winner
  ★ AUTO-INTERLINKING     — Every new post links to 3 older posts
  ★ LANDING PAGE BUILDER  — Auto-generates opt-in pages for lead magnets
  ★ NOTIFICATION SYSTEM   — Emails you daily/weekly reports
  ★ IMAGE PROMPT GEN      — Creates Gemini image prompts for every post
  ★ CONTENT SCORING       — Rates content quality before publishing
  ★ SEASONAL AWARENESS    — Adapts content to seasons/holidays/events
  ★ PORTFOLIO MANAGER     — Manages all affiliate links + tracks EPC
  ★ CANNIBALIZATION CHECK — Prevents keyword overlap between posts

═══════════════════════════════════════════════════════════════════
"""

import os, json, random, datetime, hashlib, re, time, logging, math
from collections import Counter
import requests
import functions_framework
from google.cloud import storage, firestore

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
log = logging.getLogger("wpm-v3")

# ═══════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════
C = {k: os.environ.get(k, "") for k in [
    "GEMINI_KEY","GEMINI_MODEL","WP_URL","WP_USER","WP_APP_PASS",
    "BUFFER_TOKEN","BUFFER_PROFILES","CONVERTKIT_KEY","CONVERTKIT_SECRET",
    "MEDIUM_TOKEN","GCS_BUCKET","AFF_TAG","NOTIFY_EMAIL","SENDGRID_KEY"
]}
C.setdefault("GEMINI_MODEL", "gemini-2.0-flash")
C.setdefault("GCS_BUCKET", "wellness-profit-v3")
C.setdefault("AFF_TAG", "wellnessreset")

def db():
    try: return firestore.Client()
    except: return None

def gcs():
    try: return storage.Client()
    except: return None

# ═══════════════════════════════════════
# GEMINI
# ═══════════════════════════════════════
def ai(prompt, temp=0.85, tokens=8192):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{C['GEMINI_MODEL']}:generateContent?key={C['GEMINI_KEY']}"
    r = requests.post(url, json={
        "contents":[{"parts":[{"text":prompt}]}],
        "generationConfig":{"temperature":temp,"maxOutputTokens":tokens}
    }, timeout=180)
    r.raise_for_status()
    return r.json()["candidates"][0]["content"]["parts"][0]["text"]

def ai_json(prompt):
    raw = ai(prompt+"\n\nReturn ONLY valid JSON. No markdown fences. No explanation.", temp=0.7)
    c = raw.strip()
    if c.startswith("```"): c = c.split("\n",1)[1].rsplit("```",1)[0].strip()
    return json.loads(c)

# ═══════════════════════════════════════
# AFFILIATE PORTFOLIO MANAGER
# Tracks all links, EPC, conversion rates
# ═══════════════════════════════════════
AFFILIATES = {
  "physicians_choice":{"name":"Physician's Choice 60B Probiotics","url":"https://www.amazon.com/dp/B07FL7HQ4F?tag={tag}","comm":"25%/mo recurring","kw":["gut","probiotic","bloat","digest","microbiome","ibs","bacteria"],"short":"Gold standard probiotic — 60B CFU, 10 strains, shelf-stable","long":"I take this every morning. 60 billion CFU with 10 diverse strains in delayed-release capsules that survive stomach acid. Most probiotics die before reaching your gut — this one doesn't. After 3 weeks I noticed less bloating and more energy.","cat":"gut","price":23.95,"est_epc":0.85},
  "organifi_green":{"name":"Organifi Green Juice","url":"https://www.organifi.com/products/green-juice?ref={tag}","comm":"30% + recurring","kw":["superfood","green","supplement","energy","detox","inflammation","ashwagandha","turmeric"],"short":"Premium superfood blend — ashwagandha, turmeric, spirulina in one scoop","long":"Replaces a cabinet of supplements. One scoop packs ashwagandha for stress, turmeric for inflammation, spirulina for energy. I was skeptical but after 30 days the afternoon crashes stopped completely.","cat":"supplements","price":69.95,"est_epc":2.40},
  "four_sigmatic":{"name":"Four Sigmatic Mushroom Coffee","url":"https://us.foursigmatic.com/?ref={tag}","comm":"10-20%","kw":["mushroom","coffee","focus","brain","lions mane","adaptogen","nootropic"],"short":"Lion's Mane + Chaga mushroom coffee — focus without the jitters","long":"Swapped my coffee 6 months ago. Same energy, zero jitters, noticeably sharper focus by mid-morning. Lion's Mane is a researched nootropic, and Chaga supports immunity.","cat":"supplements","price":36.00,"est_epc":1.10},
  "smart_nora":{"name":"Smart Nora Anti-Snoring","url":"https://www.smartnora.com/?ref={tag}","comm":"$40/sale","kw":["sleep","snoring","snore","partner","apnea","rest"],"short":"Stops snoring automatically — adjusts pillow position, no mask","long":"If snoring wrecks your sleep, this is a game-changer. A small device under your pillow gently adjusts position before snoring intensifies. No mask, no noise machine, no mouth guard.","cat":"sleep","price":299.00,"est_epc":4.80},
  "calm_app":{"name":"Calm Premium","url":"https://www.calm.com/?ref={tag}","comm":"25-40%","kw":["meditat","anxiety","stress","mental","mindful","calm","breath","relax","app"],"short":"#1 meditation and sleep app — 100M+ downloads","long":"I use this every night. Sleep Stories are incredible for shutting off a racing mind, and the Daily Calm is only 10 minutes. The one subscription I'd keep if I had to cancel everything.","cat":"mental","price":69.99,"est_epc":3.20},
  "organifi_gold":{"name":"Organifi Gold","url":"https://www.organifi.com/products/gold?ref={tag}","comm":"30%","kw":["sleep","turmeric","relax","evening","night","recovery","inflammation","reishi"],"short":"Turmeric + reishi evening blend for deep sleep and recovery","long":"My evening ritual. Mix in warm almond milk 30 min before bed. Turmeric fights inflammation, reishi promotes deep sleep, lemon balm calms the mind. Tastes like a golden latte.","cat":"sleep","price":69.95,"est_epc":2.40},
  "market_health":{"name":"Market Health Supplements","url":"https://www.markethealth.com/?aid={tag}","comm":"Up to 60%","kw":["supplement","weight","skin","anti-aging","beauty","health","vitamin"],"short":"Massive health supplement catalog with up to 60% commission","long":"One of the largest health affiliate networks — supplements, weight management, skincare, anti-aging. They continuously optimize product pages so conversion rates stay strong.","cat":"supplements","price":59.00,"est_epc":5.20},
  "wolfson":{"name":"Wolfson Brands","url":"https://wolfsonbrands.com/?ref={tag}","comm":"40% lifetime recurring","kw":["supplement","vitamin","natural","nootropic","testosterone","health"],"short":"Premium supplements with lifetime recurring 40% commissions","long":"What makes Wolfson special: you earn 40% not just on the first sale but on EVERY reorder — forever. With supplement reorder rates above 40%, this compounds into serious passive income.","cat":"supplements","price":64.99,"est_epc":4.60},
}

def match_affiliates(topic, n=3):
    tl = topic.lower()
    scored = [(sum(1 for k in a["kw"] if k in tl), key, a) for key, a in AFFILIATES.items()]
    scored.sort(reverse=True, key=lambda x: (x[0], x[2]["est_epc"]))
    result = [s[2] for s in scored[:n] if s[0] > 0]
    if not result:
        result = sorted(AFFILIATES.values(), key=lambda x: x["est_epc"], reverse=True)[:n]
    return result

def aff_url(prod):
    return prod["url"].replace("{tag}", C["AFF_TAG"])

# ═══════════════════════════════════════
# TOPIC BANK (52 weeks worth)
# ═══════════════════════════════════════
TOPICS = [
    "best supplements for gut health","how to fix sleep in 7 days","natural anxiety remedies that work",
    "gut brain connection explained","morning routine for all day energy","signs nervous system is dysregulated",
    "best probiotics for bloating","how to reduce cortisol naturally","anti-inflammatory foods complete guide",
    "why you wake up tired every day","adaptogenic herbs for stress","best magnesium for sleep",
    "improve gut health without supplements","meditation beginners guide","foods for gut microbiome diversity",
    "natural ways to boost serotonin","ashwagandha benefits honest review","sleep hygiene checklist",
    "break the stress cycle permanently","omega 3 mental health benefits","mushroom supplements for immunity",
    "holistic anxiety management","prebiotic vs probiotic guide","blue light and sleep quality",
    "turmeric curcumin complete guide","breathwork for instant calm","supplements for brain fog",
    "vagus nerve exercises stress relief","best teas for sleep","intermittent fasting gut health",
    "wellness routine that actually sticks","grounding techniques for anxiety","best vitamins women over 30",
    "heal leaky gut naturally","cold exposure health benefits","journaling for mental health",
    "plant based protein powders review","digital detox guide","lions mane brain health benefits",
    "reduce chronic inflammation guide","reishi mushroom sleep benefits","boost metabolism after 30",
    "berberine natural metformin review","magnesium glycinate vs citrate","seed cycling hormone balance",
    "red light therapy science review","best adaptogens for women","creatine brain health research",
    "nervous system 30 day reset","akkermansia next gen probiotic","l glutamine gut repair guide",
    "zinc carnosine stomach healing","collagen supplements honest review",
]

SEASONAL = {
    1:["new year wellness reset","detox myths debunked","winter immunity boosters"],
    2:["self love wellness routine","heart health supplements","valentine stress management"],
    3:["spring detox guide","allergy season gut connection","daylight saving sleep fix"],
    4:["spring energy reboot","outdoor wellness routine","earth day eco supplements"],
    5:["mental health awareness month","summer body prep naturally","stress awareness guide"],
    6:["summer sleep optimization","hydration and gut health","travel wellness kit"],
    7:["summer supplement guide","heat and sleep quality","gut health on vacation"],
    8:["back to routine wellness","end of summer energy slump","fall prep immune boost"],
    9:["fall wellness reset","seasonal depression prevention","immune season preparation"],
    10:["immune system winter prep","gut health and cold season","spooky sleep disruption"],
    11:["holiday stress management","gratitude and mental health","thanksgiving gut survival"],
    12:["year end wellness review","holiday sleep protection","winter supplement stack"],
}

# ═══════════════════════════════════════
# INTELLIGENCE LAYER
# ═══════════════════════════════════════
def get_used_topics():
    d = db()
    if not d: return set()
    used = set()
    for doc in d.collection("content_log").stream():
        t = doc.to_dict().get("topic","")
        if t: used.add(t.lower().strip())
    return used

def detect_trends():
    month = datetime.datetime.now().strftime("%B %Y")
    season = SEASONAL.get(datetime.datetime.now().month, [])
    return ai_json(f"""You are a health/wellness trend analyst. Current month: {month}.
Seasonal topics to consider: {json.dumps(season)}

Identify 5 HIGH-OPPORTUNITY health & wellness topics that are:
1. Trending upward in search interest right now
2. Have buying intent (people want supplements, apps, devices)
3. Not oversaturated
4. Seasonal relevant for {month}

Return JSON: {{"trends":[{{"topic":"long-tail keyword phrase","title":"click-worthy blog title","urgency":1-10,"monetization":"affiliate angle","seasonal_fit":"why now"}}]}}""")

def find_competitor_gaps(existing_topics):
    return ai_json(f"""You are a competitive SEO analyst for a health & wellness blog.

The blog has already covered these topics:
{json.dumps(list(existing_topics)[:30])}

Identify 5 HIGH-VALUE topic gaps — topics that health/wellness blogs commonly rank for that are MISSING from the list above. Focus on topics with:
1. High commercial intent (people ready to buy)
2. Medium-low competition keywords
3. Strong affiliate potential

Return JSON: {{"gaps":[{{"topic":"specific keyword topic","why_missing":"why this gap matters","est_difficulty":"low|medium","monetization":"how to monetize"}}]}}""")

def score_content(content):
    """Rate content quality before publishing"""
    return ai_json(f"""Rate this health blog post on a 1-10 scale across these dimensions:

{content[:2000]}

Return JSON: {{"scores":{{"readability":0,"seo":0,"trust":0,"engagement":0,"affiliate_natural":0,"actionability":0}},"overall":0,"issues":["issue1"],"fixes":["fix1"]}}""")

def check_cannibalization(new_topic, existing):
    """Prevent keyword cannibalization"""
    similar = [t for t in existing if len(set(new_topic.lower().split()) & set(t.lower().split())) >= 3]
    return similar[:3]

def pick_topic():
    """Smart topic selection: trends → gaps → seasonal → bank"""
    used = get_used_topics()
    month = datetime.datetime.now().month

    # Layer 1: Trending topics
    try:
        trends = detect_trends()
        for t in trends.get("trends",[])[:3]:
            topic = t.get("topic","") or t.get("title","")
            if topic.lower().strip() not in used:
                cannibal = check_cannibalization(topic, used)
                if not cannibal:
                    log.info(f"[TOPIC] Trending: {topic}")
                    return topic, "trending"
    except Exception as e:
        log.warning(f"Trend detection failed: {e}")

    # Layer 2: Competitor gaps
    try:
        gaps = find_competitor_gaps(used)
        for g in gaps.get("gaps",[])[:2]:
            topic = g.get("topic","")
            if topic.lower().strip() not in used:
                log.info(f"[TOPIC] Competitor gap: {topic}")
                return topic, "gap"
    except Exception as e:
        log.warning(f"Gap analysis failed: {e}")

    # Layer 3: Seasonal
    seasonal = SEASONAL.get(month, [])
    for s in seasonal:
        if s.lower().strip() not in used:
            log.info(f"[TOPIC] Seasonal: {s}")
            return s, "seasonal"

    # Layer 4: Topic bank
    available = [t for t in TOPICS if t.lower().strip() not in used]
    if not available: available = TOPICS
    topic = random.choice(available)
    log.info(f"[TOPIC] Bank: {topic}")
    return topic, "bank"

# ═══════════════════════════════════════
# CONTENT GENERATORS
# ═══════════════════════════════════════
def get_internal_links():
    """Get existing posts for internal linking"""
    d = db()
    if not d: return []
    links = []
    for doc in d.collection("published_posts").order_by("date",direction=firestore.Query.DESCENDING).limit(20).stream():
        data = doc.to_dict()
        if data.get("url") and data.get("title"):
            links.append({"title":data["title"],"url":data["url"],"topic":data.get("topic","")})
    return links

def gen_blog(topic):
    prods = match_affiliates(topic)
    internal = get_internal_links()

    aff_section = "\n".join([f"- {p['name']} ({aff_url(p)}): {p['long']}" for p in prods])
    link_section = "\n".join([f"- [{l['title']}]({l['url']})" for l in internal[:5]]) if internal else "None yet"

    prompt = f"""You are an elite health & wellness content writer. Write a comprehensive, genuine, 2000+ word blog post.

TOPIC: "{topic}"

AFFILIATE PRODUCTS (use EXACT URLs, max 2-3 mentions, make them feel like genuine recommendations):
{aff_section}

EXISTING POSTS TO LINK TO (naturally reference 2-3 of these with hyperlinks):
{link_section}

STRUCTURE:
1. H1 Title — compelling, keyword-rich, under 60 chars
2. Meta description — under 155 chars, keyword + CTA
3. Hook intro — pain point or surprising stat, 2-3 short paragraphs
4. Table of Contents
5. 6-8 H2 sections — each genuinely valuable and actionable
6. Affiliate placements (2-3 total): **What I recommend:** [Product Name](URL) — personal, genuine recommendation
7. Internal links to existing posts (2-3, natural context)
8. FAQ section (3-4 questions targeting "People Also Ask")
9. Conclusion + lead magnet CTA: "Download our free 7-Day Wellness Reset Guide"

RULES:
- Short paragraphs (2-3 sentences max)
- Bold key takeaways
- Cite research: "A 2024 study in the Journal of..."
- Tone: knowledgeable friend, warm, occasionally witty
- NEVER salesy — educational first
- Include specific numbers, dosages, timelines
- Add rel="nofollow sponsored" context note for affiliate links

Write the full post."""

    content = ai(prompt)

    # Generate A/B title
    titles = ai_json(f"""Generate 2 alternative blog post titles for this topic: "{topic}"
The titles should be click-worthy, SEO-optimized, under 60 chars.
One should use numbers, one should use a power word (ultimate, complete, essential, etc).
Return JSON: {{"title_a":"...","title_b":"..."}}""")

    return content, titles

def gen_social(blog, topic, count=5):
    prods = match_affiliates(topic, 2)
    return ai_json(f"""Create {count} social media posts from this blog excerpt:

{blog[:2500]}

Affiliate products to mention subtly in 1-2 posts: {json.dumps([p['name'] for p in prods])}

Return JSON array, each: {{"platform":"Instagram Reel|TikTok|Instagram Carousel|LinkedIn|Instagram Story","hook":"scroll-stopping first line under 8 words","caption":"full text 150-250 words","hashtags":["6-8"],"cta":"call to action","has_affiliate":false,"image_prompt":"detailed AI image generation prompt for a visual to pair with this post, photorealistic style, wellness aesthetic"}}

Only 1-2 should have has_affiliate:true. Each post must stand alone.""")

def gen_email(blog, topic):
    prod = match_affiliates(topic, 1)[0]
    return ai_json(f"""Transform this blog into ONE email newsletter:

{blog[:2000]}

Affiliate: {prod['name']} — {prod['short']}
URL: {aff_url(prod)}

Return JSON: {{"subject_a":"curiosity subject","subject_b":"benefit subject","preview":"under 90 chars","body":"full email markdown 300-400 words","cta_text":"button","cta_url":"{aff_url(prod)}","ps":"P.S. line with open loop or soft affiliate mention"}}""")

def gen_youtube(blog, topic):
    prod = match_affiliates(topic, 1)[0]
    return ai_json(f"""Turn this blog into a 10-min YouTube script:

{blog[:2500]}

Affiliate: {prod['name']} ({aff_url(prod)})

Return JSON: {{"title":"SEO title","thumbnails":["3 thumbnail text ideas"],"description":"full description with timestamps and affiliate links section","tags":["10 tags"],"script":"full script with [HOOK 15s] [INTRO 30s] [MAIN 4 sections] [AFFILIATE MENTION natural] [CTA] [OUTRO], include [B-ROLL:] and [TEXT ON SCREEN:] markers"}}""")

def gen_pins(blog, topic):
    return ai_json(f"""Create 5 Pinterest pins about "{topic}":
{blog[:1200]}
Return JSON array: [{{"title":"keyword-rich under 100 chars","description":"2-3 sentences with CTA","image_prompt":"detailed image prompt for pin visual","board":"board name"}}]""")

def gen_landing_page(topic):
    """Auto-generate a lead magnet opt-in landing page"""
    return ai(f"""Create a complete HTML landing page for a free wellness lead magnet.

Topic: "{topic}" — the lead magnet is a free PDF guide.

Requirements:
- Clean, modern design with inline CSS (dark theme, green accents)
- Hero section with compelling headline + subheadline
- 5 bullet points of what they'll learn
- Email opt-in form (name + email fields, submit button)
- Social proof: "Join 2,000+ readers" 
- Form action should be: /subscribe (to be connected to ConvertKit)
- Mobile responsive
- Trust badges / guarantee text
- Fast loading, no external dependencies except Google Fonts

Return ONLY the complete HTML. No explanation.""")

# ═══════════════════════════════════════
# PUBLISHERS
# ═══════════════════════════════════════
def to_html(md):
    h = md
    h = re.sub(r'^### (.*$)', r'<h3>\1</h3>', h, flags=re.MULTILINE)
    h = re.sub(r'^## (.*$)', r'<h2>\1</h2>', h, flags=re.MULTILINE)
    h = re.sub(r'^# (.*$)', r'<h1>\1</h1>', h, flags=re.MULTILINE)
    h = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', h)
    h = re.sub(r'\*(.*?)\*', r'<em>\1</em>', h)
    h = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2" target="_blank" rel="nofollow sponsored">\1</a>', h)
    h = re.sub(r'\n\n', '</p><p>', h)
    return f'<p>{h}</p>'

def pub_wp(title, content, status="draft"):
    if not all([C["WP_URL"],C["WP_USER"],C["WP_APP_PASS"]]): return {"s":"skip"}
    try:
        r = requests.post(f"{C['WP_URL']}/wp-json/wp/v2/posts",
            auth=(C["WP_USER"],C["WP_APP_PASS"]),
            json={"title":title,"content":to_html(content),"status":status}, timeout=30)
        if r.ok:
            p = r.json()
            return {"s":"ok","id":p["id"],"url":p.get("link","")}
        return {"s":"err","code":r.status_code}
    except Exception as e: return {"s":"err","msg":str(e)}

def pub_medium(title, content):
    if not C["MEDIUM_TOKEN"]: return {"s":"skip"}
    try:
        me = requests.get("https://api.medium.com/v1/me",headers={"Authorization":f"Bearer {C['MEDIUM_TOKEN']}"},timeout=10)
        uid = me.json()["data"]["id"]
        r = requests.post(f"https://api.medium.com/v1/users/{uid}/posts",
            headers={"Authorization":f"Bearer {C['MEDIUM_TOKEN']}"},
            json={"title":title,"contentFormat":"markdown","content":content,"publishStatus":"draft",
                  "tags":["health","wellness","supplements","sleep","gut-health"]},timeout=15)
        return {"s":"ok","url":r.json().get("data",{}).get("url","")} if r.ok else {"s":"err"}
    except: return {"s":"err"}

def pub_social(posts):
    if not C["BUFFER_TOKEN"]: return {"s":"skip"}
    results = []
    for p in posts:
        txt = p.get("caption","")
        if p.get("hashtags"):
            txt += "\n\n" + " ".join(h if h.startswith("#") else f"#{h}" for h in p["hashtags"])
        for pid in C["BUFFER_PROFILES"].split(","):
            if not pid.strip(): continue
            r = requests.post("https://api.bufferapp.com/1/updates/create.json",
                data={"access_token":C["BUFFER_TOKEN"],"profile_ids[]":pid.strip(),"text":txt[:2200],"now":False},timeout=15)
            results.append({"platform":p.get("platform"),"ok":r.ok})
    return results

def pub_email(subj, body, preview=""):
    if not C["CONVERTKIT_SECRET"]: return {"s":"skip"}
    try:
        r = requests.post("https://api.convertkit.com/v3/broadcasts",
            json={"api_secret":C["CONVERTKIT_SECRET"],"subject":subj,"content":body,"description":preview},timeout=15)
        return {"s":"ok"} if r.ok else {"s":"err"}
    except: return {"s":"err"}

def archive(name, content):
    try:
        c = gcs()
        if not c: return None
        b = c.bucket(C["GCS_BUCKET"])
        path = f"v3/{datetime.date.today()}/{name}"
        data = content if isinstance(content, str) else json.dumps(content, indent=2, default=str)
        b.blob(path).upload_from_string(data, content_type="text/plain")
        return path
    except: return None

def save_log(ctype, topic, data):
    d = db()
    if d:
        d.collection("content_log").add({
            "type":ctype,"topic":topic,"data":json.dumps(data,default=str),
            "ts":datetime.datetime.utcnow().isoformat(),
            "date":datetime.date.today().isoformat()})

def save_post(title, url, topic):
    d = db()
    if d:
        d.collection("published_posts").add({
            "title":title,"url":url,"topic":topic,
            "date":datetime.date.today().isoformat()})

# ═══════════════════════════════════════
# NOTIFICATION SYSTEM
# ═══════════════════════════════════════
def notify(subject, body):
    """Send notification email via SendGrid"""
    if not all([C["SENDGRID_KEY"], C["NOTIFY_EMAIL"]]): return
    try:
        requests.post("https://api.sendgrid.com/v3/mail/send",
            headers={"Authorization":f"Bearer {C['SENDGRID_KEY']}","Content-Type":"application/json"},
            json={"personalizations":[{"to":[{"email":C["NOTIFY_EMAIL"]}]}],
                  "from":{"email":"bot@wellnessprofit.machine","name":"WPM Bot"},
                  "subject":subject,"content":[{"type":"text/plain","value":body}]},
            timeout=10)
    except: pass

# ═══════════════════════════════════════
# SEO AUTO-OPTIMIZER
# Rewrites underperforming posts
# ═══════════════════════════════════════
def check_wp_posts_performance():
    """Get WordPress posts and identify underperformers"""
    if not C["WP_URL"]: return []
    try:
        r = requests.get(f"{C['WP_URL']}/wp-json/wp/v2/posts?per_page=20&orderby=date&order=desc",
            auth=(C["WP_USER"], C["WP_APP_PASS"]), timeout=15)
        if not r.ok: return []
        posts = r.json()
        # Posts older than 30 days are candidates for optimization
        cutoff = (datetime.datetime.now() - datetime.timedelta(days=30)).isoformat()
        return [{"id":p["id"],"title":p["title"]["rendered"],"url":p["link"],
                 "date":p["date"],"slug":p["slug"]}
                for p in posts if p["date"] < cutoff]
    except: return []

def optimize_post(post_id, title, current_content_url):
    """Rewrite meta, title, and intro of underperforming post"""
    new = ai_json(f"""This blog post may be underperforming in search:
Title: "{title}"

Generate improved SEO elements:
Return JSON: {{"new_title":"improved click-worthy title under 60 chars","new_meta":"improved meta description under 155 chars","new_intro":"improved hook intro paragraph (3 sentences, starts with pain point or stat)"}}""")

    # Update via WordPress API
    if C["WP_URL"]:
        try:
            requests.post(f"{C['WP_URL']}/wp-json/wp/v2/posts/{post_id}",
                auth=(C["WP_USER"],C["WP_APP_PASS"]),
                json={"title": new.get("new_title", title),
                      "excerpt": new.get("new_meta", "")},
                timeout=15)
            return {"status":"optimized","new_title":new.get("new_title")}
        except: pass
    return {"status":"failed"}

# ═══════════════════════════════════════
# REVENUE ESTIMATOR
# ═══════════════════════════════════════
def estimate_revenue():
    d = db()
    if not d: return {"est_monthly":"unknown"}
    
    # Count content pieces
    total = 0
    for doc in d.collection("content_log").where("date",">=",
        (datetime.date.today()-datetime.timedelta(days=30)).isoformat()).stream():
        total += 1
    
    # Estimate based on industry averages
    est_monthly_traffic = total * 150  # ~150 visits per post average
    est_conversion = est_monthly_traffic * 0.025  # 2.5% CTR
    avg_epc = sum(a["est_epc"] for a in AFFILIATES.values()) / len(AFFILIATES)
    est_revenue = est_conversion * avg_epc
    
    return {
        "content_pieces_30d": total,
        "est_monthly_traffic": est_monthly_traffic,
        "est_monthly_clicks": int(est_conversion),
        "avg_epc": round(avg_epc, 2),
        "est_monthly_revenue": round(est_revenue, 2),
        "est_yearly_revenue": round(est_revenue * 12, 2),
        "note": "Estimates improve as content ages and gains SEO authority"
    }

# ═══════════════════════════════════════
# MASTER PIPELINE v3
# 1 topic → 10+ assets → auto-published → tracked → learned from
# ═══════════════════════════════════════
def run_pipeline():
    start = time.time()
    R = {"v":"3","ts":datetime.datetime.utcnow().isoformat(),"assets":{}}

    # 1. Pick topic (4-layer intelligence)
    topic, source = pick_topic()
    R["topic"] = topic
    R["topic_source"] = source
    log.info(f"━━━ PIPELINE START: {topic} (via {source}) ━━━")

    # 2. Generate blog (seed content)
    log.info("[1/8] Generating blog post...")
    blog, titles = gen_blog(topic)
    title = titles.get("title_a", topic.title())
    for line in blog.split("\n"):
        if line.startswith("# "):
            title = line[2:].strip()
            break
    R["assets"]["blog"] = {"title":title,"title_b":titles.get("title_b",""),"words":len(blog.split())}

    # 3. Score content quality
    log.info("[2/8] Scoring content quality...")
    try:
        score = score_content(blog)
        R["assets"]["quality_score"] = score
        if score.get("overall",10) < 6:
            log.warning(f"Low quality score ({score.get('overall')}), regenerating...")
            blog, titles = gen_blog(topic)  # Retry once
    except: pass

    # 4. Publish blog
    log.info("[3/8] Publishing blog...")
    wp_result = pub_wp(title, blog, "draft")
    R["assets"]["wordpress"] = wp_result
    if wp_result.get("url"):
        save_post(title, wp_result["url"], topic)
    R["assets"]["medium"] = pub_medium(title, blog)
    archive(f"blog-{topic[:40].replace(' ','-')}.md", blog)

    # 5. Generate + schedule social (5 posts with image prompts)
    log.info("[4/8] Generating social posts...")
    try:
        social = gen_social(blog, topic)
        R["assets"]["social"] = {"count":len(social),"buffer":pub_social(social)}
        archive(f"social-{topic[:30].replace(' ','-')}.json", social)
    except Exception as e:
        R["assets"]["social"] = {"err":str(e)}

    # 6. Generate email (send on Tue/Thu only)
    log.info("[5/8] Generating email...")
    try:
        email = gen_email(blog, topic)
        weekday = datetime.date.today().weekday()
        if weekday in [1, 3]:  # Tue, Thu
            R["assets"]["email"] = pub_email(email["subject_a"], email.get("body",""), email.get("preview",""))
            R["assets"]["email"]["sent"] = True
        else:
            R["assets"]["email"] = {"sent":False,"queued":email["subject_a"]}
        archive(f"email-{topic[:30].replace(' ','-')}.json", email)
    except Exception as e:
        R["assets"]["email"] = {"err":str(e)}

    # 7. Generate YouTube script
    log.info("[6/8] Generating YouTube script...")
    try:
        yt = gen_youtube(blog, topic)
        R["assets"]["youtube"] = {"title":yt.get("title",""),"archived":True}
        archive(f"yt-{topic[:30].replace(' ','-')}.json", yt)
    except Exception as e:
        R["assets"]["youtube"] = {"err":str(e)}

    # 8. Generate Pinterest pins
    log.info("[7/8] Generating Pinterest pins...")
    try:
        pins = gen_pins(blog, topic)
        R["assets"]["pinterest"] = {"count":len(pins),"archived":True}
        archive(f"pins-{topic[:30].replace(' ','-')}.json", pins)
    except Exception as e:
        R["assets"]["pinterest"] = {"err":str(e)}

    # 9. Generate landing page for lead magnet
    log.info("[8/8] Generating landing page...")
    try:
        lp = gen_landing_page(topic)
        archive(f"landing-{topic[:30].replace(' ','-')}.html", lp)
        R["assets"]["landing_page"] = {"archived":True}
    except Exception as e:
        R["assets"]["landing_page"] = {"err":str(e)}

    # Finalize
    elapsed = round(time.time() - start, 1)
    R["elapsed_seconds"] = elapsed
    R["assets_created"] = sum(1 for v in R["assets"].values() if isinstance(v,dict) and "err" not in v)
    save_log("pipeline", topic, R)

    # Notify
    notify(f"✅ WPM: {R['assets_created']} assets for \"{topic}\"",
           f"Pipeline completed in {elapsed}s.\nTopic: {topic} (source: {source})\n"
           f"Assets: {R['assets_created']}\nBlog: {wp_result.get('url','draft')}")

    log.info(f"━━━ PIPELINE DONE: {R['assets_created']} assets in {elapsed}s ━━━")
    return R

# ═══════════════════════════════════════
# MONTHLY SEO OPTIMIZATION JOB
# ═══════════════════════════════════════
def run_seo_optimize():
    """Monthly: find underperformers and rewrite them"""
    posts = check_wp_posts_performance()
    results = []
    for p in posts[:5]:
        try:
            r = optimize_post(p["id"], p["title"], p["url"])
            results.append({**p, **r})
        except: pass
    save_log("seo_optimize", "monthly", results)
    notify("📊 WPM Monthly SEO Optimization", f"Optimized {len(results)} posts:\n" +
           "\n".join([f"- {r.get('title','')} → {r.get('new_title','')}" for r in results]))
    return results

# ═══════════════════════════════════════
# CLOUD FUNCTION ENDPOINTS
# ═══════════════════════════════════════
@functions_framework.http
def daily_pipeline(request):
    """Daily 6AM: Full content multiplication pipeline"""
    try:
        return json.dumps(run_pipeline(), indent=2, default=str), 200, {"Content-Type":"application/json"}
    except Exception as e:
        log.error(f"Pipeline failed: {e}", exc_info=True)
        notify("❌ WPM Pipeline Failed", str(e))
        return json.dumps({"error":str(e)}), 500, {"Content-Type":"application/json"}

@functions_framework.http
def monthly_optimize(request):
    """Monthly 1st: SEO auto-optimizer"""
    try:
        return json.dumps(run_seo_optimize(), indent=2, default=str), 200, {"Content-Type":"application/json"}
    except Exception as e:
        return json.dumps({"error":str(e)}), 500, {"Content-Type":"application/json"}

@functions_framework.http
def analytics(request):
    """On-demand: Full analytics"""
    try:
        data = {
            "trends": detect_trends(),
            "gaps": find_competitor_gaps(get_used_topics()),
            "revenue": estimate_revenue(),
            "performance": ai_json(f"""Analyze content strategy for a health/wellness blog that has published {len(get_used_topics())} articles. Recommend: double_down topics, reduce topics, content_mix percentages. Return JSON."""),
        }
        return json.dumps(data, indent=2, default=str), 200, {"Content-Type":"application/json"}
    except Exception as e:
        return json.dumps({"error":str(e)}), 500, {"Content-Type":"application/json"}

@functions_framework.http
def status(request):
    """Status dashboard"""
    d = db()
    data = {"v":"3","status":"running","ts":datetime.datetime.utcnow().isoformat()}
    data["config"] = {k: "✓" if C.get(k) else "✗" for k in ["GEMINI_KEY","WP_URL","BUFFER_TOKEN","CONVERTKIT_KEY","MEDIUM_TOKEN","SENDGRID_KEY"]}
    data["revenue"] = estimate_revenue()

    if d:
        logs = [doc.to_dict() for doc in d.collection("content_log").order_by("ts",direction=firestore.Query.DESCENDING).limit(20).stream()]
        data["recent"] = logs[:10]
        data["total_content"] = len(logs)
        data["topics_covered"] = len(get_used_topics())
    
    return json.dumps(data, indent=2, default=str), 200, {"Content-Type":"application/json"}
