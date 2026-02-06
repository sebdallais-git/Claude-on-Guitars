#!/usr/bin/env python3
"""
currency — EUR ↔ USD conversion utilities

Uses a fixed rate for now (can be updated to use live API later).
"""

# Fixed conversion rate (update periodically or use API)
# As of Feb 2026: 1 EUR ≈ 1.09 USD
EUR_TO_USD = 1.09
USD_TO_EUR = 1 / EUR_TO_USD


def eur_to_usd(amount_eur):
    """Convert EUR to USD."""
    if amount_eur is None:
        return None
    return amount_eur * EUR_TO_USD


def usd_to_eur(amount_usd):
    """Convert USD to EUR."""
    if amount_usd is None:
        return None
    return amount_usd * USD_TO_EUR


def normalize_to_usd(amount, currency="USD"):
    """
    Normalize any price to USD.

    Args:
        amount: Price value
        currency: "USD", "EUR", or None

    Returns:
        Price in USD
    """
    if amount is None:
        return None

    currency = (currency or "USD").upper()

    if currency == "USD":
        return float(amount)
    elif currency == "EUR":
        return eur_to_usd(float(amount))
    else:
        return float(amount)  # Assume USD if unknown


def format_price(amount, currency="USD", show_currency=True):
    """
    Format price with currency symbol.

    Args:
        amount: Price value
        currency: "USD" or "EUR"
        show_currency: Whether to show the currency code

    Returns:
        Formatted string like "$1,234.56" or "€1.234,56"
    """
    if amount is None:
        return "N/A"

    currency = (currency or "USD").upper()

    try:
        amount = float(amount)
    except (ValueError, TypeError):
        return str(amount)

    if currency == "EUR":
        # European format: €1.234,56
        formatted = f"€{amount:,.2f}"
        if show_currency:
            formatted += " EUR"
        return formatted
    else:
        # US format: $1,234.56
        formatted = f"${amount:,.2f}"
        if show_currency:
            formatted += " USD"
        return formatted


def format_with_conversion(amount, currency="USD"):
    """
    Format price and show conversion.

    Examples:
        "$1,234.56 (€1,132.64)"
        "€5,000.00 ($5,450.00)"
    """
    if amount is None:
        return "N/A"

    currency = (currency or "USD").upper()

    try:
        amount = float(amount)
    except (ValueError, TypeError):
        return str(amount)

    if currency == "EUR":
        usd = eur_to_usd(amount)
        return f"€{amount:,.2f} (${usd:,.2f})"
    else:
        eur = usd_to_eur(amount)
        return f"${amount:,.2f} (€{eur:,.2f})"


# Test
if __name__ == "__main__":
    print("Currency Conversion Test\n")

    print("EUR → USD:")
    print(f"  €1,000 = ${eur_to_usd(1000):,.2f}")
    print(f"  €5,000 = ${eur_to_usd(5000):,.2f}")

    print("\nUSD → EUR:")
    print(f"  $1,000 = €{usd_to_eur(1000):,.2f}")
    print(f"  $5,000 = €{usd_to_eur(5000):,.2f}")

    print("\nFormatting:")
    print(f"  {format_price(1234.56, 'USD')}")
    print(f"  {format_price(1234.56, 'EUR')}")

    print("\nWith Conversion:")
    print(f"  {format_with_conversion(5000, 'EUR')}")
    print(f"  {format_with_conversion(5000, 'USD')}")
