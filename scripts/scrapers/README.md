# Site Scrapers

Each scraper module handles a specific vintage guitar marketplace.

## Adding a New Site

1. **Inspect the site manually:**
   - Open the site in your browser
   - Right-click → Inspect Element
   - Find product listings and note the HTML structure

2. **Copy the template** (guitarpoint.py) and update:
   - `BASE_URL` - site domain
   - `CATEGORIES` - URLs for different guitar types
   - `parse_listings()` - CSS selectors for product cards
   - `parse_condition()` - pattern for extracting condition

3. **Test with one page first:**
   ```bash
   python3 scripts/scrapers/guitarpoint.py
   ```

4. **Common selectors to look for:**
   - Product container: `.product`, `.item`, `article`
   - Title: `h2`, `h3`, `.product-title`
   - Price: `.price`, `.amount`, `span[class*="price"]`
   - Link: `a[href*="product"]`

## Handling 403 Errors

Some sites block automated requests. Try:
- Adding more headers (Accept-Language, Referer)
- Using rotating User-Agents
- Adding delays between requests
- Using Selenium/Playwright for JavaScript-heavy sites
