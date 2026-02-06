#!/usr/bin/env python3
"""
scorer — scores active retrofret listings and writes top recommendations.

Scoring dimensions (weights tunable in data/budget.json):
  1. Value opportunity   — how far below (or above) the Reverb market range
  2. Appreciation        — projected annual rate from the valuation model
  3. Collection fit      — diversification bonus, duplicate penalty, type-gap bonus

Reads budget and weights from data/budget.json.  Writes a "Recommendations"
sheet into outputs/listings.xlsx with the top N guitars, colour-coded by score
and greyed out when over remaining budget.

Run standalone:
    python3 scorer.py
"""

import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

from valuation import appreciation_rate, project_value, read_collection

# ── paths ─────────────────────────────────────────────────────────
_SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_SCRIPT_DIR)
_DATA         = os.path.join(_PROJECT_ROOT, "data")
_OUTPUTS      = os.path.join(_PROJECT_ROOT, "outputs")

XLSX_PATH   = os.path.join(_OUTPUTS, "listings.xlsx")
BUDGET_FILE = os.path.join(_DATA, "budget.json")


def _load_budget():
    with open(BUDGET_FILE) as f:
        return json.load(f)


# ── read active listings ──────────────────────────────────────────
def read_active_listings():
    """Return listings from listings.xlsx that are not sold and not on hold.

    Column layout (13 cols, 0-indexed):
      0: Date Arrived  1: Source       2: Brand/Make   3: Model
      4: Type          5: Year         6: Price        7: Reverb Low
      8: Reverb High   9: Condition   10: URL         11: On Hold
     12: Sold Date
    """
    if not os.path.exists(XLSX_PATH):
        return []
    wb = load_workbook(XLSX_PATH, read_only=True, data_only=True)
    ws = wb.active
    listings = []
    for row in ws.iter_rows(min_row=2, max_col=13, values_only=True):
        url = str(row[10]) if row[10] else ""          # col 11 = URL
        # Support both retrofret ProductID and woodstore/other slug URLs
        m = re.search(r"ProductID=(\d+)", url)
        if m:
            pid = m.group(1)
        else:
            m2 = re.search(r"/products?/([^/?]+)", url)
            if not m2:
                continue
            pid = m2.group(1)
        if row[11] is not None or row[12] is not None:  # On Hold or Sold Date
            continue
        price = None
        if row[6] is not None:                           # col 7 = Price
            try:
                price = float(row[6])
            except (ValueError, TypeError):
                pass
        listings.append({
            "id":         pid,
            "brand":      str(row[2] or ""),             # col 3 = Brand
            "model":      str(row[3] or ""),             # col 4 = Model
            "type":       str(row[4] or ""),             # col 5 = Type
            "year":       str(row[5] or ""),             # col 6 = Year
            "price":      price,
            "reverb_lo":  row[7],                        # col 8 = Reverb Low
            "reverb_hi":  row[8],                        # col 9 = Reverb High
            "condition":  str(row[9] or ""),             # col 10 = Condition
            "url":        url,
        })
    wb.close()
    return listings


# ── scoring ───────────────────────────────────────────────────────
def _score_value(price, reverb_lo, reverb_hi):
    """
    0–100: how good a deal is this listing vs the Reverb market range.
    At or below reverb_lo → 100.  At reverb_hi → 50.  Above → below 50.
    Returns 50 (neutral) when price or Reverb data is missing.
    """
    if price is None or reverb_lo is None or reverb_hi is None:
        return 50.0
    mid = (reverb_lo + reverb_hi) / 2
    if price <= reverb_lo:
        return 100.0
    if price <= mid:
        return 100.0 - 25.0 * (price - reverb_lo) / (mid - reverb_lo)
    if price <= reverb_hi:
        return 75.0 - 25.0 * (price - mid) / (reverb_hi - mid)
    # above reverb_hi: linear drop toward 0
    overshoot = (price - reverb_hi) / reverb_hi
    return max(0.0, 50.0 - 50.0 * overshoot)


def _score_appreciation(brand, year):
    """0–100: maps the 0–10 % annual rate range linearly onto 0–100."""
    rate = appreciation_rate(brand, year)
    return min(100.0, rate / 0.10 * 100)


def _score_fit(entry, collection):
    """
    0–100 collection-fit score.  Starts at 50.
    +20 brand not yet owned (diversification).
    +15 type is under-represented (< 25 % of collection).
    -25 exact brand+model already owned.
    """
    score = 50
    if not collection:
        return score                                # nothing to compare against

    brands_owned = {g["brand"].lower() for g in collection}
    models_owned = {(g["brand"].lower(), g["model"].lower()) for g in collection}
    brand_l      = entry["brand"].lower()
    model_l      = entry["model"].lower()
    type_l       = entry.get("type", "").lower()

    if (brand_l, model_l) in models_owned:
        score -= 25
    elif brand_l not in brands_owned:
        score += 20

    if type_l:
        type_count = sum(1 for g in collection if g["type"].lower() == type_l)
        if type_count / len(collection) < 0.25:
            score += 15

    return max(0, min(100, score))


def score_listing(entry, collection, budget):
    """
    Composite 0–100 score + per-dimension breakdown.
    Returns (total, {"value": …, "appreciation": …, "fit": …}).
    """
    w = budget["weights"]
    s_val = _score_value(entry["price"], entry.get("reverb_lo"), entry.get("reverb_hi"))
    s_app = _score_appreciation(entry["brand"], entry["year"])
    s_fit = _score_fit(entry, collection)

    total = (
        w["value"]      * s_val +
        w["appreciate"] * s_app +
        w["fit"]        * s_fit
    )
    return round(total, 1), {
        "value":        round(s_val, 1),
        "appreciation": round(s_app, 1),
        "fit":          round(s_fit, 1),
    }


# ── write recommendations sheet ───────────────────────────────────
REC_HEADERS = [
    "Rank", "Brand", "Model", "Type", "Year", "Price ($)",
    "Reverb Low $", "Reverb High $", "Condition",
    "Score", "Value", "Apprec.", "Fit",
    "Value in 1 Year ($)", "Value in 2 Years ($)",
    "URL",
]
REC_WIDTHS = [6, 22, 26, 18, 10, 14, 14, 14, 14, 8, 8, 10, 6, 20, 22, 65]

HEADER_FILL  = PatternFill(start_color="2E75B6", end_color="2E75B6", fill_type="solid")
HEADER_FONT  = Font(bold=True, color="FFFFFF", size=11)
URL_FONT     = Font(color="0563C1", underline="single", size=10)
CURRENCY_FMT = "$#,##0.00"


def _score_fill(score):
    """Green >= 80, yellow >= 60, red below."""
    if score >= 80:
        return PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
    if score >= 60:
        return PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")
    return PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")


def write_recommendations(scored, budget):
    """Write (or replace) the 'Recommendations' sheet in listings.xlsx."""
    wb = load_workbook(XLSX_PATH)

    if "Recommendations" in wb.sheetnames:
        del wb["Recommendations"]
    ws = wb.create_sheet("Recommendations")

    # header row
    for col, (header, width) in enumerate(zip(REC_HEADERS, REC_WIDTHS), 1):
        cell           = ws.cell(row=1, column=col, value=header)
        cell.font      = HEADER_FONT
        cell.fill      = HEADER_FILL
        cell.alignment = Alignment(horizontal="center")
        ws.column_dimensions[get_column_letter(col)].width = width
    ws.row_dimensions[1].height = 20

    budget_remaining = budget["total"] - budget["spent"]

    for rank, (entry, total, breakdown) in enumerate(scored, 1):
        row   = rank + 1
        price = entry["price"] or 0
        over  = price > budget_remaining

        ws.cell(row=row, column=1,  value=rank)
        ws.cell(row=row, column=2,  value=entry["brand"])
        ws.cell(row=row, column=3,  value=entry["model"])
        ws.cell(row=row, column=4,  value=entry["type"])
        ws.cell(row=row, column=5,  value=entry["year"])

        if price:
            ws.cell(row=row, column=6, value=price)
            ws.cell(row=row, column=6).number_format = CURRENCY_FMT
        if entry.get("reverb_lo"):
            ws.cell(row=row, column=7, value=entry["reverb_lo"])
            ws.cell(row=row, column=7).number_format = CURRENCY_FMT
        if entry.get("reverb_hi"):
            ws.cell(row=row, column=8, value=entry["reverb_hi"])
            ws.cell(row=row, column=8).number_format = CURRENCY_FMT
        ws.cell(row=row, column=9, value=entry["condition"])

        # score with colour
        score_cell      = ws.cell(row=row, column=10, value=total)
        score_cell.fill = _score_fill(total)

        ws.cell(row=row, column=11, value=breakdown["value"])
        ws.cell(row=row, column=12, value=breakdown["appreciation"])
        ws.cell(row=row, column=13, value=breakdown["fit"])

        # projected values (Reverb midpoint, or listing price as fallback)
        if entry.get("reverb_lo") and entry.get("reverb_hi"):
            base = (entry["reverb_lo"] + entry["reverb_hi"]) / 2
        else:
            base = price or None
        v1y = project_value(base, entry["brand"], entry["year"], 1)
        v2y = project_value(base, entry["brand"], entry["year"], 2)
        if v1y:
            ws.cell(row=row, column=14, value=v1y)
            ws.cell(row=row, column=14).number_format = CURRENCY_FMT
        if v2y:
            ws.cell(row=row, column=15, value=v2y)
            ws.cell(row=row, column=15).number_format = CURRENCY_FMT

        # URL
        url_cell           = ws.cell(row=row, column=16, value=entry["url"])
        url_cell.hyperlink = entry["url"]
        url_cell.font      = URL_FONT

        # grey out the whole row when over remaining budget
        if over:
            grey = Font(color="808080", size=10)
            for col in range(1, 16):
                ws.cell(row=row, column=col).font = grey
            url_cell.font = Font(color="808080", size=10, underline="single")

    wb.save(XLSX_PATH)


# ── main ──────────────────────────────────────────────────────────
def run():
    """Score all active listings, print top N, write Recommendations sheet."""
    budget     = _load_budget()
    collection = read_collection()
    listings   = read_active_listings()

    if not listings:
        print("  No active listings found in listings.xlsx.")
        return

    budget_remaining = budget["total"] - budget["spent"]
    print(f"  Budget:          ${budget['total']:>10,.0f} total | "
          f"${budget['spent']:>10,.0f} spent | "
          f"${budget_remaining:>10,.0f} remaining")
    print(f"  Collection:      {len(collection)} guitars")
    print(f"  Active listings: {len(listings)}")
    print(f"  Scoring …\n")

    scored = []
    for entry in listings:
        total, breakdown = score_listing(entry, collection, budget)
        scored.append((entry, total, breakdown))

    scored.sort(key=lambda x: x[1], reverse=True)
    top = scored[:budget["top_n"]]

    # ── terminal summary ──
    print(f"  {'#':<4} {'Brand':<22} {'Model':<24} {'Year':>6} "
          f"{'Price':>10} {'Score':>6}  Budget")
    print(f"  {'─'*85}")
    for rank, (entry, total, _) in enumerate(top, 1):
        price_str  = f"${entry['price']:>9,.0f}" if entry["price"] else "          N/A"
        budget_tag = "OVER" if (entry["price"] or 0) > budget_remaining else "ok"
        print(f"  {rank:<4} {entry['brand']:<22} {entry['model']:<24} "
              f"{entry['year']:>6} {price_str} {total:>6.1f}  {budget_tag}")
    print()

    write_recommendations(top, budget)
    print(f"  'Recommendations' sheet written to listings.xlsx")


if __name__ == "__main__":
    run()
