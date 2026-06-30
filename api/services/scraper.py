"""
URL Scraper — Extract text content from news article URLs.

Uses httpx (async) + BeautifulSoup to fetch and parse HTML content.
Handles common news portal structures and gracefully fails for
paywalled or blocked content (BR3).
"""

import httpx
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import ipaddress
import socket

def is_safe_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"): return False
        
        # Resolve hostname
        ip = socket.gethostbyname(parsed.hostname)
        ip_obj = ipaddress.ip_address(ip)
        
        # Block private, loopback, multicast
        if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_multicast:
            return False
        return True
    except Exception:
        return False


# Common HTML tags that typically contain article body text
ARTICLE_SELECTORS = [
    "article",
    '[class*="article-body"]',
    '[class*="content-body"]',
    '[class*="detail-content"]',
    '[class*="read__content"]',
    '[class*="post-content"]',
    '[itemprop="articleBody"]',
    ".detail__body-text",
    ".content__body",
]

# Tags to remove (noise)
NOISE_TAGS = ["script", "style", "nav", "footer", "header", "aside", "iframe", "noscript"]


async def scrape_url(url: str) -> dict:
    """
    Scrape text content from a news article URL.

    Args:
        url: The URL of the news article.

    Returns:
        Dict with 'title' and 'text' keys.

    Raises:
        ValueError: If the URL cannot be scraped or no text is found.
    """
    if not is_safe_url(url):
        raise ValueError("URL ditolak. URL tidak valid atau merujuk pada IP internal (potensi SSRF).")

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
    }

    try:
        async with httpx.AsyncClient(
            follow_redirects=True, timeout=10.0
        ) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
    except httpx.HTTPStatusError as e:
        raise ValueError(
            f"Konten dari URL ini tidak dapat diakses (HTTP {e.response.status_code}). "
            "Silakan copy-paste teks artikelnya secara manual."
        ) from e
    except (httpx.RequestError, httpx.TimeoutException) as e:
        raise ValueError(
            "Konten dari URL ini tidak dapat diakses "
            "(kemungkinan dilindungi paywall atau anti-bot). "
            "Silakan copy-paste teks artikelnya secara manual."
        ) from e

    soup = BeautifulSoup(response.text, "html.parser")

    # Remove noise elements
    for tag in NOISE_TAGS:
        for element in soup.find_all(tag):
            element.decompose()

    # Extract title
    title = ""
    title_tag = soup.find("h1")
    if title_tag:
        title = title_tag.get_text(strip=True)
    elif soup.title:
        title = soup.title.get_text(strip=True)

    # Try to find article body using common selectors
    article_text = ""
    for selector in ARTICLE_SELECTORS:
        element = soup.select_one(selector)
        if element:
            # Get all paragraph text within the article body
            paragraphs = element.find_all("p")
            if paragraphs:
                article_text = "\n\n".join(
                    p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)
                )
                break

    # Fallback: get all paragraphs from body
    if not article_text:
        body = soup.find("body")
        if body:
            paragraphs = body.find_all("p")
            article_text = "\n\n".join(
                p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)
            )

    if not article_text or len(article_text.split()) < 10:
        raise ValueError(
            "Konten dari URL ini tidak dapat diakses "
            "(kemungkinan dilindungi paywall atau anti-bot). "
            "Silakan copy-paste teks artikelnya secara manual."
        )

    # Combine title + body for analysis
    full_text = f"{title}\n\n{article_text}" if title else article_text

    return {"title": title, "text": full_text}
