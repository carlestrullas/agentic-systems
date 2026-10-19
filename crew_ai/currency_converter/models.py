"""
Pydantic schema shared by the query parser and the currency tool.

The same model is used twice:

1. As `output_pydantic` of the parsing task, so the first agent turns a
   free-text question into a validated `ConversionRequest`.
2. As `args_schema` of `CurrencyConverterTool`, so the second agent calls the
   tool with exactly the same fields.

Using one schema for both guarantees the hand-off between agents always matches
what the tool expects.
"""

from pydantic import BaseModel, Field, field_validator


class ConversionRequest(BaseModel):
    """A currency conversion extracted from the user's question."""

    amount: float = Field(..., gt=0, description="The amount of money to convert, e.g. 100.")
    from_currency: str = Field(
        ..., description="ISO 4217 code of the source currency, e.g. 'USD' for US dollars."
    )
    to_currency: str = Field(
        ..., description="ISO 4217 code of the target currency, e.g. 'EUR' for euros."
    )

    @field_validator("from_currency", "to_currency")
    @classmethod
    def normalise_code(cls, value: str) -> str:
        code = value.strip().upper()
        if len(code) != 3 or not code.isalpha():
            raise ValueError(f"'{value}' is not a 3-letter ISO 4217 currency code")
        return code
