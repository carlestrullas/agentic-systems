"""
05 · A custom knowledge source: load knowledge from an API.

    Open-Meteo geocoding ──▶ lat/lon ──▶ Open-Meteo forecast ──▶ text ──▶ chunks ──▶ Weather Reporter

Any data can become knowledge by subclassing `BaseKnowledgeSource` and
implementing three methods:

* `validate_content()` → load the data and return it as clean text.
* `add()`              → chunk that text (`self._chunk_text`) and store it
                         (`self._save_documents()`).
* `aadd()`             → the async version of `add()`, which CrewAI now requires.

Extra settings are ordinary Pydantic fields (here `city` and `forecast_days`).
Open-Meteo is free and needs no API key.

Knowledge is a SNAPSHOT taken when the crew starts, not a live connection: it
suits reference data that changes slowly. For data that must be fresh at the
moment the agent acts, give it a tool instead (see `currency_converter`). This
script empties its store on every run so old forecasts do not pile up.

Usage:
    python 05_custom_source.py
    python 05_custom_source.py --city Manresa --question "Will it rain this weekend?"
"""

import argparse
import asyncio
import json
import urllib.parse
import urllib.request

from knowledge_setup import build_embedder, reset_knowledge  # before crewai: it sets the storage

from crewai import Agent, Crew, Process, Task
from crewai.knowledge.source.base_knowledge_source import BaseKnowledgeSource
from pydantic import Field

from llm import build_llm

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

# WMO weather codes used by Open-Meteo (grouped)
WEATHER_CODES = {
    0: "clear sky", 1: "mainly clear", 2: "partly cloudy", 3: "overcast", 45: "fog", 48: "fog",
    51: "light drizzle", 53: "drizzle", 55: "dense drizzle", 61: "light rain", 63: "rain",
    65: "heavy rain", 71: "light snow", 73: "snow", 75: "heavy snow", 80: "rain showers",
    81: "rain showers", 82: "violent rain showers", 95: "thunderstorm", 96: "thunderstorm with hail",
    99: "thunderstorm with hail",
}


def get_json(url: str, **params) -> dict:
    with urllib.request.urlopen(f"{url}?{urllib.parse.urlencode(params)}", timeout=15) as response:
        return json.load(response)


class WeatherKnowledgeSource(BaseKnowledgeSource):
    """Current weather and a short forecast for a city, from the Open-Meteo API."""

    city: str = Field(description="City to get the weather for")
    forecast_days: int = Field(default=3, description="Days of forecast to include (1-7)")

    def validate_content(self) -> str:
        """Fetch the data and format it as text the agent can read."""
        print(f"🌍 Fetching the weather for {self.city}…")
        places = get_json(GEOCODING_URL, name=self.city, count=1).get("results")
        if not places:
            raise ValueError(f"City not found: {self.city}")
        place = places[0]

        data = get_json(
            FORECAST_URL,
            latitude=place["latitude"],
            longitude=place["longitude"],
            current="temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code",
            daily="weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max",
            forecast_days=self.forecast_days,
            timezone="auto",
        )
        now, daily = data["current"], data["daily"]

        lines = [
            f"Weather for {place['name']}, {place.get('country', '')} (local time {now['time']}).",
            f"Current conditions: {WEATHER_CODES.get(now['weather_code'], 'unknown')}, "
            f"{now['temperature_2m']} °C, humidity {now['relative_humidity_2m']} %, "
            f"wind {now['wind_speed_10m']} km/h.",
            "Daily forecast:",
        ]
        for i, day in enumerate(daily["time"]):
            lines.append(
                f"- {day}: {WEATHER_CODES.get(daily['weather_code'][i], 'unknown')}, "
                f"{daily['temperature_2m_min'][i]}–{daily['temperature_2m_max'][i]} °C, "
                f"{daily['precipitation_probability_max'][i]} % chance of rain."
            )
        return "\n".join(lines)

    def add(self) -> None:
        self.chunks.extend(self._chunk_text(self.validate_content()))
        self._save_documents()

    async def aadd(self) -> None:
        text = await asyncio.to_thread(self.validate_content)
        self.chunks.extend(self._chunk_text(text))
        await self._asave_documents()


def main() -> None:
    parser = argparse.ArgumentParser(description="Use an API as a knowledge source.")
    parser.add_argument("--city", default="Barcelona")
    parser.add_argument("--question", default="What is the weather like right now, and do I need an umbrella tomorrow?")
    parser.add_argument("--model", help="Override the MODEL variable from .env")
    args = parser.parse_args()

    reset_knowledge()  # a fresh snapshot on every run

    weather_reporter = Agent(
        role="Weather Reporter",
        goal=f"Answer questions about the weather in {args.city}.",
        backstory="A friendly meteorologist who gives practical, concrete weather advice.",
        knowledge_sources=[WeatherKnowledgeSource(city=args.city)],
        embedder=build_embedder(),
        llm=build_llm(args.model, temperature=0),
        verbose=True,
    )
    task = Task(
        description=f"Answer this question about the weather in {args.city}: {args.question}",
        expected_output="A short answer with the relevant numbers (temperature, chance of rain…).",
        agent=weather_reporter,
    )

    result = Crew(agents=[weather_reporter], tasks=[task], process=Process.sequential, verbose=True).kickoff()

    print("\n" + "=" * 60)
    print(result.raw)
    print("=" * 60)


if __name__ == "__main__":
    main()
