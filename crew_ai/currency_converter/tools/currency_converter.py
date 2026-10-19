"""
A custom CrewAI tool that converts money using live exchange rates.

A custom tool is a class that inherits from `BaseTool` and defines:

* `name` and `description`: what the agent reads to decide when to use it.
* `args_schema`: a Pydantic model describing the arguments; CrewAI validates
  the agent's call against it before running the tool.
* `_run(...)`: the code executed when the agent calls the tool.

Exchange rates come from ExchangeRate-API. With EXCHANGE_RATE_API_KEY set it
uses the keyed endpoint; otherwise it falls back to the open access endpoint,
which needs no key but is updated once a day and rate-limited.
"""

import os
from typing import Type

import requests
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from models import ConversionRequest

KEYED_URL = "https://v6.exchangerate-api.com/v6/{api_key}/latest/{base}"
OPEN_URL = "https://open.er-api.com/v6/latest/{base}"


def _api_key_from_env() -> str | None:
    key = os.getenv("EXCHANGE_RATE_API_KEY", "").strip()
    return key if key and key != "REPLACE_ME" else None


class CurrencyConverterTool(BaseTool):
    name: str = "Currency Converter Tool"
    description: str = (
        "Converts an amount of money from one currency to another using live exchange "
        "rates. Input: amount, from_currency and to_currency as ISO 4217 codes (e.g. USD, EUR)."
    )
    args_schema: Type[BaseModel] = ConversionRequest

    # Read when the tool is created (after load_dotenv), not when this module is imported.
    api_key: str | None = Field(default_factory=_api_key_from_env)
    timeout: float = 10.0

    def _fetch_rates(self, base: str) -> dict[str, float]:
        url = (
            KEYED_URL.format(api_key=self.api_key, base=base)
            if self.api_key
            else OPEN_URL.format(base=base)
        )
        response = requests.get(url, timeout=self.timeout)
        data = response.json()

        if response.status_code != 200 or data.get("result") != "success":
            raise RuntimeError(data.get("error-type", f"HTTP {response.status_code}"))

        # The keyed endpoint returns "conversion_rates"; the open endpoint returns "rates".
        return data.get("conversion_rates") or data["rates"]

    def _run(self, amount: float, from_currency: str, to_currency: str) -> str:
        from_currency, to_currency = from_currency.upper(), to_currency.upper()

        try:
            rates = self._fetch_rates(from_currency)
        except (requests.RequestException, RuntimeError, ValueError, KeyError) as error:
            return f"Error: could not fetch exchange rates for {from_currency} ({error})."

        if to_currency not in rates:
            return f"Error: unknown target currency code '{to_currency}'."

        rate = rates[to_currency]
        return (
            f"{amount:,.2f} {from_currency} = {amount * rate:,.2f} {to_currency} "
            f"(rate: 1 {from_currency} = {rate:.6f} {to_currency})"
        )
