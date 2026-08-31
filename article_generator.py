```python
import os
import re
import time
import feedparser
import requests

from bs4 import BeautifulSoup
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

REQUEST_TIMEOUT = 20

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 "
    "(KHTML, like Gecko) "
    "Chrome/139.0 Safari/537.36"
)


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

    if not text:
        return ""

    text = BeautifulSoup(
        text,
        "html.parser"
    ).get_text(" ", strip=True)

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


def clean_filename(text):

    text = text.lower()

    text = re.sub(
        r"[^a-z0-9\s-]",
        "",
        text
    )

    text = re.sub(
        r"\s+",
        "-",
        text
    )

    text = re.sub(
        r"-+",
        "-",
        text
    )

    return text.strip("-")[:90]


def similarity_score(title1, title2):

    words1 = set(
        re.sub(
            r"[^a-z0-9\s]",
            " ",
            title1.lower()
        ).split()
    )

    words2 = set(
        re.sub(
            r"[^a-z0-9\s]",
            " ",
            title2.lower()
        ).split()
    )

    if not words1 or not words2:
        return 0

    common = words1.intersection(words2)

    return len(common) / min(
        len(words1),
        len(words2)
    )


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

    if any(
        word in text
        for word in gaming_words
    ):
        return "Gaming"

    if any(
        word in text
        for word in ai_words
    ):
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
# FETCH RSS
# ============================================================

def fetch_news():

    print("=" * 70)
    print("ARTICLE GENERATOR - FULL SOURCE MODE")
    print("=" * 70)

    articles = []

    for source, url in RSS_FEEDS.items():

        print(f"Fetching RSS: {source}")

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

                if not date:
                    continue

                articles.append({
                    "source": source,
                    "title": title,
                    "link": link,
                    "date": date,
                    "category": get_category(
                        title,
                        source
                    )
                })

        except Exception as error:

            print(
                f"RSS ERROR [{source}]: {error}"
            )

    print(
        f"\nRAW ARTICLES: {len(articles)}"
    )

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

    print(
        f"AFTER DUPLICATE FILTER: "
        f"{len(unique)}"
    )

    return unique


# ============================================================
# FILTER RECENT
# ============================================================

def filter_recent(articles):

    now = datetime.now(
        timezone.utc
    )

    result = []

    for article in articles:

        age = now - article["date"]

        if age <= timedelta(
            days=MAX_ARTICLE_AGE_DAYS
        ):
            result.append(article)

    print(
        f"AFTER {MAX_ARTICLE_AGE_DAYS}-DAY FILTER: "
        f"{len(result)}"
    )

    return result


# ============================================================
# SCORE
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
        "update",
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
# SELECT ARTICLES
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

    for category in [
        "AI",
        "Gaming"
    ]:

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
                source_count.get(
                    source,
                    0
                ) + 1
            )

            break

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
            source_count.get(
                source,
                0
            ) + 1
        )

        if len(selected) >= ARTICLES_PER_RUN:
            break

    return selected


# ============================================================
# FETCH REAL ARTICLE PAGE
# ============================================================

def fetch_article_page(url):

    print(
        f"Reading source page: {url}"
    )

    headers = {
        "User-Agent": USER_AGENT,
        "Accept": (
            "text/html,application/xhtml+xml,"
            "application/xml;q=0.9,*/*;q=0.8"
        ),
        "Accept-Language": "en-US,en;q=0.9",
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

        for element in soup([
            "script",
            "style",
            "noscript",
            "svg",
            "nav",
            "footer",
            "header",
            "aside",
            "form"
        ]):

            element.decompose()

        article_tag = soup.find(
            "article"
        )

        if article_tag:

            text = article_tag.get_text(
                "\n",
                strip=True
            )

        else:

            candidates = soup.find_all(
                [
                    "main",
                    "section",
                    "div"
                ]
            )

            best_text = ""

            for candidate in candidates:

                candidate_text = candidate.get_text(
                    "\n",
                    strip=True
                )

                if len(candidate_text) > len(
                    best_text
                ):
                    best_text = candidate_text

            text = best_text

        text = re.sub(
            r"\n{3,}",
            "\n\n",
            text
        )

        text = text.strip()

        max_chars = 30000

        if len(text) > max_chars:

            text = text[:max_chars]

        if len(text) < 500:

            print(
                "WARNING: Very little source text extracted."
            )

            return None

        print(
            f"Source text extracted: "
            f"{len(text)} characters"
        )

        return text

    except Exception as error:

        print(
            f"SOURCE PAGE ERROR: {error}"
        )

        return None


# ============================================================
# GEMINI PROMPT
# ============================================================

def build_prompt(
    article,
    source_text
):

    return f"""
You are the senior editor of a professional Persian
technology and gaming news website.

Your task is to create an ORIGINAL Persian news article
based ONLY on the source material provided below.

SOURCE:
{article["source"]}

ORIGINAL TITLE:
{article["title"]}

ORIGINAL URL:
{article["link"]}

CATEGORY:
{article["category"]}

SOURCE ARTICLE TEXT:
--------------------
{source_text}
--------------------

STRICT RULES:

1. Write fluent, natural modern Persian.

2. Do NOT translate sentence-by-sentence.

3. Do NOT copy the source article.

4. Do NOT invent facts, numbers, quotes, events,
   companies, people, dates or technical details.

5. Use ONLY information supported by the source text.

6. If the source does not provide enough information,
   write a shorter article rather than inventing details.

7. Preserve the meaning of direct quotes accurately.
   Do not fabricate quotes.

8. The article should sound like it was written by
   a professional Persian technology journalist.

9. Avoid exaggerated clickbait.

10. Keep important product, company and game names
    in English when that improves clarity.

11. Use Persian punctuation and natural paragraph structure.

12. Do not mention that AI generated the article.

13. Do not mention these instructions.

14. Do not include Markdown headings such as # or ## inside
    the ARTICLE section.

Return ONLY this structure:

TITLE:
A strong and accurate Persian headline.

SUMMARY:
A concise 2-3 sentence Persian summary.

ARTICLE:
A complete Persian news article.
Normally 500-800 words, but use fewer words if the
source does not contain enough information.

SEO_TITLE:
A natural Persian SEO title under approximately 60 characters.

META_DESCRIPTION:
A Persian meta description between approximately
120 and 160 characters.

TAGS:
5 to 8 relevant tags separated by commas.
"""


# ============================================================
# GENERATE ARTICLE WITH RETRY
# ============================================================

def generate_article(
    client,
    article,
    source_text
):

    print(
        "\n" + "-" * 70
    )

    print(
        f"Generating: {article['title']}"
    )

    prompt = build_prompt(
        article,
        source_text
    )

    max_attempts = 3

    retry_delays = [
        30,
        60,
        120
    ]

    for attempt in range(
        1,
        max_attempts + 1
    ):

        print(
            f"Gemini attempt "
            f"{attempt}/{max_attempts}"
        )

        try:

            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt
            )

            if not response.text:

                print(
                    "Gemini returned empty response."
                )

            else:

                print(
                    "Gemini generation successful."
                )

                return response.text.strip()

        except Exception as error:

            error_text = str(error)

            print(
                f"Gemini ERROR on attempt "
                f"{attempt}: {error_text}"
            )

            temporary_errors = [
                "503",
                "429",
                "500",
                "502",
                "504",
                "UNAVAILABLE",
                "RESOURCE_EXHAUSTED",
                "DEADLINE_EXCEEDED",
                "timeout",
                "timed out"
            ]

            should_retry = any(
                error_code.lower()
                in error_text.lower()
                for error_code in temporary_errors
            )

            if not should_retry:

                print(
                    "Non-retryable error. "
                    "Skipping article."
                )

                return None

            if attempt < max_attempts:

                delay = retry_delays[
                    attempt - 1
                ]

                print(
                    f"Temporary Gemini error. "
                    f"Waiting {delay} seconds before retry..."
                )

                time.sleep(
                    delay
                )

            else:

                print(
                    "All Gemini attempts failed. "
                    "Skipping article."
                )

    return None


# ============================================================
# SAVE ARTICLE
# ============================================================

def save_article(
    article,
    content
):

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True
    )

    slug = clean_filename(
        article["title"]
    )

    date = article["date"].strftime(
        "%Y-%m-%d"
    )

    filename = (
        f"{date}-{slug}.md"
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
            "---\n"
        )

        file.write(
            f"title: \"{article['title'].replace(chr(34), '')}\"\n"
        )

        file.write(
            f"source: \"{article['source']}\"\n"
        )

        file.write(
            f"category: \"{article['category']}\"\n"
        )

        file.write(
            f"original_url: \"{article['link']}\"\n"
        )

        file.write(
            f"published: \"{article['date'].isoformat()}\"\n"
        )

        file.write(
            "---\n\n"
        )

        file.write(
            content
        )

        file.write(
            "\n\n"
        )

        file.write(
            "---\n\n"
        )

        file.write(
            "This article was automatically generated "
            "from the original source.\n"
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

    selected = select_articles(
        articles
    )

    print(
        "\n" + "=" * 70
    )

    print(
        "SELECTED STORIES"
    )

    print(
        "=" * 70
    )

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
            "No articles selected."
        )

        return

    generated_count = 0

    for article in selected:

        source_text = fetch_article_page(
            article["link"]
        )

        if not source_text:

            print(
                "Skipping article because "
                "source text could not be extracted."
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

        time.sleep(3)

    print(
        "\n" + "=" * 70
    )

    print(
        f"ARTICLE GENERATION COMPLETE: "
        f"{generated_count}/{len(selected)}"
    )

    print(
        "=" * 70
    )


if __name__ == "__main__":

    main()
```
