#!/usr/bin/env python3
"""Debug script to inspect rudysmusic.com HTML structure."""

import requests
from bs4 import BeautifulSoup

url = "https://rudysmusic.com/collections/electric-guitars"

resp = requests.get(url, timeout=15)
soup = BeautifulSoup(resp.text, "html.parser")

# Save full HTML to file
with open("/tmp/rudysmusic.html", "w") as f:
    f.write(soup.prettify())

print("HTML saved to /tmp/rudysmusic.html")
print("\nSearching for product containers...")

# Try different selectors
selectors = [
    ("div.collection__item", soup.find_all("div", class_="collection__item")),
    ("div.product-item", soup.find_all("div", class_="product-item")),
    ("div[class*='product']", soup.find_all("div", class_=lambda x: x and "product" in x.lower())),
    ("article", soup.find_all("article")),
    ("a[href*='/products/']", soup.find_all("a", href=lambda x: x and "/products/" in x)),
]

for selector, results in selectors:
    print(f"\n{selector}: {len(results)} found")
    if results:
        print(f"  First item class: {results[0].get('class', 'N/A')}")
        print(f"  Preview: {str(results[0])[:200]}...")

# Look for JSON data
scripts = soup.find_all("script", type="application/json")
print(f"\n\nJSON script tags: {len(scripts)}")
for i, script in enumerate(scripts[:3]):
    print(f"\nScript {i+1} (first 300 chars):")
    print(script.string[:300] if script.string else "Empty")
