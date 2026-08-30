import feedparser
import re
from datetime import datetime, timezone, timedelta

RSS_FEEDS = {
    "OpenAI": "https://openai.com/news/rss.xml",
    "Google AI": "https://blog.google/technology/ai/rss/",
    "TechCrunch AI": "https://techcrunch.com/category/artificial-intelligence/feed/",
    "The Verge AI": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
    "PC Gamer": "https://www.pcgamer.com/rss/",
}


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

    if source in ["OpenAI", "Google AI", "TechCrunch AI", "The Verge AI"]:
        return "AI"

    if source == "PC Gamer":
        return "Gaming"

    return "Technology"


def freshness_score(article):
    date = article.get("date")

    if not date:
        return 0

    now = datetime.now(timezone.utc)
    hours_old = (now - date).total_seconds() / 3600

    if hours_old < 6:
        return 40
    elif hours_old < 12:
        return 35
    elif hours_old < 24:
        return 30
    elif hours_old < 48:
        return 20
    elif hours_old < 72:
        return 12
    elif hours_old < 168:
        return 5

    return 0


def calculate_score(article):
    title = article["title"].lower()
    score = 0

    source_scores = {
        "OpenAI": 20,
        "Google AI": 20,
        "TechCrunch AI": 16,
        "The Verge AI": 15,
        "PC Gamer": 14,
    }

    score += source_scores.get(article["source"], 10)

    important_ai = [
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

    for word in important_ai:
        if word in title:
            score += 5

    important_news = [
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

    for word in important_news:
        if word in title:
            score += 4

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

    score += freshness_score(article)

    return score


def fetch_news():

    print("=" * 70)
    print("AI NEWS ENGINE - SMART SELECTION v3")
    print("=" * 70)

    all_articles = []

    # ---------------------------------------------------------
    # FETCH RSS
    # ---------------------------------------------------------

    for source, url in RSS_FEEDS.items():

        print(f"\nFetching: {source}")

        try:
            feed = feedparser.parse(url)

            for article in feed.entries[:10]:

                title = article.get("title", "").strip()
                link = article.get("link", "").strip()

                if not title or not link:
                    continue

                published = article.get(
                    "published",
                    article.get("updated", "Unknown date")
                )

                date = parse_date(article)

                if not date:
                    continue

                all_articles.append({
                    "source": source,
                    "title": title,
                    "link": link,
                    "published": published,
                    "date": date,
                    "category": get_category(title, source)
                })

        except Exception as error:
            print(f"ERROR: {error}")

    print("\n" + "=" * 70)
    print(f"RAW ARTICLES FOUND: {len(all_articles)}")
    print("=" * 70)

    # ---------------------------------------------------------
    # REMOVE DUPLICATES
    # ---------------------------------------------------------

    unique_articles = []

    for article in all_articles:

        duplicate = False

        for existing in unique_articles:

            if similarity_score(
                article["title"],
                existing["title"]
            ) >= 0.60:

                duplicate = True
                break

        if not duplicate:
            unique_articles.append(article)

    print(f"AFTER DUPLICATE FILTER: {len(unique_articles)}")

    # ---------------------------------------------------------
    # LAST 7 DAYS ONLY
    # ---------------------------------------------------------

    now = datetime.now(timezone.utc)

    recent_articles = []

    for article in unique_articles:

        age = now - article["date"]

        if age <= timedelta(days=7):
            recent_articles.append(article)

    print(f"AFTER 7-DAY FILTER: {len(recent_articles)}")

    # ---------------------------------------------------------
    # SCORE
    # ---------------------------------------------------------

    for article in recent_articles:
        article["score"] = calculate_score(article)

    recent_articles.sort(
        key=lambda article: article["score"],
        reverse=True
    )

    # ---------------------------------------------------------
    # SELECT NEWS
    #
    # Maximum 2 articles from each source.
    # Try to include both AI and Gaming.
    # ---------------------------------------------------------

    selected = []

    source_count = {}
    category_count = {}

    # First: try to get at least one article from each category
    for preferred_category in ["AI", "Gaming"]:

        for article in recent_articles:

            if article in selected:
                continue

            source = article["source"]

            if article["category"] != preferred_category:
                continue

            if source_count.get(source, 0) >= 2:
                continue

            selected.append(article)

            source_count[source] = source_count.get(source, 0) + 1
            category_count[preferred_category] = (
                category_count.get(preferred_category, 0) + 1
            )

            break

    # Second: fill remaining positions with highest scoring stories
    for article in recent_articles:

        if article in selected:
            continue

        source = article["source"]

        if source_count.get(source, 0) >= 2:
            continue

        selected.append(article)

        source_count[source] = source_count.get(source, 0) + 1

        if len(selected) >= 4:
            break

    # ---------------------------------------------------------
    # FINAL OUTPUT
    # ---------------------------------------------------------

    print("\n" + "=" * 70)
    print("TOP STORIES")
    print("=" * 70)

    for index, article in enumerate(selected, start=1):

        print(f"\n#{index}")
        print(f"SCORE: {article['score']}")
        print(f"CATEGORY: {article['category']}")
        print(f"SOURCE: {article['source']}")
        print(f"TITLE: {article['title']}")
        print(f"DATE: {article['published']}")
        print(f"LINK: {article['link']}")

    print("\n" + "=" * 70)
    print("NEWS SELECTION COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    fetch_news()
