# Google ADK Based Agent Exploration

A collection of experiments and implementations exploring **Google Agent Development Kit (ADK)** and agent-based application development.

The current project includes a basic Google ADK agent that uses **LiteLLM + OpenRouter** and dynamically selects an available **free OpenRouter model that supports tool calling**, instead of hard-coding a specific model.

## Key Components
The main building blocks include:
- Agent — an intelligent worker, typically an LlmAgent.
- Tools — functions, APIs, search, databases, external services, etc.
- Workflow agents — deterministic orchestration such as sequential, parallel, and loop execution.
- Multi-agent systems — agents can delegate work to other specialized agents.
- Sessions/state/context — maintain information across agent execution.
- Callbacks — intercept and customize agent/tool execution.
- Evaluation & tracing — inspect and evaluate agent behavior.
- Deployment — including containerized deployment and Google Cloud options.

## Current Setup

- Python
- Google ADK
- LiteLLM
- OpenRouter
- `uv` for dependency and environment management
- `python-dotenv` for environment configuration
- `requests` for querying the OpenRouter model catalog
- Google ADK tools / function calling

## Project Structure

```text
google-adk-agents/
├── .env
├── model_selector.py
└── 02/
    └── basic_agent.py
```

### File Responsibilities

#### `.env`

Stores the OpenRouter API key locally.

#### `model_selector.py`

Responsible for discovering and selecting a suitable OpenRouter model.

It:

1. Calls the OpenRouter models API.
2. Reads the available model metadata.
3. Filters for models with zero prompt and completion pricing.
4. Filters for models that support the `tools` parameter.
5. Selects a concrete model ID from the matching models.

This keeps model-selection logic separate from the Google ADK agent implementation.

#### `02/basic_agent.py`

Contains the Google ADK agent implementation.

The agent:

1. Loads the environment configuration.
2. Calls `select_model()` from `model_selector.py`.
3. Builds the LiteLLM model name using the selected OpenRouter model.
4. Creates a Google ADK `Agent`.
5. Runs the agent using `InMemoryRunner`.
6. Processes and prints the generated response.

---

## Configuration

Create a `.env` file in the project root:

```env
API_KEY=your_openrouter_api_key_here
```

The application reads this value and uses it for OpenRouter requests.

> **Important:** Do not commit your `.env` file or expose your API key in source control.

---

## Setup

Install the project dependencies with:

```bash
uv sync
```

Or add the required packages individually:

```bash
uv add google-adk litellm python-dotenv requests
```

---

## Dynamic Model Selection

Instead of manually choosing a model such as:

```python
model="openrouter/some-model:free"
```

the project uses:

```python
from model_selector import select_model

MODEL_ID = select_model()
```

The selected model is then passed to LiteLLM:

```python
model=LiteLlm(
    model=f"openrouter/{MODEL_ID}"
)
```

### How the selector works

`model_selector.py` queries:

```text
https://openrouter.ai/api/v1/models
```

It then looks for models where:

```text
prompt price      == 0
completion price  == 0
```

and where:

```text
"tools" in supported_parameters
```

Only models satisfying these conditions are considered.

The selector returns the concrete OpenRouter model ID, for example:

```text
some-provider/some-model:free
```

The exact model selected can change because the OpenRouter model catalog and model availability can change over time.

### Why use model selection?

This avoids tying the agent implementation to one specific free model.

For example, if one free model becomes unavailable or reaches a provider resource limit, another currently available model can be selected from the OpenRouter catalog.

The model-selection logic is intentionally kept outside the ADK agent code so that the agent remains focused on agent behavior.

---

## Run

Run the current basic agent from the project root:

```powershell
uv run .\02\basic_agent.py
```

The application will first select a suitable free tool-capable model and then start the Google ADK agent.

You should see output similar to:

```text
[MODEL SELECTOR] Selected model: provider/model-name:free

[MAIN] Model selected: provider/model-name:free
```

The exact model name depends on the models currently returned by OpenRouter.

---

## Agent

The current implementation uses Google ADK's `Agent` with LiteLLM.

Conceptually, the model configuration is:

```python
agent = Agent(
    name="test_agent",
    model=LiteLlm(
        model=f"openrouter/{MODEL_ID}"
    ),
    instruction=(
        "You are a helpful assistant. "
        "Answer briefly and clearly."
    ),
)
```

The important part is that `MODEL_ID` is obtained dynamically:

```python
MODEL_ID = select_model()
```

rather than being hard-coded.

---

## Tools and Function Calling

Google ADK supports tools that allow an agent to call Python functions.

A simple example is:

```python
def add_numbers(a: int, b: int) -> int:
    """Add two numbers and return the result."""
    return a + b
```

The function can be supplied to the ADK agent as a tool:

```python
tools=[add_numbers]
```

A suitable model must support tool calling for this workflow to work correctly.

This is why `model_selector.py` checks:

```python
"tools" in supported_parameters
```

when selecting free models.

---

## Running the Model Selector Directly

You can also run the selector by itself to inspect the available free tool-capable models:

```powershell
uv run .\model_selector.py
```

It prints the models discovered from OpenRouter and then shows the model selected by the selector.

This is useful for understanding which free models are currently available before running the ADK agent.

---

## Importing the Model Selector from `02/`

Because `model_selector.py` is located in the project root while `basic_agent.py` is inside the `02/` directory, the agent makes the project root available to Python before importing the selector.

The important structure is:

```text
google-adk-agents/
├── model_selector.py
└── 02/
    └── basic_agent.py
```

The agent can then use:

```python
from model_selector import select_model
```

when executed from the project root.

---

## Agent Runner

The agent is executed with Google ADK's `InMemoryRunner`:

```python
runner = InMemoryRunner(agent=agent)
```

The application then runs the agent asynchronously:

```python
events = await runner.run_debug(
    "Say hello and tell me that you are working."
)
```

The returned events are processed to display the generated text while avoiding internal thought content.

---

## Error Handling

The agent includes handling for common API and model-related failures.

### Rate limits / resource limits

A model provider may temporarily reject requests because of rate limits or resource constraints.

For example, a free provider can report that its available worker capacity has been exhausted.

This is generally a provider/model availability issue rather than a problem with the Python tool implementation.

Because model selection is dynamic, the project can select another matching model on a subsequent run when one is available.

### Authentication errors

HTTP `401` or `403` responses generally indicate an API-key or authorization problem.

Check:

```env
API_KEY=your_openrouter_api_key_here
```

and make sure the key is valid.

### Model not found

A `404` or similar model error can occur if a model ID is no longer available.

The selector avoids hard-coding a specific model ID and instead discovers models from the current OpenRouter catalog.

### Other errors

Unexpected exceptions are displayed so that development and debugging can continue without silently hiding the failure.

---

## Important Notes About Free Models

Free model availability is dynamic.

A model can:

- Become temporarily unavailable.
- Reach provider-specific resource limits.
- Change its supported capabilities.
- Be removed or replaced.
- Have different availability from one run to another.

Therefore, this project does **not** assume that one particular free model will always work.

The selector uses the OpenRouter model metadata available at runtime.

---

## Why Not `openrouter/free`?

The project does not directly configure LiteLLM with:

```text
openrouter/free
```

Instead, it first queries OpenRouter's model catalog and selects a concrete model ID.

This is useful because the ADK/LiteLLM configuration can then receive an explicit model identifier such as:

```text
openrouter/provider/model:free
```

rather than relying on a generic free-model alias.

---

## Areas of Exploration

This repository may include experiments around:

- ADK agents
- Dynamic model selection
- OpenRouter model integrations
- LiteLLM
- Agent runners
- Sessions and state
- Tools and function calling
- Multi-agent workflows
- Agent orchestration
- Streaming responses
- Environment configuration
- Agent-based application patterns

---

## Development Approach

The repository is organized incrementally.

Each numbered directory can contain a focused experiment that explores a particular Google ADK capability.

The current `02/` example focuses on:

```text
Google ADK
    ↓
LiteLLM
    ↓
OpenRouter
    ↓
Dynamic free + tool-capable model selection
```

The separation between model discovery and agent implementation also makes it easier to expand the project later with:

- Model fallback strategies
- Model capability filtering
- Model ranking or selection rules
- Additional ADK tools
- More advanced agent workflows
- Multiple agents

---

## Summary

The current implementation demonstrates a basic Google ADK agent with dynamic OpenRouter model selection.

The main flow is:

```text
.env
  │
  ▼
API_KEY
  │
  ▼
model_selector.py
  │
  ├── Query OpenRouter models
  ├── Find free models
  ├── Check tool support
  └── Select a model
  │
  ▼
02/basic_agent.py
  │
  ├── Create LiteLLM model
  ├── Create ADK Agent
  ├── Create InMemoryRunner
  └── Run the agent
  │
  ▼
Agent Response
```

This keeps the project simple while providing a foundation for experimenting with Google ADK, tools, LiteLLM, OpenRouter, and dynamic model selection.

---

## Author / Contact

- **Author**: `Dr. Amit Chougule, PhD`
- **Email**: [amitchougule121@gmail.com](mailto:amitchougule121@gmail.com)
