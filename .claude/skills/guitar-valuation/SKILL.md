# Skill: Guitar Valuation

Knows how to value a vintage guitar using Reverb price-guide data and the
project's appreciation model.

## Appreciation model

Rates are annual, compounded.  Determined by two axes:

1. **Era** — which `_ERA_RATES` band the guitar's year falls into
2. **Brand tier** — major (Gibson, Fender, Martin …) vs minor

```
Pre-1950   → 10 % / 5 %
1950-1965  →  8 % / 4 %
1965-1980  →  5 % / 3 %
1980-2000  →  3 % / 2 %
2000+      →  1 % / 0 %
```

## Reverb lookup strategy

`reverb_price(brand, model, year)` tries queries most-specific-first:

1. full brand + full model + year
2. short brand (last word) + full model + year
3. … same two without year
4. … truncated model (first 2 words) variants

Brand matching is lenient: strips non-alpha and checks containment both ways
(`"C. F. Martin"` matches Reverb's `"Martin"`).

## Key functions

| Function | File | Returns |
|---|---|---|
| `reverb_price(brand, model, year)` | searcher.py | `(lo, hi)` or `(None, None)` |
| `appreciation_rate(brand, year)` | valuation.py | float (e.g. 0.08) |
| `project_value(current, brand, year, years)` | valuation.py | float or None |
| `value_guitar(brand, model, year)` | valuation.py | dict with current / 1y / 2y |
