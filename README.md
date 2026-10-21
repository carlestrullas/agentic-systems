# Agentic Systems

Hands-on projects on building **agentic systems**: applications in which one or more agents powered by large language models (LLMs) reason, plan and use tools to complete tasks autonomously.

The repository is organised **by framework**. Each framework folder has its own README with a learning path through its examples, from a single agent with one tool to multi-agent workflows, so the same problems can be compared across different approaches.

## Frameworks

| Framework | Examples | What they cover |
|---|---|---|
| [CrewAI](crew_ai/) | 8 | Agents, tasks and crews; multi-agent pipelines; YAML config and modular crew classes; structured output with Pydantic; custom tools; Flows and multi-crew flows running crews in parallel. |

More frameworks (such as LangGraph, the OpenAI Agents SDK, the Claude Agent SDK or agents built from scratch) will be added over time.

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
├── README.md                 # this file: frameworks and shared conventions
└── <framework>/              # e.g. crew_ai/
    ├── README.md             # learning path, setup and conventions for the framework
    └── <example>/            # one self-contained example
        ├── README.md         # what it does, setup and how to run it
        ├── requirements.txt
        ├── .env.example
        └── ...
```

Each level only describes what is below it: this README lists frameworks, each framework README lists its examples, and each example README explains its own code. Adding an example therefore only touches its framework's README.

## Getting started

1. Clone the repository:

   ```bash
   git clone https://github.com/carlestrullas/agentic-systems.git
   cd agentic-systems
   ```

2. Open the framework folder you are interested in and follow its README: it explains the common setup (including which model to use) and the order in which to go through the examples.

> **Local or hosted models:** every example runs either on a local model served by [Ollama](https://ollama.com) (free, no API key) or on a hosted provider (OpenAI, Anthropic, Gemini, Groq…) with an API key. You switch between them by changing the `MODEL` line in `.env`.

> **API keys:** never commit real keys. Copy `.env.example` to `.env` (which is git-ignored) and replace the `REPLACE_ME` placeholders there.

## Author

Carles Trullàs — [@carlestrullas](https://github.com/carlestrullas)
