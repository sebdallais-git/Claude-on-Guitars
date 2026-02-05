# Command: /scan

**What it does:** Runs a single scrape cycle of retrofret.com and appends
any new listings to `outputs/listings.xlsx`.  Useful for a quick manual
refresh without starting the full 5-minute loop.

**How to run:**
```bash
python3 scripts/searcher.py   # runs the full loop (Ctrl-C to stop after one cycle)
```

For a one-shot scrape the simplest approach is to start `searcher.py`,
wait for the first `"next crawl in 5 min"` message, then Ctrl-C.
