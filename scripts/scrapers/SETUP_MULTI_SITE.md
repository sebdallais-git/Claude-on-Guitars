# Multi-Site Scraper Setup

## Current Status

| Site | Status | Count | Notes |
|------|--------|-------|-------|
| **retrofret.com** | ✅ Working | 419 | Original scraper, USD |
| **woodstore.fr** | ✅ Integrated | 52 | EUR, Paris-based |
| **rudysmusic.com** | ⚠️ Partial | 33 | Titles/links work, prices TBD |
| **guitarpoint.de** | ❌ Blocked | 0 | 403 error - needs manual setup |

**Multi-site scraper available:** `scripts/searcher_multisite.py`

---

## ✅ woodstore.fr (Ready to Use)

French vintage guitar marketplace based in Paris. Prices in EUR.

**Test it:**
```bash
python3 scripts/scrapers/woodstore.py
```

**Integration:** Ready to add to main workflow. Currently finds:
- Fender guitars (Telecaster, Stratocaster, Jaguar, Musicmaster, etc.)
- Gibson guitars (ES-335, Les Paul, Explorer, etc.)
- Japanese brands (Greco, Orville)
- Prices range from €2,190 to €59,000

---

## ⚠️ guitarpoint.de (Needs Setup)

**Issue:** Site blocks automated requests (403 Forbidden)

**Next steps:**
1. Visit guitarpoint.de manually in browser
2. Note category URLs and HTML structure
3. Update `scripts/scrapers/guitarpoint.py` selectors
4. Test: `python3 scripts/scrapers/guitarpoint.py`

See `SETUP_GUITARPOINT.md` for detailed instructions.

---

## ⚠️ rudymusic.com (SSL Issues)

**Issue:** SSL certificate verification fails

**Next steps:**
1. Verify site is accessible in browser
2. Check if domain/URL is correct
3. May need to contact site or use alternative approach
4. Test: `python3 scripts/scrapers/rudymusic.py`

The scraper is configured to bypass SSL verification for testing (not recommended for production).

---

## Integrating with Main Workflow

Once a scraper is working:

1. **Import in watchdog.py:**
   ```python
   from scrapers import woodstore
   ```

2. **Merge results:**
   ```python
   retrofret_guitars = searcher.scrape_all()
   woodstore_guitars = woodstore.scrape_all()
   all_guitars = retrofret_guitars + woodstore_guitars
   ```

3. **Add site identifier** to distinguish listings:
   ```python
   for g in woodstore_guitars:
       g['source'] = 'woodstore.fr'
   ```

4. **Update Excel sheet** to show source column

5. **Test notifications** work for both sites

---

## Price Handling

Different sites use different currencies:
- retrofret.com → USD ($)
- woodstore.fr → EUR (€)
- guitarpoint.de → EUR (€)

**TODO:** Add currency conversion for unified comparisons in recommendations.
