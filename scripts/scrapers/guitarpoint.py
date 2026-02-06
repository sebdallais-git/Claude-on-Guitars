#!/usr/bin/env python3
"""
guitarpoint — scraper for guitarpoint.de

NOTE: This is a template. You'll need to:
1. Inspect guitarpoint.de manually to find:
   - Category URLs (acoustic, electric, bass)
   - Product listing HTML structure (CSS selectors)
   - Product detail page structure
2. Update the selectors in this file accordingly
3. Test with a single page first before running the full scraper
"""

import re
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.guitarpoint.de"
CATEGORIES = [
    "/vintage-guitars/",  # UPDATE THESE URLs
    "/electric-guitars/",
    "/bass-guitars/",
]

HTTP_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,de;q=0.8",
}


def fetch_soup(url):
    """Fetch and parse HTML from URL."""
    try:
        resp = requests.get(url, headers=HTTP_HEADERS, timeout=15)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, "html.parser")
    except requests.RequestException as e:
        print(f"  [!] {url} → {e}")
        return None


def parse_listings(soup):
    """
    Extract guitar listings from a category page.

    Returns list of dicts: [{"id": ..., "title": ..., "price": ..., "url": ...}, ...]

    TODO: Update these selectors based on actual guitarpoint.de HTML structure.
    """
    guitars = []

    # EXAMPLE - you'll need to inspect the actual HTML:
    # Look for product cards/items - common patterns:
    #   - <div class="product-item">
    #   - <article class="guitar-card">
    #   - <li class="product">

    for item in soup.find_all("div", class_="product-item"):  # PLACEHOLDER
        try:
            # Extract product ID from URL or data attribute
            link = item.find("a", href=True)
            if not link:
                continue

            url = link["href"]
            if not url.startswith("http"):
                url = f"{BASE_URL}{url}"

            # Extract ID from URL (e.g., /product/12345 → "12345")
            pid = re.search(r"/(\d+)", url)
            pid = pid.group(1) if pid else url

            # Extract title
            title_tag = item.find("h2") or item.find("h3") or link  # ADJUST
            title = title_tag.get_text(strip=True) if title_tag else "Unknown"

            # Extract price
            price_tag = item.find("span", class_="price")  # ADJUST
            price = price_tag.get_text(strip=True) if price_tag else "N/A"

            guitars.append({
                "id": pid,
                "title": title,
                "price": price,
                "url": url,
                "on_hold": False,  # Detect if marked as "reserved" or similar
            })
        except Exception as e:
            print(f"  [!] Error parsing item: {e}")
            continue

    return guitars


def parse_condition(page_html):
    """
    Extract condition from product detail page.

    Common patterns:
    - "Condition: Excellent"
    - "Zustand: Sehr gut" (German)

    Returns normalized condition string or None.
    """
    # Look for condition mentions (English or German)
    m = re.search(
        r"(?:condition|zustand):\s*(\w+(?:\s+\w+)?)",
        page_html,
        re.IGNORECASE
    )
    if m:
        return m.group(1).strip().lower()
    return None


def scrape_all():
    """Scrape all categories and return all guitar listings."""
    all_guitars = {}

    for category in CATEGORIES:
        print(f"  Scraping {category} ...")
        soup = fetch_soup(f"{BASE_URL}{category}")

        if not soup:
            continue

        listings = parse_listings(soup)
        print(f"    Found {len(listings)} items")

        for guitar in listings:
            all_guitars.setdefault(guitar["id"], guitar)

        # TODO: Handle pagination if category has multiple pages
        # Look for "next page" links or page numbers

    return list(all_guitars.values())


def test():
    """Test scraper on a single category page."""
    print("\n=== Testing guitarpoint.de scraper ===\n")

    # Test first category
    if CATEGORIES:
        url = f"{BASE_URL}{CATEGORIES[0]}"
        print(f"Fetching {url} ...\n")

        soup = fetch_soup(url)
        if soup:
            listings = parse_listings(soup)
            print(f"\nFound {len(listings)} listings:\n")

            for i, guitar in enumerate(listings[:5], 1):  # Show first 5
                print(f"{i}. {guitar['title']}")
                print(f"   Price: {guitar['price']}")
                print(f"   URL: {guitar['url']}\n")
        else:
            print("Failed to fetch page. Check URL or headers.")


if __name__ == "__main__":
    test()
