# Agentic Systems

Hands-on projects on building **agentic systems**: applications in which one or more agents powered by large language models (LLMs) reason, plan and use tools to complete tasks autonomously.

The repository is organised **by framework**. Each folder contains self-contained examples, from a single agent with one tool to multi-agent workflows, with the code and the ideas behind it, so the same problems can be compared across different approaches.

## Frameworks and examples

| Framework | Example | Description |
|---|---|---|
| [CrewAI](crew_ai/) | [`researcher_agent`](crew_ai/researcher_agent/) | A research analyst agent that searches the web and writes a structured, sourced report on any topic. |

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
    └── researcher_agent/
        ├── researcher.py
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

> **API keys:** never commit real keys. Copy `.env.example` to `.env` (which is git-ignored) and replace the `REPLACE_ME` placeholders there.

## Author

Carles Trullas — [@carlestrullas](https://github.com/carlestrullas)
