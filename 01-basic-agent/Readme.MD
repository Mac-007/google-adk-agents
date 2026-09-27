# Basic Google ADK Agent with Dynamic OpenRouter Model Selection

Creates and runs a basic Google ADK agent using `LiteLlm`, OpenRouter, and `InMemoryRunner`.

The project also includes a separate model-selection module that dynamically discovers available OpenRouter models and selects a free model that supports tool calling.

---

## Project Structure

```text
google-adk-agents/
│
├── .env
│
├── model_selector.py
│
└── 02/
    └── basic_agent.py
```

### File Responsibilities

| File                | Responsibility                                    |
| ------------------- | ------------------------------------------------- |
| `.env`              | Stores the OpenRouter API key                     |
| `model_selector.py` | Discovers and selects a suitable OpenRouter model |
| `02/basic_agent.py` | Creates and runs the Google ADK agent             |

The important design principle is that **model selection is separated from agent logic**.

```text
basic_agent.py
      │
      │ select_model()
      ▼
model_selector.py
      │
      │ OpenRouter /models
      ▼
Available models
      │
      │ filter
      ▼
Free + tool-capable model
      │
      │ return model ID
      ▼
basic_agent.py
      │
      ▼
LiteLlm
      │
      ▼
OpenRouter
      │
      ▼
Selected model
```

---

# What the Code Does

The project:

* Loads the OpenRouter API key from `.env`
* Separates model selection from agent creation
* Queries OpenRouter for currently available models
* Finds free models
* Filters models that support tool calling
* Selects one suitable model dynamically
* Passes the selected model to LiteLLM
* Creates a Google ADK agent
* Runs the agent using `InMemoryRunner`
* Sends a prompt to the agent
* Processes the response events returned by ADK
* Prints only the generated text response
* Filters out thought/reasoning content
* Handles common authentication, rate-limit, and model errors

---

# 1. Environment Configuration

Create a `.env` file in the project root:

```text
API_KEY=your_openrouter_api_key
```

The project uses `load_dotenv()` to load this value into the environment.

The API key is then read using:

```python
API_KEY = os.getenv("API_KEY")
```

The value is also assigned to:

```python
os.environ["OPENROUTER_API_KEY"] = API_KEY
```

because LiteLLM expects the OpenRouter API key through the `OPENROUTER_API_KEY` environment variable.

The configuration flow is:

```text
.env
  │
  ▼
API_KEY
  │
  ▼
OPENROUTER_API_KEY
  │
  ▼
LiteLLM
  │
  ▼
OpenRouter
```

Keeping the API key in `.env` prevents the key from being hard-coded into the Python source code.

---

# 2. Dynamic Model Selection

The model-selection logic is located in:

```text
model_selector.py
```

The ADK agent does not directly specify a particular OpenRouter model.

Instead, `basic_agent.py` imports:

```python
from model_selector import select_model
```

and calls:

```python
MODEL_ID = select_model()
```

This keeps model selection separate from the agent implementation.

---

# 3. Get Available OpenRouter Models

`model_selector.py` queries the OpenRouter models endpoint:

```python
url = "https://openrouter.ai/api/v1/models"
```

The request uses the OpenRouter API key:

```python
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}
```

The response contains information about the models currently available through OpenRouter.

The basic flow is:

```text
model_selector.py
      │
      ▼
OpenRouter /api/v1/models
      │
      ▼
Model catalog
      │
      ▼
Python list of models
```

---

# 4. Find Free Models

The model selector examines the pricing information for every model.

A model is considered free when both its prompt and completion prices are zero:

```python
is_free = (
    prompt_price == "0"
    and completion_price == "0"
)
```

This prevents the agent from automatically selecting a paid model.

The selector therefore looks for:

```text
Prompt price = 0
Completion price = 0
```

---

# 5. Find Models That Support Tools

Not every model supports tool calling.

The selector checks the model's:

```python
supported_parameters
```

and looks for:

```python
"tools"
```

The check is:

```python
supports_tools = (
    "tools" in supported_parameters
)
```

A model is selected only when both conditions are satisfied:

```text
Free
 +
Supports tools
 =
Candidate model
```

The filtering logic is therefore:

```python
if is_free and supports_tools:
    free_tool_models.append(model)
```

This is important because the agent will eventually provide tools to the model.

---

# 6. Select a Model

After filtering the available models, the selector checks whether at least one suitable model exists:

```python
if not models:
    raise RuntimeError(
        "No free model with tool-calling support "
        "is currently available on OpenRouter."
    )
```

If suitable models are available, the current implementation selects the first matching model:

```python
selected_model = models[0]
```

The model ID is then returned:

```python
return model_id
```

For example, the returned value could look like:

```text
inclusionai/ling-3.0-flash-fin:free
```

The important point is that the model ID is **discovered dynamically**, rather than being hard-coded into the agent.

---

# 7. Why Model Selection Is Separate

The model selector is intentionally kept separate from the ADK agent.

Without separation, the agent might contain something like:

```python
model=LiteLlm(
    model="openrouter/some-model:free"
)
```

This means changing the model requires editing the agent code.

With the new design:

```python
MODEL_ID = select_model()

agent = Agent(
    ...
    model=LiteLlm(
        model=f"openrouter/{MODEL_ID}"
    ),
)
```

The agent does not need to know how the model was selected.

This gives the project a cleaner separation of responsibilities:

```text
model_selector.py
    │
    └── Which model should I use?

basic_agent.py
    │
    └── How should my ADK agent work?
```

---

# 8. Import the Model Selector

Because `basic_agent.py` is inside the `02` directory while `model_selector.py` is in the project root, the project root is added to Python's import path.

The structure is:

```text
google-adk-agents/
│
├── model_selector.py
│
└── 02/
    └── basic_agent.py
```

`basic_agent.py` determines the project root:

```python
PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)
```

Then it adds the root to `sys.path`:

```python
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
```

Now this import works:

```python
from model_selector import select_model
```

---

# 9. Configure LiteLLM

After the model selector returns a model ID:

```python
MODEL_ID = select_model()
```

the model is passed to LiteLLM:

```python
model=LiteLlm(
    model=f"openrouter/{MODEL_ID}"
)
```

For example, if the selector returns:

```text
inclusionai/ling-3.0-flash-fin:free
```

LiteLLM receives:

```text
openrouter/inclusionai/ling-3.0-flash-fin:free
```

The model access flow is:

```text
Google ADK
    │
    ▼
LiteLlm
    │
    ▼
OpenRouter
    │
    ▼
Selected free model
```

---

# 10. Create the Google ADK Agent

The agent is created using:

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

There are three important pieces here.

## Agent Name

```python
name="test_agent"
```

This gives the agent its name.

---

## Model

```python
model=LiteLlm(
    model=f"openrouter/{MODEL_ID}"
)
```

The model ID comes from `model_selector.py`.

The agent therefore does not need to know which particular free model is currently available.

---

## Instruction

```python
instruction=(
    "You are a helpful assistant. "
    "Answer briefly and clearly."
)
```

The instruction defines how the agent should behave.

The instruction is different from the user's request.

```text
Agent instruction
      │
      ▼
How the agent should behave

User request
      │
      ▼
What the agent should do
```

---

# 11. Create an In-Memory Runner

The agent is passed to an `InMemoryRunner`:

```python
runner = InMemoryRunner(
    agent=agent
)
```

The runner is responsible for executing the agent.

For this learning project, `InMemoryRunner` is useful because the application does not require an external database for session information.

The relationship is:

```text
Agent
  │
  ▼
InMemoryRunner
  │
  ▼
Agent execution
```

---

# 12. Run the Agent

The agent is executed using:

```python
events = await runner.run_debug(
    "Say hello and tell me that you are working."
)
```

The request is passed to the agent.

`run_debug()` returns events generated during execution.

The flow is:

```text
User request
      │
      ▼
run_debug()
      │
      ▼
ADK Agent
      │
      ▼
Selected OpenRouter model
      │
      ▼
Events
```

---

# 13. Process ADK Events

The returned events are processed using:

```python
for event in events:
```

Not every event necessarily contains displayable content, so the code checks:

```python
if not event.content:
    continue
```

Then it examines the content parts:

```python
for part in event.content.parts:
```

The structure is:

```text
events
  │
  ▼
event
  │
  ▼
event.content
  │
  ▼
event.content.parts
  │
  ▼
part
```

---

# 14. Print Only Normal Text

The code checks:

```python
if part.text and not part.thought:
    print(part.text)
```

This means the program:

1. Checks that the part contains text.
2. Checks that it is not marked as a thought.
3. Prints the text.

This keeps the terminal output focused on the response intended for the user.

---

# 15. Error Handling

The program catches exceptions:

```python
try:
    ...
except Exception as error:
    ...
```

The error is converted into a string:

```python
error_message = str(error)
```

The code then checks several common cases.

## Rate Limiting

```python
if (
    "429" in error_message
    or "rate-limited" in error_message.lower()
):
```

The program reports that the model is temporarily rate-limited.

---

## Authentication

The code checks:

```python
"401"
"403"
```

These are treated as authentication or permission-related problems.

The user is instructed to check the OpenRouter API key.

---

## Model Not Found

The code checks:

```python
"404"
```

If found, it reports:

```text
Model not found.
Please check the OpenRouter model name.
```

Because the model is now selected dynamically, a 404 may indicate that the selected model is no longer available or that the provider endpoint has changed.

---

# 16. Start the Program

The program starts with:

```python
if __name__ == "__main__":
    asyncio.run(main())
```

This executes the asynchronous `main()` function.

The complete execution flow is now:

```text
Start program
      │
      ▼
Load .env
      │
      ▼
Read API key
      │
      ▼
Configure OPENROUTER_API_KEY
      │
      ▼
Import model_selector
      │
      ▼
Query OpenRouter models
      │
      ▼
Filter free models
      │
      ▼
Filter tool-capable models
      │
      ▼
Select model
      │
      ▼
Create LiteLlm
      │
      ▼
Create ADK Agent
      │
      ▼
Create InMemoryRunner
      │
      ▼
Run agent
      │
      ▼
Receive events
      │
      ▼
Process event content
      │
      ▼
Print text response
```

---

# 17. Running the Project

From the project root:

```powershell
uv run .\02\basic_agent.py
```

The model selector will first query OpenRouter and select a suitable model.

You should see output similar to:

```text
[MODEL SELECTOR] Selected model: inclusionai/ling-3.0-flash-fin:free

[MAIN] Model selected: inclusionai/ling-3.0-flash-fin:free

Agent response:
----------------------------------------
Hello! I am working.
----------------------------------------
```

The exact model selected can change because the selector uses the models currently returned by OpenRouter.

---

# 18. Installing Dependencies

If the project does not already have the required packages, install them using `uv`.

For example:

```powershell
uv add google-adk
uv add litellm
uv add python-dotenv
uv add requests
```

The `requests` package is used by `model_selector.py` to query the OpenRouter models API.

---

# 19. Complete Architecture

The project now separates the application into two main layers.

```text
                 ┌─────────────────────┐
                 │      .env            │
                 │                     │
                 │ API_KEY=...         │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │ model_selector.py   │
                 │                     │
                 │ Get models           │
                 │ Filter free          │
                 │ Filter tools         │
                 │ Select model         │
                 └──────────┬──────────┘
                            │
                            │ model ID
                            ▼
                 ┌─────────────────────┐
                 │  basic_agent.py     │
                 │                     │
                 │ Create LiteLlm      │
                 │ Create ADK Agent    │
                 │ Create Runner       │
                 │ Run Agent           │
                 └──────────┬──────────┘
                            │
                            ▼
                     ┌─────────────┐
                     │  LiteLLM    │
                     └──────┬──────┘
                            │
                            ▼
                     ┌─────────────┐
                     │ OpenRouter  │
                     └──────┬──────┘
                            │
                            ▼
                   Selected Free Model
```

---

# 20. Why This Architecture Is Useful

The main benefit is that **model selection and agent behavior are independent**.

If you want to change how models are selected, modify:

```text
model_selector.py
```

If you want to change the agent's behavior, modify:

```text
02/basic_agent.py
```

For example, later the selector could be extended to consider:

```text
Free
  +
Tool calling
  +
Context length
  +
Vision support
  +
Provider
  +
Model preference
```

without changing the ADK agent.

The architecture can therefore evolve from:

```text
Simple Agent
```

into:

```text
Model Selector
      │
      ▼
ADK Agent
      │
      ▼
Tools
```

while keeping the individual responsibilities separate.

---

# Summary

This project demonstrates a basic Google ADK agent using OpenRouter through LiteLLM, while keeping model selection separate from the agent implementation.

The main learning points are:

1. Store API credentials in `.env`.
2. Load environment variables with `load_dotenv()`.
3. Configure `OPENROUTER_API_KEY` for LiteLLM.
4. Use a separate module to discover available models.
5. Filter for free models.
6. Filter for models supporting tool calling.
7. Dynamically select a model.
8. Pass the selected model to `LiteLlm`.
9. Create an ADK `Agent`.
10. Execute it with `InMemoryRunner`.
11. Process the events returned by ADK.
12. Print only normal text responses.
13. Keep model-selection logic independent from agent logic.

The resulting structure is:

```text
model_selector.py
       │
       │ selects model
       ▼
basic_agent.py
       │
       │ creates agent
       ▼
LiteLlm
       │
       ▼
OpenRouter
       │
       ▼
Selected free model
```