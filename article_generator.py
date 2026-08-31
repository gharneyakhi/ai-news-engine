import os
import re
import time
import feedparser
import requests

from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta
from google import genai


RSS_FEEDS = {
    "OpenAI": "https://openai.com/news/rss.xml",
    "Google AI": "https://blog.google/technology/ai/rss/",
    "TechCrunch AI": "https://techcrunch.com/category/artificial-intelligence/feed/",
    "The Verge AI": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
    "PC Gamer": "https://www.pcgamer.com/rss/",
    "IGN": "https://feeds.feedburner.com/ign/all",
    "GameSpot": "https://www.gamespot.com/feeds/news/",
    "Eurogamer": "https://www.eurogamer.net/feed",
}


GEMINI_MODEL = "gemini-3.6-flash"

OUTPUT_DIR = "articles"

ARTICLES_PER_RUN = 3

MAX_ARTICLE_AGE_DAYS = 7

MAX_SOURCE_CHARS = 12000

MAX_RETRIES = 3

RETRY_DELAY = 8

REQUEST_TIMEOUT = 20


def create_client():
    api_key = os.environ.get("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError("Missing GEMINI_API_KEY")

    return genai.Client(api_key=api_key)


def clean_text(text):
    text = text.lower()

    text = re.sub(
        r"[^a-z0-9\s]",
        " ",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


def get_category(title, source):
    text = title.lower()

    gaming_words = [
        "game",
        "gaming",
        "playstation",
        "xbox",
        "nintendo",
        "steam",
        "elden ring",
        "gta",
        "grand theft auto",
        "gta 6",
        "gta vi",
        "grand theft auto vi",
        "grand theft auto 6",
        "fps",
        "rpg",
        "rockstar",
        "rockstar games",
        "ps5",
        "xbox series",
        "switch",
        "switch 2",
        "esports"
    ]

    ai_words = [
        "ai",
        "artificial intelligence",
        "openai",
        "chatgpt",
        "gemini",
        "claude",
        "nvidia",
        "machine learning",
        "generative ai",
        "llm",
        "language model"
    ]

    if any(word in text for word in gaming_words):
        return "Gaming"

    if any(word in text for word in ai_words):
        return "AI"

    if source in [
        "PC Gamer",
        "IGN",
        "GameSpot",
        "Eurogamer"
    ]:
        return "Gaming"

    if source in [
        "OpenAI",
        "Google AI",
        "TechCrunch AI",
        "The Verge AI"
    ]:
        return "AI"

    return "Technology"


def parse_date(item):
    try:
        if item.get("published_parsed"):
            return datetime(
                *item.published_parsed[:6],
                tzinfo=timezone.utc
            )

        if item.get("updated_parsed"):
            return datetime(
                *item.updated_parsed[:6],
                tzinfo=timezone.utc
            )
    except Exception:
        pass

    return datetime.now(timezone.utc)


def fetch_news():
    articles = []

    print("=" * 70)
    print("NEWS ENGINE - AI + GAMING MODE")
    print("=" * 70)

    for source, url in RSS_FEEDS.items():
        print(f"Fetching: {source}")

        try:
            feed = feedparser.parse(url)

            for item in feed.entries[:10]:
                title = item.get(
                    "title",
                    ""
                ).strip()

                link = item.get(
                    "link",
                    ""
                ).strip()

                if not title or not link:
                    continue

                date = parse_date(item)

                articles.append(
                    {
                        "source": source,
                        "title": title,
                        "link": link,
                        "date": date,
                        "category": get_category(
                            title,
                            source
                        )
                    }
                )

        except Exception as error:
            print(
                f"ERROR {source}: {error}"
            )

    print(
        f"RAW ARTICLES: {len(articles)}"
    )

    return articles


def filter_recent(articles):
    now = datetime.now(timezone.utc)

    result = []

    for article in articles:
        age = now - article["date"]

        if age <= timedelta(
            days=MAX_ARTICLE_AGE_DAYS
        ):
            result.append(article)

    print(
        f"AFTER 7-DAY FILTER: {len(result)}"
    )

    return result


def remove_duplicates(articles):
    unique = []

    titles = set()

    for article in articles:
        key = clean_text(
            article["title"]
        )

        if key in titles:
            continue

        titles.add(key)

        unique.append(article)

    print(
        f"AFTER DUPLICATE FILTER: {len(unique)}"
    )

    return unique


def score_article(article):
    title = article["title"].lower()

    score = 0

    source_scores = {
        "OpenAI": 20,
        "Google AI": 20,
        "TechCrunch AI": 16,
        "The Verge AI": 15,
        "PC Gamer": 18,
        "IGN": 17,
        "GameSpot": 17,
        "Eurogamer": 17
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
        "update",
        "revealed",
        "reveals",
        "trailer",
        "official"
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
        "machine learning"
    ]

    for word in ai_words:
        if word in title:
            score += 5

    gaming_words = [
        "gta",
        "grand theft auto",
        "rockstar",
        "elden ring",
        "playstation",
        "xbox",
        "nintendo",
        "steam",
        "gaming",
        "game",
        "fps",
        "rpg",
        "trailer",
        "ps5"
    ]

    for word in gaming_words:
        if word in title:
            score += 5

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


def select_articles(articles):
    for article in articles:
        article["score"] = score_article(article)

    articles.sort(
        key=lambda item: item["score"],
        reverse=True
    )

    selected = []

    source_count = {}

    category_limits = {
        "AI": 1,
        "Gaming": 2,
        "Technology": 1
    }

    for category in [
        "AI",
        "Gaming",
        "Technology"
    ]:
        for article in articles:
            if len(selected) >= ARTICLES_PER_RUN:
                break

            if article in selected:
                continue

            if article["category"] != category:
                continue

            source = article["source"]

            if source_count.get(source, 0) >= 2:
                continue

            selected.append(article)

            source_count[source] = (
                source_count.get(source, 0) + 1
            )

            if len(
                [
                    item for item in selected
                    if item["category"] == category
                ]
            ) >= category_limits.get(category, 1):
                break

    if len(selected) < ARTICLES_PER_RUN:
        for article in articles:
            if len(selected) >= ARTICLES_PER_RUN:
                break

            if article in selected:
                continue

            source = article["source"]

            if source_count.get(source, 0) >= 2:
                continue

            selected.append(article)

            source_count[source] = (
                source_count.get(source, 0) + 1
            )

    return selected[:ARTICLES_PER_RUN]


def read_source_page(url):
    print(
        f"Reading source: {url}"
    )

    headers = {
        "User-Agent": (
            "Mozilla/5.0 "
            "(Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/120 Safari/537.36"
        )
    }

    try:
        response = requests.get(
            url,
            headers=headers,
            timeout=REQUEST_TIMEOUT
        )

        response.raise_for_status()

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        for tag in soup(
            [
                "script",
                "style",
                "nav",
                "footer",
                "header",
                "aside",
                "form",
                "noscript"
            ]
        ):
            tag.decompose()

        paragraphs = []

        for paragraph in soup.find_all("p"):
            text = paragraph.get_text(
                " ",
                strip=True
            )

            if len(text) >= 40:
                paragraphs.append(text)

        content = "\n\n".join(
            paragraphs
        )

        content = re.sub(
            r"\n{3,}",
            "\n\n",
            content
        ).strip()

        if len(content) > MAX_SOURCE_CHARS:
            content = content[:MAX_SOURCE_CHARS]

        print(
            f"Source text extracted: "
            f"{len(content)} characters"
        )

        return content

    except Exception as error:
        print(
            f"Source error: {error}"
        )

        return ""


def build_prompt(article, source_text):
    return f"""
You are a professional Persian technology and gaming editor.

Write an original Persian news article based ONLY on the source text.

Rules:
- Write fluent, natural and modern Persian.
- Do not translate word by word.
- Do not invent facts.
- Do not add unsupported claims.
- Do not fabricate quotes.
- Do not copy sentences from the source.
- Clearly distinguish facts from opinions.
- Keep important game, company, product and technology names in English when useful.
- Do not mention AI or these instructions.
- Do not use clickbait.
- The article must read like professional Persian journalism.

Category:
{article["category"]}

Source:
{article["source"]}

Original title:
{article["title"]}

Original URL:
{article["link"]}

Source text:
{source_text}

Return ONLY this structure:

TITLE:
A strong natural Persian headline.

SUMMARY:
A concise 2-3 sentence Persian summary.

ARTICLE:
Write a complete Persian news article of approximately 500-800 words.

SEO_TITLE:
A Persian SEO title under 60 characters.

META_DESCRIPTION:
A Persian meta description between 120 and 160 characters.

TAGS:
5 to 8 relevant Persian or English tags separated by commas.
"""


def generate_article(
    client,
    article,
    source_text
):
    print("-" * 70)

    print(
        "Generating:",
        article["title"]
    )

    prompt = build_prompt(
        article,
        source_text
    )

    for attempt in range(
        1,
        MAX_RETRIES + 1
    ):
        try:
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt
            )

            if response and response.text:
                return response.text.strip()

            print(
                "Gemini returned empty response."
            )

        except Exception as error:
            print(
                f"Gemini ERROR "
                f"(attempt {attempt}/{MAX_RETRIES}): "
                f"{error}"
            )

            if attempt < MAX_RETRIES:
                print(
                    f"Retrying in "
                    f"{RETRY_DELAY} seconds..."
                )

                time.sleep(RETRY_DELAY)

    return None


def save_article(
    article,
    content
):
    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True
    )

    date = datetime.now().strftime(
        "%Y-%m-%d-%H-%M-%S"
    )

    safe_category = (
        article["category"].lower()
    )

    filename = (
        f"{date}-{safe_category}.md"
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
            "# "
            + article["title"]
            + "\n\n"
        )

        file.write(
            "Category: "
            + article["category"]
            + "\n\n"
        )

        file.write(
            "Source: "
            + article["source"]
            + "\n\n"
        )

        file.write(
            "URL: "
            + article["link"]
            + "\n\n"
        )

        file.write(
            "Score: "
            + str(article["score"])
            + "\n\n"
        )

        file.write(
            "---\n\n"
        )

        file.write(content)

        file.write(
            "\n\n---\n\n"
        )

        file.write(
            "Generated: "
            + datetime.now(
                timezone.utc
            ).isoformat()
            + "\n"
        )

    print(
        "Saved:",
        path
    )


def main():
    client = create_client()

    articles = fetch_news()

    articles = remove_duplicates(
        articles
    )

    articles = filter_recent(
        articles
    )

    selected = select_articles(
        articles
    )

    print("=" * 70)
    print("SELECTED STORIES")
    print("=" * 70)

    for index, article in enumerate(
        selected,
        start=1
    ):
        print(
            f"{index}. "
            f"[{article['category']}] "
            f"SCORE {article['score']} - "
            f"{article['title']}"
        )

    if not selected:
        print(
            "No suitable articles found."
        )
        return

    generated_count = 0

    for article in selected:
        source_text = read_source_page(
            article["link"]
        )

        if not source_text:
            print(
                "No source text, skip"
            )
            continue

        content = generate_article(
            client,
            article,
            source_text
        )

        if content:
            save_article(
                article,
                content
            )
            generated_count += 1
        else:
            print(
                "Article generation failed."
            )

        time.sleep(3)

    print("=" * 70)
    print(
        "ARTICLE GENERATION COMPLETE: "
        f"{generated_count}/{len(selected)}"
    )
    print("=" * 70)


if __name__ == "__main__":
    main()
