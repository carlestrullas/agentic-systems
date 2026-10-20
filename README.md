# Agentic Systems

Hands-on projects on building **agentic systems**: applications in which one or more agents powered by large language models (LLMs) reason, plan and use tools to complete tasks autonomously.

The repository is organised **by framework**. Each folder contains self-contained examples, from a single agent with one tool to multi-agent workflows, with the code and the ideas behind it, so the same problems can be compared across different approaches.

## Frameworks and examples

| Framework | Example | Description |
|---|---|---|
| [CrewAI](crew_ai/) | [`researcher_agent`](crew_ai/researcher_agent/) | A research analyst agent that searches the web and writes a structured, sourced report on any topic. Works with Ollama or an API key. |
| [CrewAI](crew_ai/) | [`technical_writer_agent`](crew_ai/technical_writer_agent/) | A technical writer agent that drafts articles, plus a summarizer agent that reads files with a tool. Works with Ollama or an API key. |
| [CrewAI](crew_ai/) | [`research_crew`](crew_ai/research_crew/) | A three-agent crew (researcher, summarizer, fact-checker) built as a modular class with YAML config. Works with Ollama or an API key. |
| [CrewAI](crew_ai/) | [`entity_extractor`](crew_ai/entity_extractor/) | Extracts subject-relation-object triplets from text as a validated Pydantic object (structured output). Works with Ollama or an API key. |
| [CrewAI](crew_ai/) | [`currency_converter`](crew_ai/currency_converter/) | Answers money questions with a custom live exchange-rate tool and a query-parsing agent. Works with Ollama or an API key. |
| [CrewAI](crew_ai/) | [`flows`](crew_ai/flows/) | Event-driven workflows with CrewAI Flows: chained steps, shared state, conditional logic, routing and crews inside flows. Works with Ollama or an API key. |

More frameworks (such as LangGraph, the OpenAI Agents SDK, the Claude Agent SDK or agents built from scratch) and more complex examples will be added over time.

## Key concepts

| Concept | Description |
| --- | --- |
| **Agent** | An LLM that decides which actions to take in a loop until it reaches a goal. |
| **Tools** | External functions the agent can call (search, APIs, code execution, files…). |
| **Memory** | Mechanisms for retaining context across steps or sessions. |
| **Planning** | Breaking a complex task down into manageable subtasks. |
| **Multi-agent** | Several specialised agents that collaborate or coordinate with each other. |

## Repository structure

```
agentic-systems/
├── README.md
└── crew_ai/
    ├── README.md
    ├── researcher_agent/
    │   ├── researcher.py
    │   ├── llm.py
    │   ├── requirements.txt
    │   ├── .env.example
    │   └── README.md
    ├── technical_writer_agent/
    │   ├── writer.py
    │   ├── summarizer.py
    │   ├── llm.py
    │   ├── requirements.txt
    │   ├── .env.example
    │   └── README.md
    ├── research_crew/
    │   ├── main.py
    │   ├── research_crew.py
    │   ├── llm.py
    │   ├── config/
    │   │   ├── agents.yaml
    │   │   └── tasks.yaml
    │   ├── requirements.txt
    │   ├── .env.example
    │   └── README.md
    ├── entity_extractor/
    │   ├── main.py
    │   ├── extractor_crew.py
    │   ├── models.py
    │   ├── llm.py
    │   ├── config/
    │   ├── requirements.txt
    │   ├── .env.example
    │   └── README.md
    ├── currency_converter/
    │   ├── main.py
    │   ├── currency_crew.py
    │   ├── models.py
    │   ├── tools/
    │   │   └── currency_converter.py
    │   ├── llm.py
    │   ├── config/
    │   ├── requirements.txt
    │   ├── .env.example
    │   └── README.md
    └── flows/
        ├── 01_basic_flow.py
        ├── 02_unstructured_state.py
        ├── 03_structured_state.py
        ├── 04_or_and.py
        ├── 05_router.py
        ├── poem_flow/                # crewai create flow structure
        │   ├── pyproject.toml
        │   ├── .env.example
        │   ├── README.md
        │   ├── tests/
        │   └── src/poem_flow/
        │       ├── main.py
        │       ├── llm.py
        │       ├── crews/poem_crew/
        │       └── tools/custom_tool.py
        ├── llm.py
        ├── requirements.txt
        ├── .env.example
        └── README.md
```

## Getting started

1. Clone the repository:

   ```bash
   git clone https://github.com/carlestrullas/agentic-systems.git
   cd agentic-systems
   ```

2. Go to the example you want to run and follow its README. Each example has its own `requirements.txt` and a `.env.example` file listing the API keys it needs.

> **Local or hosted models:** all examples run either on a local model served by [Ollama](https://ollama.com) (free, no API key) or on a hosted provider (OpenAI, Anthropic, Gemini, Groq…) with an API key. You switch between them by changing the `MODEL` line in `.env`.

> **API keys:** never commit real keys. Copy `.env.example` to `.env` (which is git-ignored) and replace the `REPLACE_ME` placeholders there.

## Author

Carles Trullàs — [@carlestrullas](https://github.com/carlestrullas)
