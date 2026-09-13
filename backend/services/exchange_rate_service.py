import json
from decimal import Decimal, InvalidOperation
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from services.errors import ServiceError


SUPPORTED_CURRENCIES = {"USD", "EUR", "GBP", "AED", "SGD"}
_API_URL = "https://api.frankfurter.dev/v2/rate/{base}/inr"


def current_rate_to_inr(currency: str) -> dict:
    """Return a display-only reference rate; nothing is written to the database."""
    currency = currency.upper()
    if currency not in SUPPORTED_CURRENCIES:
        raise ServiceError(422, "Unsupported export currency")
    try:
        request = Request(
            _API_URL.format(base=currency.lower()),
            headers={"Accept": "application/json"},
        )
        with urlopen(request, timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))
        rate = Decimal(str(data["rate"]))
        if rate <= 0:
            raise ValueError("non-positive rate")
        return {
            "base_currency": currency,
            "quote_currency": "INR",
            "rate": rate,
            "rate_date": data["date"],
            "source": "Frankfurter",
        }
    except (HTTPError, URLError, TimeoutError, ValueError, KeyError, InvalidOperation, json.JSONDecodeError):
        raise ServiceError(503, "Live reference rate is unavailable. Enter your rate manually.")
