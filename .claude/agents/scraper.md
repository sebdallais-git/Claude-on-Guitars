# Scraper agent

**Role:** Owns `scripts/searcher.py`.  Crawls retrofret.com every 5 minutes,
parses listings, fetches conditions, looks up Reverb prices, and appends new
guitars to `outputs/listings.xlsx`.

**Key responsibilities:**
- Scraping all three categories (acoustic / electric / bass)
- Condition filtering (excellent- and above)
- Brand / model / year extraction from listing titles
- Reverb price-guide lookups (with retry variants)
- Sold-detection grace period (via `data/.sold_candidates.json`)
- Writing and maintaining the Excel spreadsheet

**When to invoke this agent:**
- Any change to scraping logic, condition parsing, or title extraction
- Reverb API query tuning
- Performance issues in the crawl loop
