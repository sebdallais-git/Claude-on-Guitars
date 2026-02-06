#!/usr/bin/env python3
"""
rudysmusic — scraper for rudysmusic.com (Soho & Scarsdale, NY)

Shopify-based vintage guitar marketplace.
Prices in USD.
Categories: Electric, Acoustic, Bass
"""

import re
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://rudysmusic.com"

# Shopify collection URLs
CATEGORIES = [
    "/collections/electric-guitars",
    "/collections/acoustic-guitars",
    "/collections/bass-guitars",
]

HTTP_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
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
    Extract guitar listings from Shopify collection page.

    This site uses custom Empire theme classes:
    - a.productitem--image-link - product links
    """
    guitars = []
    seen = set()

    # Find all product links
    for link in soup.find_all("a", class_="productitem--image-link"):
        try:
            url = link["href"]
            if not url.startswith("http"):
                url = f"{BASE_URL}{url}"

            # Extract product ID from URL slug
            slug_match = re.search(r"/products/([^/?]+)", url)
            if not slug_match:
                continue

            pid = slug_match.group(1)
            if pid in seen:
                continue
            seen.add(pid)

            # Find the parent product item container
            parent = link.find_parent("div", class_=re.compile(r"productitem"))
            if not parent:
                parent = link.find_parent("div")

            # Extract title - look for productitem--title or similar
            title_tag = parent.find(class_=re.compile(r"productitem--title")) if parent else None
            if not title_tag:
                # Fallback: look for any heading or strong text
                title_tag = parent.find(["h2", "h3", "strong"]) if parent else None

            title = title_tag.get_text(strip=True) if title_tag else pid.replace("-", " ").title()

            # Extract price - look for .money with data-price attribute
            price_tag = parent.find("span", class_="money", attrs={"data-price": True}) if parent else None
            if not price_tag and parent:
                # Fallback to any .money span
                price_tag = parent.find("span", class_="money")
            price = price_tag.get_text(strip=True) if price_tag else "N/A"

            # Check if sold out
            sold_tag = parent.find(string=re.compile(r"sold out", re.I)) if parent else None
            if sold_tag:
                continue

            guitars.append({
                "id": pid,
                "title": title,
                "price": price,
                "url": url,
                "on_hold": False,
            })

        except Exception as e:
            print(f"  [!] Error parsing item: {e}")
            continue

    return guitars


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

    return list(all_guitars.values())


def test():
    """Test scraper on electric guitars collection."""
    print("\n=== Testing rudysmusic.com scraper ===\n")

    # Test first category
    url = f"{BASE_URL}{CATEGORIES[0]}"
    print(f"Fetching {url} ...\n")

    soup = fetch_soup(url)
    if soup:
        listings = parse_listings(soup)
        print(f"\nFound {len(listings)} listings:\n")

        # Show first 10
        for i, guitar in enumerate(listings[:10], 1):
            print(f"{i}. {guitar['title']}")
            print(f"   Price: {guitar['price']}")
            print(f"   URL: {guitar['url']}\n")
    else:
        print("Failed to fetch page.")


if __name__ == "__main__":
    test()
