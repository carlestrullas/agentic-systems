# Currency Converter

Two agents and a **custom tool** answer money questions written in natural language, using live exchange rates.

```
"How much is 100 dollars in euros today?"
        │
        ▼
Query Analyst ──▶ ConversionRequest(amount=100.0, from_currency="USD", to_currency="EUR")
        │               (structured output, validated by Pydantic)
        ▼
Currency Analyst ──▶ CurrencyConverterTool ──▶ ExchangeRate-API ──▶ "**100 USD = 92.00 EUR** …"
```

| Agent | Tools | Task |
|---|---|---|
| *Senior Financial Query Analyst* | none | Turns the question into a `ConversionRequest` (`output_pydantic`). Maps "dollars" → `USD`, "yen" → `JPY`, etc. |
| *Senior Currency Analyst* | `CurrencyConverterTool` | Calls the tool with the request, gets the live rate and writes the answer. |

The point of the split: the LLM is good at understanding language, but it should never *guess* an exchange rate. That well-defined, factual step is delegated to a tool that calls an API.

## Building a custom tool

A CrewAI tool is a class that inherits from `BaseTool` ([`tools/currency_converter.py`](tools/currency_converter.py)):

```python
class CurrencyConverterTool(BaseTool):
    name: str = "Currency Converter Tool"
    description: str = "Converts an amount of money from one currency to another using live exchange rates. …"
    args_schema: Type[BaseModel] = ConversionRequest      # arguments, validated before _run is called
    api_key: str | None = Field(default_factory=_api_key_from_env)

    def _run(self, amount: float, from_currency: str, to_currency: str) -> str:
        rates = self._fetch_rates(from_currency)
        ...
        return f"{amount:,.2f} {from_currency} = {amount * rate:,.2f} {to_currency} (rate: …)"
```

| Part | Why it matters |
|---|---|
| `name` + `description` | This is all the agent knows about the tool; it decides when and how to call it from this text. |
| `args_schema` | A Pydantic model of the arguments. CrewAI validates every call against it, and its field descriptions tell the agent what to pass. |
| `_run` | The actual code. It returns a string, and errors are returned as messages (not raised) so the agent can explain them instead of crashing. |
| `api_key` with `default_factory` | The key is read when the tool is created, after `.env` is loaded, not when the module is imported. |

You can test the tool on its own, without any LLM:

```bash
python -c "from tools import CurrencyConverterTool; print(CurrencyConverterTool().run(amount=100, from_currency='USD', to_currency='EUR'))"
```

### One schema, two uses

[`models.py`](models.py) defines `ConversionRequest` once and it is used both as the **output** of the parsing task (`output_pydantic=ConversionRequest`) and as the **input** of the tool (`args_schema = ConversionRequest`). The hand-off between the two agents therefore always matches what the tool expects. The model also validates its own data: amounts must be positive and currency codes are upper-cased and must have three letters.

## Files

| File | Content |
|---|---|
| [`models.py`](models.py) | `ConversionRequest` Pydantic model. |
| [`tools/currency_converter.py`](tools/currency_converter.py) | `CurrencyConverterTool`, the custom tool. |
| [`currency_crew.py`](currency_crew.py) | `CurrencyCrew`, a `@CrewBase` class with both agents and tasks. |
| [`config/`](config/) | Agent and task prompts in YAML. |
| [`main.py`](main.py) | Command-line entry point. |

## Setup

```bash
cd crew_ai/currency_converter
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

**Model:** set `MODEL` in `.env` to a local Ollama model (the default, `ollama/llama3.1:8b`) or to a hosted model with its API key. Both options are explained step by step in [Choosing the model](../README.md#choosing-the-model). The second agent must call a tool with the right arguments, so with Ollama use a 7–8B model or larger; 1–3B models often skip the tool and invent a rate.

**Exchange rates (optional):** get a free key at [exchangerate-api.com](https://www.exchangerate-api.com) and set `EXCHANGE_RATE_API_KEY`. Without it the tool uses the provider's open endpoint, which needs no key but is updated once a day and rate-limited.

## Run

```bash
python main.py --query "How much is 100 dollars in euros today?"
python main.py --query "Convert 2500 yen to pounds" --model gpt-4o-mini
```

The script prints the parsed `ConversionRequest` and the final answer. With `verbose=True` you can also see in the console when the analyst calls the tool and what it returns.

## Ideas to extend it

- Add a second tool for historical rates and let the analyst compare today's rate with last month's.
- Give the final task its own `output_pydantic` (amount, rate, timestamp) so another program can consume the answer.
- Build other tools the same way: weather, stock prices, your own database or internal API.
