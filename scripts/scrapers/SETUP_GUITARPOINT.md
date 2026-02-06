# Setting Up guitarpoint.de Scraper

## Quick Start

guitarpoint.de returned a 403 (blocked automated requests), so you'll need to:

### 1. Find the Right URLs

Visit guitarpoint.de manually and find:
- **Category pages** - URLs for acoustic, electric, bass guitars
- **Example product URL** - to understand ID format

Update `CATEGORIES` in `guitarpoint.py`.

### 2. Inspect HTML Structure

On a category page:
1. Right-click any guitar listing → Inspect
2. Find the parent container (e.g., `<div class="product-card">`)
3. Note the selectors for:
   - Product link: `<a href="...">`
   - Title: usually `<h2>` or `<h3>`
   - Price: usually `<span class="price">` or similar

Update `parse_listings()` in `guitarpoint.py`.

### 3. Test

```bash
cd /Users/seb/claude/Claude-on-Guitars/vintage-guitar-collector
python3 scripts/scrapers/guitarpoint.py
```

This will fetch one category page and show the first 5 results.

### 4. Common Issues

**403 Forbidden:**
- The site may require cookies or session tokens
- Try browsing the site first in your browser, then run the scraper
- May need to add `Referer` header or use Selenium

**No results found:**
- Selectors are wrong - re-inspect the HTML
- Site uses JavaScript to load products - may need Playwright

**German language:**
- Condition might be "Zustand" instead of "Condition"
- Update `parse_condition()` regex

## Example: What Good Output Looks Like

```
=== Testing guitarpoint.de scraper ===

Fetching https://www.guitarpoint.de/vintage-guitars/ ...

Found 24 listings:

1. Gibson Les Paul Standard 1959
   Price: €45,000
   URL: https://www.guitarpoint.de/product/12345

2. Fender Stratocaster 1964
   Price: €18,500
   URL: https://www.guitarpoint.de/product/12346
```

## Next Steps After It Works

1. Integrate with main scraper (searcher.py)
2. Add guitarpoint listings to the same Excel sheet
3. Enable Telegram notifications for new guitarpoint finds
