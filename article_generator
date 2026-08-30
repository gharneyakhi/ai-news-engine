import os
import re
import time
import feedparser

from datetime import datetime, timezone, timedelta
from google import genai


# ============================================================
# CONFIGURATION
# ============================================================

RSS_FEEDS = {
    "OpenAI": "https://openai.com/news/rss.xml",
    "Google AI": "https://blog.google/technology/ai/rss/",
    "TechCrunch AI": "https://techcrunch.com/category/artificial-intelligence/feed/",
    "The Verge AI": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
    "PC Gamer": "https://www.pcgamer.com/rss/",
}

ARTICLES_PER_RUN = 3
MAX_ARTICLE_AGE_DAYS = 7

OUTPUT_DIR = "articles"

GEMINI_MODEL = "gemini-3.6-flash"


# ============================================================
# GEMINI
# ============================================================

def create_gemini_client():

    api_key = os.environ.get("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is missing. "
            "Check GitHub Actions Secrets."
        )

    return genai.Client(api_key=api_key)


# ============================================================
# TEXT HELPERS
# ============================================================

def clean_text(text):

    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def similarity_score(title1, title2):

    words1 = set(clean_text(title1).split())
    words2 = set(clean_text(title2).split())

    if not words1 or not words2:
        return 0

    common = words1.intersection(words2)

    return len(common) / min(len(words1), len(words2))


# ============================================================
# DATE
# ============================================================

def parse_date(article):

    try:

        if article.get("published_parsed"):

            return datetime(
                *article.published_parsed[:6],
                tzinfo=timezone.utc
            )

        if article.get("updated_parsed"):

            return datetime(
                *article.updated_parsed[:6],
                tzinfo=timezone.utc
            )

    except Exception:
        pass

    return None


# ============================================================
# CATEGORY
# ============================================================

def get_category(title, source):

    text = f" {title.lower()} "

    gaming_words = [
        " game ",
        " gaming ",
        " playstation ",
        " xbox ",
        " nintendo ",
        " steam ",
        " elden ring ",
        " fps ",
        " rpg ",
        " dayz ",
        " ps3 ",
        " wii "
    ]

    ai_words = [
        " openai ",
        " anthropic ",
        " chatgpt ",
        " gemini ",
        " claude ",
        " nvidia ",
        " artificial intelligence ",
        " machine learning ",
        " ai model ",
        " generative ai ",
        " ai "
    ]

    if any(word in text for word in gaming_words):
        return "Gaming"

    if any(word in text for word in ai_words):
        return "AI"

    if source in [
        "OpenAI",
        "Google AI",
        "TechCrunch AI",
        "The Verge AI"
    ]:
        return "AI"

    if source == "PC Gamer":
        return "Gaming"

    return "Technology"


# ============================================================
# FETCH NEWS
# ============================================================

def fetch_news():

    print("=" * 70)
    print("ARTICLE GENERATOR")
    print("=" * 70)

    articles = []

    for source, url in RSS_FEEDS.items():

        print(f"Fetching: {source}")

        try:

            feed = feedparser.parse(url)

            for item in feed.entries[:10]:

                title = item.get("title", "").strip()
                link = item.get("link", "").strip()

                if not title or not link:
                    continue

                date = parse_date(item)

                if not date:
                    continue

                articles.append({
                    "source": source,
                    "title": title,
                    "link": link,
                    "date": date,
                    "published": item.get(
                        "published",
                        item.get("updated", "")
                    ),
                    "category": get_category(
                        title,
                        source
                    )
                })

        except Exception as error:

            print(
                f"ERROR fetching {source}: {error}"
            )

    print(f"\nRAW ARTICLES: {len(articles)}")

    return articles


# ============================================================
# REMOVE DUPLICATES
# ============================================================

def remove_duplicates(articles):

    unique = []

    for article in articles:

        duplicate = False

        for existing in unique:

            if similarity_score(
                article["title"],
                existing["title"]
            ) >= 0.60:

                duplicate = True
                break

        if not duplicate:
            unique.append(article)

    return unique


# ============================================================
# FILTER RECENT NEWS
# ============================================================

def filter_recent(articles):

    now = datetime.now(timezone.utc)

    result = []

    for article in articles:

        age = now - article["date"]

        if age <= timedelta(
            days=MAX_ARTICLE_AGE_DAYS
        ):
            result.append(article)

    return result


# ============================================================
# SIMPLE IMPORTANCE SCORE
# ============================================================

def score_article(article):

    title = article["title"].lower()

    score = 0

    source_scores = {
        "OpenAI": 20,
        "Google AI": 20,
        "TechCrunch AI": 16,
        "The Verge AI": 15,
        "PC Gamer": 14,
    }

    score += source_scores.get(
        article["source"],
        10
    )

    important_words = [
        "launch",
        "launches",
        "announces",
        "announced",
        "introduces",
        "introduced",
        "released",
        "release",
        "acquisition",
        "acquires",
        "lawsuit",
        "partnership",
        "new model",
    ]

    for word in important_words:

        if word in title:
            score += 4

    ai_words = [
        "openai",
        "anthropic",
        "chatgpt",
        "gemini",
        "claude",
        "nvidia",
        "artificial intelligence",
        "ai model",
        "generative ai",
    ]

    for word in ai_words:

        if word in title:
            score += 5

    gaming_words = [
        "elden ring",
        "playstation",
        "xbox",
        "nintendo",
        "steam",
        "gaming",
        "game",
        "fps",
        "rpg",
    ]

    for word in gaming_words:

        if word in title:
            score += 3

    age_hours = (
        datetime.now(timezone.utc)
        - article["date"]
    ).total_seconds() / 3600

    if age_hours < 6:
        score += 40

    elif age_hours < 12:
        score += 35

    elif age_hours < 24:
        score += 30

    elif age_hours < 48:
        score += 20

    elif age_hours < 72:
        score += 12

    else:
        score += 5

    return score


# ============================================================
# SELECT STORIES
# ============================================================

def select_articles(articles):

    for article in articles:

        article["score"] = score_article(
            article
        )

    articles.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    selected = []

    source_count = {}
    category_count = {}

    # --------------------------------------------------------
    # First pass:
    # force some category diversity
    # --------------------------------------------------------

    for category in ["AI", "Gaming"]:

        for article in articles:

            if article in selected:
                continue

            if article["category"] != category:
                continue

            source = article["source"]

            if source_count.get(
                source,
                0
            ) >= 2:
                continue

            selected.append(article)

            source_count[source] = (
                source_count.get(source, 0) + 1
            )

            category_count[category] = (
                category_count.get(category, 0) + 1
            )

            break

    # --------------------------------------------------------
    # Fill remaining slots
    # --------------------------------------------------------

    for article in articles:

        if article in selected:
            continue

        source = article["source"]

        if source_count.get(
            source,
            0
        ) >= 2:
            continue

        selected.append(article)

        source_count[source] = (
            source_count.get(source, 0) + 1
        )

        if len(selected) >= ARTICLES_PER_RUN:
            break

    return selected


# ============================================================
# GEMINI PROMPT
# ============================================================

def build_prompt(article):

    return f"""
You are the senior Persian editor of a technology news website.

Rewrite the following English news item into an original,
natural Persian news article.

IMPORTANT RULES:

1. Write fluent, modern Persian.
2. Do NOT translate word-for-word.
3. Do NOT invent facts.
4. Do NOT add information that is not supported by the source.
5. Clearly distinguish facts from opinions.
6. Do not copy the source article.
7. The result must feel like an original Persian technology news report.
8. Avoid clickbait.
9. Keep technical product names in their original English form
   when that improves clarity.
10. Write for Persian-speaking readers.

SOURCE:
{article["source"]}

ORIGINAL TITLE:
{article["title"]}

SOURCE URL:
{article["link"]}

CATEGORY:
{article["category"]}

Return ONLY the following structure:

TITLE:
A strong Persian headline.

SUMMARY:
A 2-3 sentence summary.

ARTICLE:
A complete Persian news article of approximately 500-800 words.

SEO_TITLE:
A Persian SEO title under 60 characters.

META_DESCRIPTION:
A Persian meta description between 120 and 160 characters.

TAGS:
5 to 8 relevant Persian or English tags separated by commas.
"""


# ============================================================
# GENERATE ARTICLE
# ============================================================

def generate_article(client, article):

    print("\n" + "-" * 70)

    print(
        f"Generating article: "
        f"{article['title']}"
    )

    prompt = build_prompt(article)

    try:

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt
        )

        return response.text

    except Exception as error:

        print(
            f"Gemini ERROR: {error}"
        )

        return None


# ============================================================
# SAFE FILENAME
# ============================================================

def make_filename(article):

    title = clean_text(
        article["title"]
    )

    words = title.split()[:8]

    slug = "-".join(words)

    date = article["date"].strftime(
        "%Y-%m-%d"
    )

    return f"{date}-{slug}.md"


# ============================================================
# SAVE ARTICLE
# ============================================================

def save_article(article, content):

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True
    )

    filename = make_filename(
        article
    )

    path = os.path.join(
        OUTPUT_DIR,
        filename
    )

    with open(
        path,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(
            f"# {article['title']}\n\n"
        )

        file.write(
            f"**Source:** {article['source']}\n\n"
        )

        file.write(
            f"**Original URL:** "
            f"{article['link']}\n\n"
        )

        file.write(
            "---\n\n"
        )

        file.write(content)

        file.write(
            "\n\n---\n\n"
        )

        file.write(
            f"Generated: "
            f"{datetime.now(timezone.utc).isoformat()}\n"
        )

    print(
        f"Saved: {path}"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    client = create_gemini_client()

    articles = fetch_news()

    articles = remove_duplicates(
        articles
    )

    articles = filter_recent(
        articles
    )

    print(
        f"After filtering: "
        f"{len(articles)} articles"
    )

    selected = select_articles(
        articles
    )

    print("\nSELECTED STORIES:")

    for index, article in enumerate(
        selected,
        start=1
    ):

        print(
            f"{index}. "
            f"[{article['category']}] "
            f"{article['title']}"
        )

    if not selected:

        print(
            "No suitable articles found."
        )

        return

    print("\nGENERATING ARTICLES...")

    for article in selected:

        content = generate_article(
            client,
            article
        )

        if content:

            save_article(
                article,
                content
            )

        # Small delay between requests
        time.sleep(2)

    print("\n" + "=" * 70)
    print("ARTICLE GENERATION COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
