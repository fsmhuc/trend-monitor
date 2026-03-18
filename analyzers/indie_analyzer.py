import re
from datetime import datetime


# ---------------------------------------------------------------------------
# Filter keyword lists
# ---------------------------------------------------------------------------

B2B_KEYWORDS = [
    "enterprise", "workplace", "slack integration", "sso", "single sign-on",
    "b2b", "crm", "sales pipeline", "churn", "sales team", "lead generation",
    "account management", "customer success", "revenue operations",
]

# "analytics" and "saas" alone are too broad; use compound phrases
B2B_PHRASE_PAIRS = [
    ("analytics", "team"),
    ("analytics", "enterprise"),
    ("saas", "b2b"),
    ("saas", "enterprise"),
    ("platform", "enterprise"),
]

COMPLEX_KEYWORDS = ["hardware", "blockchain", "crypto", "infrastructure"]
EDUCATIONAL_KEYWORDS = ["school", "classroom", "lms"]

# GitHub repos that are developer libraries, not products
GITHUB_LIBRARY_SIGNALS = [
    "npm install", "pip install", "cargo add", "gem install",
    "library for", "framework for", "use as a dependency",
    "import from", "package for", "#include",
]

# ---------------------------------------------------------------------------
# Domain detection table
# (domain_id, keywords, user_persona, pain_description)
# Checked in priority order against name + description (lowercased).
# ---------------------------------------------------------------------------

_DOMAIN_TABLE = [
    ("fortune_telling",
     ["fortune", "tarot", "astrology", "horoscope", "fate", "zodiac",
      "psychic", "divination", "palm reading", "numerology", "birth chart", "crystal ball"],
     "spirituality enthusiasts and people curious about fortune telling or astrology",
     "They want personalised spiritual guidance or entertainment without expensive readings"),

    ("browser_extension",
     ["chrome extension", "browser extension", "firefox addon", "firefox extension", "manifest v3"],
     "everyday browser users who want to enhance their web experience",
     "They repeat tedious browser actions daily that a one-click extension could eliminate"),

    ("image_generation",
     ["image generation", "text to image", "generate image", "ai art",
      "stable diffusion", "dall-e", "midjourney", "art generator", "ai image"],
     "designers, content creators, and non-artists who need visuals quickly",
     "Creating custom images is slow and expensive; AI cuts this to seconds"),

    ("video_ai",
     ["video", "youtube", "subtitles", "transcript", "caption", "clip", "reel", "short video"],
     "content creators, video editors, and YouTubers",
     "Video production and editing takes enormous time; AI compresses the workflow"),

    ("writing_ai",
     ["copywriting", "essay", "blog post", "draft", "proofread", "grammar check",
      "text generation", "ai writer", "ai writing"],
     "writers, marketers, students, and professionals who produce written content regularly",
     "Writing from scratch is slow and mentally draining; they need a starting point or polishing"),

    ("social_media",
     ["twitter", "instagram", "tiktok", "linkedin", "social media",
      "post scheduler", "tweet", "followers", "engagement"],
     "social media managers, creators, and marketers",
     "Consistent posting is exhausting; they need scheduling, idea generation, or analytics"),

    ("developer_tool",
     ["developer", "engineer", "programmer", "coder", "devops",
      "git", "debug", "terminal", "cli", "ide", "vscode", "api client", "open source tool"],
     "software developers and engineers",
     "Developer workflow has constant friction — this removes one specific bottleneck"),

    ("productivity",
     ["productivity", "focus", "pomodoro", "task manager", "todo",
      "organize", "planner", "habit tracker", "time management", "deep work"],
     "knowledge workers and students who struggle with focus or task organisation",
     "Distraction and poor prioritisation kill output; they need a simple, frictionless system"),

    ("health_wellness",
     ["health", "fitness", "meditation", "wellness", "sleep tracker",
      "nutrition", "workout", "mindfulness", "mental health"],
     "health-conscious individuals and fitness enthusiasts",
     "Tracking habits and staying consistent is hard without personalised, gentle nudges"),

    ("language_learning",
     ["language learning", "vocabulary", "grammar", "learn spanish", "learn japanese",
      "flashcard", "anki", "language practice", "translation app"],
     "language learners at all levels",
     "Traditional language apps feel like homework; they want bite-sized, fun practice"),

    ("finance",
     ["budget", "expense tracker", "personal finance", "invest", "tax", "invoice", "accounting"],
     "individuals and freelancers managing personal or small-business finances",
     "Tracking money manually is tedious and error-prone; they want automatic clarity"),

    ("ecommerce",
     ["ecommerce", "shopify", "dropship", "amazon seller", "product listing", "online store"],
     "e-commerce store owners and online sellers",
     "Running a store involves constant manual tasks that eat into profit margins"),

    ("data_viz",
     ["chart", "dashboard", "data visualization", "spreadsheet", "csv", "data analysis", "report builder"],
     "analysts and data-curious non-technical users who need clear insights",
     "Raw data is overwhelming; they need clean visualisations without writing code"),

    ("entertainment",
     ["game", "quiz", "trivia", "fun", "entertainment", "puzzle", "interactive story"],
     "casual users looking for engaging entertainment or fun interactive experiences",
     "Generic entertainment is passive; they want personalised, interactive experiences"),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_text(product):
    """Return a single lowercased string combining all text fields."""
    tags = product.get("tags", "")
    if isinstance(tags, list):
        tags = " ".join(tags)
    parts = [
        product.get("name", ""),
        product.get("title", ""),
        product.get("description", ""),
        product.get("tagline", ""),
        product.get("category", ""),
        tags,
    ]
    return " ".join(p for p in parts if p).lower()


def _detect_domain(product):
    """
    Return (domain_id, user_persona, pain_description) for a product.

    Checks name + description specifically (not tags/category) to keep
    domain detection tied to what the product actually *is*.
    """
    name = (product.get("name") or product.get("title") or "").lower()
    desc = (product.get("description") or product.get("tagline") or "").lower()
    combined = name + " " + desc
    source = product.get("_source", "")

    for domain_id, keywords, persona, pain in _DOMAIN_TABLE:
        if any(kw in combined for kw in keywords):
            return domain_id, persona, pain

    # GitHub repos without a clearer signal → developer tool
    if source == "github":
        return ("developer_tool",
                "software developers and open-source contributors",
                "They have a recurring pain in their development workflow that existing tools don't solve cleanly")

    return ("general",
            "general consumers looking for a specific solution",
            "They have a daily friction point with no good existing solution")


def _first_sentence(text):
    """Extract the first meaningful sentence from a description."""
    if not text:
        return ""
    # Split on period/exclamation/question, take first non-empty fragment
    parts = re.split(r"[.!?]", text)
    for part in parts:
        part = part.strip()
        if len(part) > 15:
            return part
    return text[:120].strip()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def filter_unsuitable_products(all_products):
    """
    Filter products unsuitable for indie hackers.

    Input:  dict with keys: product_hunt, toolify, ai_tools,
                            chrome_extensions, github, hackernews
    Output: (suitable_list, filtered_out_list)
            filtered_out items have an extra 'filter_reason' key.
    """
    combined = []
    for source, products in all_products.items():
        if not isinstance(products, list):
            continue
        for p in products:
            item = dict(p)
            item.setdefault("_source", source)
            combined.append(item)

    suitable = []
    filtered_out = []

    for product in combined:
        text = _get_text(product)
        reason = None

        # 1. Hard B2B keywords
        for kw in B2B_KEYWORDS:
            if kw in text:
                reason = f"B2B keyword: '{kw}'"
                break

        # 2. B2B compound phrases ("analytics" alone is OK; "analytics + team" is not)
        if reason is None:
            for kw_a, kw_b in B2B_PHRASE_PAIRS:
                if kw_a in text and kw_b in text:
                    reason = f"B2B combination: '{kw_a}' + '{kw_b}'"
                    break

        # 3. Too-complex domains
        if reason is None:
            for kw in COMPLEX_KEYWORDS:
                if kw in text:
                    reason = f"Too complex for indie: '{kw}'"
                    break

        # 4. Institutional / educational
        if reason is None:
            for kw in EDUCATIONAL_KEYWORDS:
                if kw in text:
                    reason = f"Institutional/educational: '{kw}'"
                    break

        # 5. GitHub library/framework (not a usable product)
        if reason is None and product.get("_source") == "github":
            desc = (product.get("description") or "").lower()
            for signal in GITHUB_LIBRARY_SIGNALS:
                if signal in desc:
                    reason = f"GitHub library/package, not a product: '{signal}'"
                    break

        if reason:
            item = dict(product)
            item["filter_reason"] = reason
            filtered_out.append(item)
        else:
            suitable.append(product)

    return suitable, filtered_out


def score_product(product):
    """
    Score a product 1–5 on four dimensions.

    Returns dict with individual scores and total_score (max 20).
    """
    text = _get_text(product)
    source = product.get("_source", "")
    domain_id, _, _ = _detect_domain(product)

    # --- Tech difficulty (lower = easier to build) ---
    if domain_id == "browser_extension" or source == "chrome_extensions":
        tech_difficulty = 1  # HTML/JS/CSS
    elif any(kw in text for kw in ["no-code", "nocode", "template", "drag and drop"]):
        tech_difficulty = 1
    elif domain_id in ("fortune_telling", "entertainment", "language_learning"):
        tech_difficulty = 2  # data + simple UI
    elif any(kw in text for kw in ["ai", "gpt", "llm", "openai", "claude", "anthropic"]):
        tech_difficulty = 3  # AI API wrapper + UX
    elif any(kw in text for kw in ["distributed", "real-time", "compiler", "kernel", "embedded"]):
        tech_difficulty = 5
    else:
        tech_difficulty = 2

    # --- User acquisition / viral potential (higher = easier) ---
    if domain_id in ("fortune_telling", "entertainment"):
        user_acquisition = 5  # shareable results
    elif domain_id == "browser_extension" or source == "chrome_extensions":
        user_acquisition = 4  # Chrome Web Store distribution
    elif domain_id in ("writing_ai", "image_generation", "video_ai"):
        user_acquisition = 4  # AI directories + shareable output
    elif any(kw in text for kw in ["viral", "share", "referral"]):
        user_acquisition = 5
    elif source == "github":
        user_acquisition = 3  # HN / dev communities
    else:
        user_acquisition = 2

    # --- Revenue potential (higher = more monetisable) ---
    if any(kw in text for kw in ["subscription", "monthly", "annual", "/mo", "/yr", "per month"]):
        revenue_potential = 4
    elif any(kw in text for kw in ["freemium", "free plan", "upgrade", "premium"]):
        revenue_potential = 3
    elif any(kw in text for kw in ["one-time", "lifetime", "pay once"]):
        revenue_potential = 2
    elif domain_id in ("fortune_telling", "entertainment"):
        revenue_potential = 3  # credits / microtransactions
    elif domain_id in ("finance", "ecommerce", "productivity"):
        revenue_potential = 4  # high willingness to pay
    else:
        revenue_potential = 2

    # --- Indie-friendly (higher = more soloable) ---
    if domain_id == "browser_extension" or source == "chrome_extensions":
        indie_friendly = 5
    elif any(kw in text for kw in ["simple", "minimal", "lightweight", "tiny", "micro"]):
        indie_friendly = 5
    elif domain_id in ("fortune_telling", "entertainment", "language_learning"):
        indie_friendly = 5  # content-driven, no ops team needed
    elif any(kw in text for kw in ["platform", "ecosystem", "suite"]):
        indie_friendly = 2
    elif source == "github":
        indie_friendly = 4  # OSS → SaaS is a known solo path
    else:
        indie_friendly = 3

    total_score = tech_difficulty + user_acquisition + revenue_potential + indie_friendly

    return {
        "tech_difficulty": tech_difficulty,
        "user_acquisition": user_acquisition,
        "revenue_potential": revenue_potential,
        "indie_friendly": indie_friendly,
        "total_score": total_score,
    }


def deep_analyze_product(product, rank):
    """
    Generate a detailed, product-specific markdown analysis section.

    Every answer is derived from the actual product description and domain.
    Returns a formatted markdown string.
    """
    name = product.get("name") or product.get("title") or "Unknown Product"
    description = product.get("description") or product.get("tagline") or "No description available."
    url = product.get("url") or product.get("link") or product.get("website") or ""
    source = product.get("_source", "unknown")
    scores = product.get("_scores", {})

    url_line = f"[{url}]({url})" if url else "_URL not available_"
    text = _get_text(product)

    domain_id, user_persona, pain_description = _detect_domain(product)
    core_sentence = _first_sentence(description)

    # ------------------------------------------------------------------ #
    # 1. Who are the users?
    # ------------------------------------------------------------------ #
    if domain_id in ("developer_tool",) or source == "github":
        audience_type = "B2C prosumer / B2B small teams"
    elif domain_id in ("ecommerce", "data_viz"):
        audience_type = "B2C prosumers and small business owners (not enterprise)"
    else:
        audience_type = "B2C — individual users making a personal purchase decision"

    users = f"**{user_persona.capitalize()}** ({audience_type})."

    # ------------------------------------------------------------------ #
    # 2. Why do they need it?  (anchored to actual description)
    # ------------------------------------------------------------------ #
    pain_point = pain_description
    if core_sentence:
        pain_point += f'\n\n  > What the product says: _"{core_sentence}"_'

    # ------------------------------------------------------------------ #
    # 3. How does it find users?
    # ------------------------------------------------------------------ #
    if source == "chrome_extensions" or domain_id == "browser_extension":
        distribution = (
            "**Chrome Web Store** organic search is the primary channel — users search for a task "
            "and your extension appears. Submit to extension directories (extlib.io, alternativeto). "
            "Zero ongoing CAC once listed."
        )
    elif source == "github":
        distribution = (
            "**GitHub Trending** → HN 'Show HN' post → dev Twitter/X. The README *is* the landing page. "
            "Stars compound: once it trends, press coverage follows automatically."
        )
    elif domain_id == "fortune_telling":
        distribution = (
            "**Viral sharing** is the engine — users share their reading results on social media. "
            "Target SEO keywords like 'free tarot reading online', 'daily horoscope [zodiac]'. "
            "TikTok/Reels short demos can explode in the spirituality niche."
        )
    elif domain_id == "entertainment":
        distribution = (
            "**Shareable results** drive organic growth (quiz results, game scores). "
            "Post short demo clips on TikTok/Instagram Reels. "
            "Reddit communities (r/quiz, niche hobby subreddits) for targeted seeding."
        )
    elif domain_id in ("writing_ai", "image_generation", "video_ai"):
        distribution = (
            "**AI tool directories** (There's An AI For That, Futurepedia, Toolify) drive high-intent "
            "passive traffic. Product Hunt launch for initial spike. "
            "Before/after demos on Twitter/X — the output is inherently shareable."
        )
    elif source == "product_hunt":
        distribution = (
            "**Product Hunt community** for launch momentum. "
            "Follow with SEO content targeting the core use case and directory submissions. "
            "The PH badge adds credibility for cold outreach."
        )
    else:
        distribution = (
            "**SEO + community seeding**: write content targeting the core pain-point keyword, "
            "then engage in the niche's Reddit / Discord / Facebook Group. "
            "Direct DMs to potential users for early feedback and word-of-mouth."
        )

    # ------------------------------------------------------------------ #
    # 4. Business model & revenue estimate
    # ------------------------------------------------------------------ #
    if any(kw in text for kw in ["subscription", "monthly", "annual", "/mo", "/yr", "per month"]):
        biz_model = (
            "Subscription SaaS. In this niche, $7–$29/month is typical. "
            "At **500 paying users → $42K–$174K ARR**. Watch monthly churn — keep below 5%."
        )
    elif any(kw in text for kw in ["freemium", "free plan", "upgrade", "free tier"]):
        biz_model = (
            "Freemium. Free tier creates a large user base; paid tier unlocks limits or power features. "
            "Industry average: **2–5% free→paid conversion**. "
            "A $9–$19/month Pro plan is the sweet spot for this audience."
        )
    elif any(kw in text for kw in ["one-time", "lifetime", "pay once"]):
        biz_model = (
            "One-time purchase. Excellent for AppSumo / LTD deals to bootstrap early revenue. "
            "Lower LTV, but great launch momentum and zero churn overhead."
        )
    elif domain_id in ("fortune_telling", "entertainment"):
        biz_model = (
            "Free with credits / microtransactions, or freemium with a **$2.99–$4.99/month** "
            "'unlimited readings' tier. This audience converts well on impulse micro-purchases. "
            "Ad-supported free tier also viable at scale."
        )
    elif source == "github":
        biz_model = (
            "**Open-source core + hosted SaaS layer**. Revenue comes from the managed/hosted version "
            "($10–$50/month). The OSS version builds credibility, backlinks, and a user base "
            "that eventually upgrades for convenience."
        )
    else:
        biz_model = (
            "Monetisation model not explicit from public info. "
            "For indie viability, target freemium with a **$9–$29/month** paid tier. "
            "Validate willingness to pay before building the billing system."
        )

    # ------------------------------------------------------------------ #
    # 5. What can I learn?
    # ------------------------------------------------------------------ #
    learnings = []

    if domain_id == "fortune_telling":
        learnings.append(
            f"Spiritual / entertainment niches are vastly underserved by developers — "
            f"most builders ignore them, leaving them wide open."
        )
        learnings.append(
            "Users come back *daily* if the content feels personalised and fresh — "
            "retention is built-in if you add variety (daily draws, moon phases, etc.)."
        )
    elif domain_id in ("browser_extension",) or source == "chrome_extensions":
        learnings.append(
            "The Chrome Web Store is a search engine most developers forget to compete in — "
            "a well-optimised listing gets passive, recurring installs with zero ad spend."
        )
        learnings.append(
            "Extensions have structurally better retention than web apps: "
            "uninstalling requires deliberate effort, so users stick around."
        )
    elif domain_id in ("writing_ai", "image_generation", "video_ai"):
        learnings.append(
            "AI wrapper products succeed on UX, not model quality — the underlying AI is a commodity. "
            "The product is the workflow, the UI, and the presets."
        )
    elif source == "github":
        learnings.append(
            "OSS projects that solve a real pain can convert GitHub stars to paying SaaS users — "
            "the repo *is* the marketing funnel."
        )

    if not learnings:
        learnings.append(
            "Tight niche focus beats broad reach — the more specific the problem, "
            "the easier it is to find users who will pay."
        )
        learnings.append(
            "This product's single-purpose approach is the right indie instinct: "
            "one problem, one solution, one clear CTA."
        )

    # ------------------------------------------------------------------ #
    # 6. One-sentence pitch  (uses real description)
    # ------------------------------------------------------------------ #
    if core_sentence:
        pitch = (
            f"{name} helps {user_persona} by letting them "
            f"{core_sentence.lower().rstrip('.')}."
        )
    else:
        pitch = (
            f"{name} is the simplest way for {user_persona} "
            f"to {pain_description.lower().rstrip('.')}."
        )

    # ------------------------------------------------------------------ #
    # 7. Can I build it?
    # ------------------------------------------------------------------ #
    td = scores.get("tech_difficulty", 3)
    if source == "chrome_extensions" or domain_id == "browser_extension":
        buildable = (
            "**Yes** — Chrome extensions are HTML/CSS/JS. Any web developer can ship an MVP "
            "in a weekend. Google's Manifest V3 docs are excellent."
        )
    elif source == "github":
        buildable = (
            "**Yes, and the hard part is done** — it's open source. You can fork it, "
            "add a hosted layer (auth + Stripe billing), and launch a SaaS in 2–4 weeks."
        )
    elif td <= 2:
        buildable = (
            "**Yes** — low technical complexity. "
            "A solo developer could ship an MVP in 1–2 weeks using existing APIs and a simple UI."
        )
    elif td == 3:
        buildable = (
            "**Probably** — moderate complexity (AI API calls + basic UI). "
            "Use OpenAI / Claude API + a simple React or Next.js frontend. "
            "Expect 2–4 weeks for a solid, shippable MVP."
        )
    else:
        buildable = (
            "**Maybe** — higher complexity. Scope ruthlessly: build only the single core feature first, "
            "ignore everything else. Budget 1–3 months solo, or find a technical co-founder."
        )

    # ------------------------------------------------------------------ #
    # 8. How do I find users?
    # ------------------------------------------------------------------ #
    ua = scores.get("user_acquisition", 2)

    if domain_id == "fortune_telling":
        find_users = (
            "Post on **r/astrology**, **r/tarot**, **r/spirituality** — these are massive, "
            "active communities hungry for tools. Create TikTok videos showing a live reading. "
            "Target '[zodiac sign] daily horoscope' SEO — millions of monthly searches."
        )
    elif source == "chrome_extensions" or domain_id == "browser_extension":
        find_users = (
            "Optimise your **Chrome Web Store listing** (title + description for search terms). "
            "Post in subreddits relevant to the use case. "
            "Submit to ProductHunt and extension directories (extlib.io, chromeextensions.dev)."
        )
    elif source == "github" or domain_id == "developer_tool":
        find_users = (
            "Post a **'Show HN'** on Hacker News, tweet with a demo GIF, "
            "and post in relevant subreddits (r/programming, r/devtools, tool-specific subs). "
            "Write a blog post about the problem you solved — SEO + dev community sharing."
        )
    elif domain_id in ("writing_ai", "image_generation", "video_ai"):
        find_users = (
            "Submit to **There's An AI For That**, **Futurepedia**, and **Toolify** — "
            "these directories drive passive, high-intent traffic. "
            "Post a compelling before/after demo on Twitter/X to seed virality."
        )
    elif domain_id == "productivity":
        find_users = (
            "Post on **r/productivity** and **r/getdisciplined**. "
            "Write a 'how I fixed my workflow' blog post that naturally features the tool. "
            "Reach out to productivity-focused YouTubers or newsletter writers for an honest review."
        )
    elif ua >= 4:
        find_users = (
            "The built-in viral loop or SEO potential does the heavy lifting. "
            "Kick-start with a Product Hunt launch and submissions to relevant directories. "
            "Then let organic growth compound."
        )
    else:
        find_users = (
            "Write **SEO content** targeting the core pain-point keyword. "
            "Engage in niche Discord / Slack / Reddit communities where your target users hang out. "
            "Cold-DM 10–20 potential users on Twitter/LinkedIn and offer free beta access."
        )

    # ------------------------------------------------------------------ #
    # First step recommendation  (product-specific)
    # ------------------------------------------------------------------ #
    if domain_id == "fortune_telling":
        first_step = (
            f"Check Google Trends for 'free tarot reading online' and 'daily horoscope'. "
            f"If trending, build a dead-simple landing page with ONE free reading — no login required — "
            f"and post the link on r/astrology tonight."
        )
    elif source == "github":
        first_step = (
            f"Star the repo and run it locally. If it solves a real pain you have, "
            f"build a hosted version with a free tier and post 'Show HN'. "
            f"Let real usage tell you what to charge."
        )
    elif domain_id == "browser_extension" or source == "chrome_extensions":
        first_step = (
            f"Search the Chrome Web Store for similar extensions and read the **1-star reviews** — "
            f"that's your feature backlog. Build one clear improvement over the top competitor and launch."
        )
    else:
        first_step = (
            f"Search Reddit and Twitter for '{name}' or the core pain point. "
            f"Find 5–10 threads where people wish this existed or complain about current solutions. "
            f"DM those users — offer free early access in exchange for a 15-minute call."
        )

    lines = [
        f"## #{rank} — {name}",
        f"> Source: `{source}` | {url_line}",
        "",
        f"**Description:** {description}",
        "",
        "---",
        "",
        "### 1. Who are the users?",
        users,
        "",
        "### 2. Why do they need it?",
        pain_point,
        "",
        "### 3. How does it find users?",
        distribution,
        "",
        "### 4. Does it make money? How much?",
        biz_model,
        "",
        "### 5. What can I learn from this?",
        "\n".join(f"- {l}" for l in learnings),
        "",
        "### 6. One-sentence pitch",
        f"_{pitch}_",
        "",
        "### 7. Can I build it?",
        buildable,
        "",
        "### 8. How do I find users?",
        find_users,
        "",
        "---",
        "",
        f"💡 **First Step:** {first_step}",
        "",
    ]

    return "\n".join(lines)


def generate_indie_report(
    product_hunt_data,
    toolify_data,
    ai_tools_data,
    chrome_extensions_data,
    github_data,
    hn_data,
):
    """
    Generate a full indie hacker opportunity report in markdown.

    Returns a complete markdown string.
    """
    if isinstance(toolify_data, dict):
        toolify_list = toolify_data.get("new", []) + toolify_data.get("trending", [])
    elif isinstance(toolify_data, list):
        toolify_list = toolify_data
    else:
        toolify_list = []

    all_products = {
        "product_hunt": product_hunt_data or [],
        "toolify": toolify_list,
        "ai_tools": ai_tools_data or [],
        "chrome_extensions": chrome_extensions_data or [],
        "github": github_data or [],
        "hackernews": hn_data or [],
    }

    suitable, filtered_out = filter_unsuitable_products(all_products)

    for p in suitable:
        p["_scores"] = score_product(p)

    suitable.sort(key=lambda p: p["_scores"]["total_score"], reverse=True)

    top5 = suitable[:5]
    today = datetime.now().strftime("%Y-%m-%d")
    total_input = sum(len(v) for v in all_products.values())

    sections = [
        f"# Indie Hacker Opportunity Report — {today}",
        "",
        f"Analysed **{total_input}** products across 6 sources. "
        f"**{len(suitable)}** passed the indie filter; **{len(filtered_out)}** were removed.",
        "",
    ]

    # --- Section 1: Filtered Out ---
    sections += ["---", "", "## 🚫 Filtered Out", ""]
    if filtered_out:
        sections.append("| Product | Source | Reason |")
        sections.append("|---------|--------|--------|")
        for p in filtered_out:
            name = p.get("name") or p.get("title") or "Unknown"
            src = p.get("_source", "?")
            reason = p.get("filter_reason", "N/A")
            sections.append(f"| {name} | {src} | {reason} |")
    else:
        sections.append("_No products were filtered out._")
    sections.append("")

    # --- Section 2: Quick Score Table ---
    sections += [
        "---", "",
        "## ⭐ Quick Score — All Suitable Products", "",
        "Scores are 1–5 per dimension. `total` = sum (max 20).", "",
        "| # | Product | Source | Tech Difficulty | User Acquisition | Revenue Potential | Indie Friendly | Total |",
        "|---|---------|--------|:-:|:-:|:-:|:-:|:-:|",
    ]
    for i, p in enumerate(suitable, 1):
        name = p.get("name") or p.get("title") or "Unknown"
        src = p.get("_source", "?")
        s = p["_scores"]
        sections.append(
            f"| {i} | {name} | {src} | {s['tech_difficulty']} | {s['user_acquisition']} | "
            f"{s['revenue_potential']} | {s['indie_friendly']} | **{s['total_score']}** |"
        )
    sections.append("")

    # --- Section 3: Top 5 Deep Dive ---
    sections += ["---", "", "## 🎯 Top 5 Deep Dive", ""]
    for rank, product in enumerate(top5, 1):
        sections.append(deep_analyze_product(product, rank))

    return "\n".join(sections)
