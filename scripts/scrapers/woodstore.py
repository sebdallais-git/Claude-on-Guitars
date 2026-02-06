#!/usr/bin/env python3
"""
woodstore — scraper for woodstore.fr (Paris)

French vintage guitar marketplace using Squarespace.
Prices in EUR (euros).
Categories: All, Fender, Gibson, Fender Japan, Divers (Other brands)
"""

import re
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.woodstore.fr"

# Main guitar category page shows all guitars
CATEGORIES = [
    "/guitares",
]

HTTP_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,fr;q=0.8",
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


def parse_price(price_str):
    """
    Convert French price format to USD equivalent.
    Input: "9 490,00 €" or "2 990,00 €"
    Returns: price in EUR (as float)
    """
    try:
        # Remove €, spaces, and convert comma to dot
        clean = price_str.replace("€", "").replace(" ", "").replace(",", ".")
        return float(clean)
    except (ValueError, AttributeError):
        return None


def parse_listings(soup):
    """
    Extract guitar listings from woodstore.fr page.

    Squarespace site structure:
    - Product links: <a href="/guitares/p/product-slug">
    - Each link contains images, title, and price
    """
    guitars = []

    # Find all product links (Squarespace pattern)
    for link in soup.find_all("a", href=re.compile(r"/guitares/p/")):
        try:
            url = link["href"]
            if not url.startswith("http"):
                url = f"{BASE_URL}{url}"

            # Extract product ID from URL slug
            slug_match = re.search(r"/guitares/p/([^/?]+)", url)
            pid = slug_match.group(1) if slug_match else url

            # Get all text from the link - includes title and price
            text = link.get_text(separator="\n", strip=True)
            lines = [l.strip() for l in text.split("\n") if l.strip()]

            # Parse title and price from text
            # Typical structure: [image alts], "Aperçu", TITLE, PRICE, [status]
            title = "Unknown"
            price_str = "N/A"
            sold = False

            for line in lines:
                # Price pattern: contains € and numbers
                if "€" in line and re.search(r"\d", line):
                    price_str = line
                # Check if sold
                elif "VENDU" in line.upper() or "SOLD" in line.upper():
                    sold = True
                # Title: longer text without € or status keywords
                elif (len(line) > 10 and "€" not in line and
                      "APERÇU" not in line.upper() and
                      "PREVIEW" not in line.upper() and
                      "VENDU" not in line.upper()):
                    title = line

            # Skip if already sold
            if sold:
                continue

            price_float = parse_price(price_str)

            guitars.append({
                "id": pid,
                "title": title,
                "price": f"€{price_float:,.0f}" if price_float else price_str,
                "price_eur": price_float,
                "url": url,
                "on_hold": False,
                "sold": sold,
            })

        except Exception as e:
            print(f"  [!] Error parsing item: {e}")
            continue

    return guitars


def parse_condition(page_html):
    """
    Extract condition from product detail page.
    French terms: "État" or "Condition"
    """
    # Look for condition in French or English
    patterns = [
        r"(?:état|condition):\s*(\w+(?:\s+\w+)?)",
        r"(?:état|condition)\s+:\s*(\w+(?:\s+\w+)?)",
    ]

    for pattern in patterns:
        m = re.search(pattern, page_html, re.IGNORECASE)
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

    return list(all_guitars.values())


def test():
    """Test scraper on the main guitars page."""
    print("\n=== Testing woodstore.fr scraper ===\n")

    url = f"{BASE_URL}/guitares"
    print(f"Fetching {url} ...\n")

    soup = fetch_soup(url)
    if soup:
        listings = parse_listings(soup)
        print(f"\nFound {len(listings)} available listings:\n")

        # Show first 10
        for i, guitar in enumerate(listings[:10], 1):
            print(f"{i}. {guitar['title']}")
            print(f"   Price: {guitar['price']}")
            print(f"   URL: {guitar['url']}\n")
    else:
        print("Failed to fetch page.")


if __name__ == "__main__":
    test()
