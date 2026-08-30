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
    """
    Convert RSS publication date into a Python datetime.
    """
    try:
        if hasattr(article, "published_parsed") and article.published_parsed:
            return datetime(
                *article.published_parsed[:6],
                tzinfo=timezone.utc
            )

        if hasattr(article, "updated_parsed") and article.updated_parsed:
            return datetime(
                *article.updated_parsed[:6],
                tzinfo=timezone.utc
            )

    except Exception:
        pass

    return None


def freshness_score(article):
    """
    Newer articles receive much higher scores.
    Articles older than 7 days receive zero freshness points.
    """
    published_date = article.get("date")

    if not published_date:
        return 0

    now = datetime.now(timezone.utc)
    age = now - published_date

    hours_old = age.total_seconds() / 3600

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
    else:
        return 0


def calculate_score(article):
    title = article["title"].lower()
    score = 0

    # Source reliability
    source_scores = {
        "OpenAI": 20,
        "Google AI": 20,
        "TechCrunch AI": 16,
        "The Verge AI": 15,
        "PC Gamer": 14,
    }

    score += source_scores.get(article["source"], 10)

    # Important AI terms
    ai_keywords = [
        "openai",
        "anthropic",
        "google ai",
        "gemini",
        "chatgpt",
        "artificial intelligence",
        "nvidia",
        "claude",
        "ai model",
        "language model",
        "generative ai",
        "machine learning",
    ]

    for keyword in ai_keywords:
        if keyword in title:
            score += 5

    # Important news terms
    news_keywords = [
        "launch",
        "launches",
        "announces",
        "announced",
        "introduces",
        "introduced",
        "releases",
        "released",
        "acquires",
        "acquisition",
        "lawsuit",
        "partnership",
        "new model",
    ]

    for keyword in news_keywords:
        if keyword in title:
            score += 3

    # Gaming terms
    gaming_keywords = [
        "elden ring",
        "playstation",
        "xbox",
        "nintendo",
        "steam",
        "game",
        "gaming",
        "fps",
        "rpg",
    ]

    for keyword in gaming_keywords:
        if keyword in title:
            score += 3

    # Freshness is very important
    score += freshness_score(article)

    return score


def fetch_news():
    print("=" * 70)
    print("AI NEWS ENGINE - SMART NEWS FILTER v2")
    print("=" * 70)

    all_articles = []

    # ---------------------------------------------------------
    # 1. Fetch RSS feeds
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

                all_articles.append({
                    "source": source,
                    "title": title,
                    "link": link,
                    "published": published,
                    "date": date,
                })

        except Exception as error:
            print(f"ERROR: {error}")

    print("\n" + "=" * 70)
    print(f"RAW ARTICLES FOUND: {len(all_articles)}")
    print("=" * 70)

    # ---------------------------------------------------------
    # 2. Remove duplicates
    # ---------------------------------------------------------

    unique_articles = []

    for article in all_articles:

        duplicate = False

        for existing in unique_articles:

            similarity = similarity_score(
                article["title"],
                existing["title"]
            )

            if similarity >= 0.60:
                duplicate = True
                break

        if not duplicate:
            unique_articles.append(article)

    print(f"AFTER DUPLICATE FILTER: {len(unique_articles)}")

    # ---------------------------------------------------------
    # 3. Remove very old news
    # ---------------------------------------------------------

    recent_articles = []

    now = datetime.now(timezone.utc)

    for article in unique_articles:

        if not article["date"]:
            continue

        age = now - article["date"]

        if age <= timedelta(days=7):
            recent_articles.append(article)

    print(f"AFTER 7-DAY FILTER: {len(recent_articles)}")

    # ---------------------------------------------------------
    # 4. Score articles
    # ---------------------------------------------------------

    for article in recent_articles:
        article["score"] = calculate_score(article)

    # ---------------------------------------------------------
    # 5. Sort by score
    # ---------------------------------------------------------

    recent_articles.sort(
        key=lambda article: article["score"],
        reverse=True
    )

    # ---------------------------------------------------------
    # 6. Select top 4
    # ---------------------------------------------------------

    top_articles = recent_articles[:4]

    print("\n" + "=" * 70)
    print("TOP STORIES")
    print("=" * 70)

    for index, article in enumerate(top_articles, start=1):

        print(f"\n#{index}")
        print(f"SCORE: {article['score']}")
        print(f"SOURCE: {article['source']}")
        print(f"TITLE: {article['title']}")
        print(f"DATE: {article['published']}")
        print(f"LINK: {article['link']}")

    print("\n" + "=" * 70)
    print("NEWS SELECTION COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    fetch_news()
