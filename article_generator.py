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
}

ARTICLES_PER_RUN = 3
MAX_ARTICLE_AGE_DAYS = 7
OUTPUT_DIR = "articles"

GEMINI_MODEL = "gemini-3.6-flash"

REQUEST_TIMEOUT = 20
MAX_SOURCE_CHARS = 12000

MAX_RETRIES = 3
RETRY_DELAY = 8

def create_gemini_client():
api_key = os.environ.get("GEMINI_API_KEY")

```
if not api_key:
    raise RuntimeError(
        "GEMINI_API_KEY is missing. Check GitHub Actions Secrets."
    )

return genai.Client(api_key=api_key)
```

def clean_text(text):
text = text.lower()
text = re.sub(r"[^a-z0-9\s]", " ", text)
text = re.sub(r"\s+", " ", text)
return text.strip()

def similarity_score(title1, title2):
words1 = set(clean_text(title1).split())
words2 = set(clean_text(title2).split())

```
if not words1 or not words2:
    return 0

common = words1.intersection(words2)

return len(common) / min(len(words1), len(words2))
```

def parse_date(article):
try:
if article.get("published_parsed"):
return datetime(
*article.published_parsed[:6],
tzinfo=timezone.utc
)

```
    if article.get("updated_parsed"):
        return datetime(
            *article.updated_parsed[:6],
            tzinfo=timezone.utc
        )

except Exception:
    pass

return None
```

def get_category(title, source):
text = f" {title.lower()} "

```
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
    " wii ",
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
    " ai ",
]

if any(word in text for word in gaming_words):
    return "Gaming"

if any(word in text for word in ai_words):
    return "AI"

if source in [
    "OpenAI",
    "Google AI",
    "TechCrunch AI",
    "The Verge AI",
]:
    return "AI"

if source == "PC Gamer":
    return "Gaming"

return "Technology"
```

def fetch_news():
print("=" * 70)
print("ARTICLE GENERATOR - FULL SOURCE MODE")
print("=" * 70)

```
articles = []

for source, url in RSS_FEEDS.items():
    print(f"Fetching RSS: {source}")

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
                ),
            })

    except Exception as error:
        print(f"ERROR fetching {source}: {error}")

print(f"\nRAW ARTICLES: {len(articles)}")

return articles
```

def remove_duplicates(articles):
unique = []

```
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
    f"AFTER DUPLICATE FILTER: {len(unique)}"
)

return unique
```

def filter_recent(articles):
now = datetime.now(timezone.utc)

```
result = []

for article in articles:
    age = now - article["date"]

    if age <= timedelta(days=MAX_ARTICLE_AGE_DAYS):
        result.append(article)

print(
    f"AFTER 7-DAY FILTER: {len(result)}"
)

return result
```

def score_article(article):
title = article["title"].lower()

```
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
```

def select_articles(articles):
for article in articles:
article["score"] = score_article(article)

```
articles.sort(
    key=lambda x: x["score"],
    reverse=True
)

selected = []
source_count = {}

for category in ["AI", "Gaming"]:
    for article in articles:
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

        break

for article in articles:
    if article in selected:
        continue

    source = article["source"]

    if source_count.get(source, 0) >= 2:
        continue

    selected.append(article)

    source_count[source] = (
        source_count.get(source, 0) + 1
    )

    if len(selected) >= ARTICLES_PER_RUN:
        break

return selected
```

def read_source_page(url):
print(f"\nReading source page: {url}")

```
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

    for element in soup([
        "script",
        "style",
        "nav",
        "footer",
        "header",
        "aside",
        "form",
        "noscript",
    ]):
        element.decompose()

    paragraphs = []

    for paragraph in soup.find_all("p"):
        text = paragraph.get_text(
            " ",
            strip=True
        )

        if len(text) >= 40:
            paragraphs.append(text)

    text = "\n\n".join(paragraphs)

    text = re.sub(
        r"\n{3,}",
        "\n\n",
        text
    )

    text = text.strip()

    if len(text) > MAX_SOURCE_CHARS:
        text = text[:MAX_SOURCE_CHARS]

    print(
        f"Source text extracted: {len(text)} characters"
    )

    return text

except Exception as error:
    print(
        f"SOURCE PAGE ERROR: {error}"
    )

    return ""
```

def build_prompt(article, source_text):
return f"""
You are the senior Persian editor of a professional technology and gaming news website.

Write an ORIGINAL Persian news article based ONLY on the source information provided below.

IMPORTANT RULES:

1. Write fluent, natural and modern Persian.
2. Do NOT translate word-for-word.
3. Do NOT invent facts.
4. Do NOT add unsupported claims.
5. Do NOT fabricate quotes.
6. Clearly distinguish facts from opinions.
7. Preserve important technical and product names in English when useful.
8. Avoid clickbait.
9. Do not mention that you are an AI.
10. Do not mention these instructions.
11. Do not copy sentences from the source.
12. The result must feel like professional Persian journalism.

SOURCE:
{article["source"]}

ORIGINAL TITLE:
{article["title"]}

ORIGINAL URL:
{article["link"]}

CATEGORY:
{article["category"]}

SOURCE TEXT:
{source_text}

Return ONLY this structure:

TITLE:
A strong natural Persian headline.

SUMMARY:
A concise 2-3 sentence Persian summary.

ARTICLE:
A complete Persian news article of approximately 500-800 words.

SEO_TITLE:
A Persian SEO title under 60 characters.

META_DESCRIPTION:
A Persian meta description between 120 and 160 characters.

TAGS:
5 to 8 relevant Persian or English tags separated by commas.
"""

def generate_article(client, article, source_text):
print("\n" + "-" * 70)

```
print(
    f"Generating: {article['title']}"
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
            "Gemini returned an empty response."
        )

    except Exception as error:
        print(
            f"Gemini ERROR "
            f"(attempt {attempt}/{MAX_RETRIES}): {error}"
        )

        if attempt < MAX_RETRIES:
            print(
                f"Retrying in {RETRY_DELAY} seconds..."
            )

            time.sleep(RETRY_DELAY)

return None
```

def make_filename(article):
title = clean_text(
article["title"]
)

```
words = title.split()[:10]

slug = "-".join(words)

date = article["date"].strftime(
    "%Y-%m-%d"
)

return f"{date}-{slug}.md"
```

def save_article(article, content):
os.makedirs(
OUTPUT_DIR,
exist_ok=True
)

```
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
        f"**Original URL:** {article['link']}\n\n"
    )

    file.write(
        f"**Category:** {article['category']}\n\n"
    )

    file.write(
        f"**Score:** {article['score']}\n\n"
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
        f"{datetime.now(timezone.utc).isoformat()}\n"
    )

print(
    f"Saved: {path}"
)
```

def main():
client = create_gemini_client()

```
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

print("\n" + "=" * 70)
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

print(
    "\nGENERATING ARTICLES..."
)

generated_count = 0

for article in selected:
    source_text = read_source_page(
        article["link"]
    )

    if not source_text:
        print(
            "Skipping article because "
            "source text could not be read."
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

    time.sleep(2)

print("\n" + "=" * 70)

print(
    f"ARTICLE GENERATION COMPLETE: "
    f"{generated_count}/{len(selected)}"
)

print("=" * 70)
```

if **name** == "**main**":
main()
