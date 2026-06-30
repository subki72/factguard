"""
News Crawler Service — Scrape political articles from Indonesian news portals.

Runs daily at 08:00 WIB (BR11). Only scrapes political category (BR12).
Analyzes each article via Groq and saves to crawled_articles table.

Portal list from Glossary Domain document (02-Glossary-Domain.md).
"""

import httpx
from bs4 import BeautifulSoup

from api.services.groq_analyzer import analyze_text
from api.services.supabase_client import get_supabase_client
from api.utils.language_detector import detect_language


# News portal configs — URL to their politics/national section RSS or page
# Each portal has different structure, so we define scraping targets per portal
PORTAL_CONFIGS = [
    {
        "name": "detik.com",
        "politics_url": "https://news.detik.com/indeks/politik",
        "article_selector": "article a[href]",
        "base_url": "https://news.detik.com",
    },
    {
        "name": "kompas.com",
        "politics_url": "https://nasional.kompas.com/politik",
        "article_selector": ".articleList a.article__link",
        "base_url": "https://nasional.kompas.com",
    },
    {
        "name": "tirto.id",
        "politics_url": "https://tirto.id/politik",
        "article_selector": "a.news-list-item",
        "base_url": "https://tirto.id",
    },
    {
        "name": "tempo.co",
        "politics_url": "https://nasional.tempo.co/politik",
        "article_selector": ".card-box a",
        "base_url": "https://nasional.tempo.co",
    },
    {
        "name": "antaranews.com",
        "politics_url": "https://www.antaranews.com/politik",
        "article_selector": ".card__post a",
        "base_url": "https://www.antaranews.com",
    },
]

# Maximum articles to crawl per portal per run (to stay within Groq free tier)
MAX_ARTICLES_PER_PORTAL = 3


async def crawl_and_analyze() -> dict:
    """
    Crawl political articles from all portals and analyze them.

    Returns:
        Summary dict with counts of articles crawled and analyzed.
    """
    supabase = get_supabase_client()
    total_crawled = 0
    total_analyzed = 0
    errors = []

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
    }

    for portal in PORTAL_CONFIGS:
        try:
            # Step 1: Fetch the politics index page
            async with httpx.AsyncClient(
                follow_redirects=True, timeout=10.0
            ) as client:
                response = await client.get(portal["politics_url"], headers=headers)
                response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            # Step 2: Extract article links
            links = soup.select(portal["article_selector"])
            article_urls = []

            for link in links[:MAX_ARTICLES_PER_PORTAL * 2]:  # Fetch extra in case of duplicates
                href = link.get("href", "")
                if href.startswith("/"):
                    href = portal["base_url"] + href
                if href.startswith("http") and href not in article_urls:
                    article_urls.append(href)

            # Step 3: For each article, check if already crawled, then scrape & analyze
            for url in article_urls[:MAX_ARTICLES_PER_PORTAL]:
                # Check if URL already exists in DB
                existing = (
                    supabase.table("crawled_articles")
                    .select("id")
                    .eq("url", url)
                    .execute()
                )
                if existing.data:
                    continue  # Skip already crawled articles

                total_crawled += 1

                try:
                    # Scrape article content
                    from api.services.scraper import scrape_url
                    article_data = await scrape_url(url)

                    # Detect language and analyze
                    lang = detect_language(article_data["text"])
                    analysis = await analyze_text(article_data["text"], lang)

                    # Save to database
                    supabase.table("crawled_articles").insert({
                        "source_portal": portal["name"],
                        "url": url,
                        "title": article_data["title"],
                        "content_text": article_data["text"][:50000],
                        "score": analysis["score"],
                        "label": analysis["label"],
                        "reasoning": analysis["reasoning"],
                    }).execute()

                    total_analyzed += 1

                except Exception as e:
                    errors.append(f"{portal['name']}: {url} — {str(e)[:100]}")

        except Exception as e:
            errors.append(f"{portal['name']}: Failed to fetch index — {str(e)[:100]}")

    return {
        "total_crawled": total_crawled,
        "total_analyzed": total_analyzed,
        "portals_attempted": len(PORTAL_CONFIGS),
        "errors": errors[:10],  # Limit error list
    }
