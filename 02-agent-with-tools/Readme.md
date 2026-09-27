# Google ADK Agent with Tool Calling

This example demonstrates how to build a **Google ADK agent with a custom Python tool**, using **LiteLLM** and **OpenRouter**.

The agent dynamically selects an available OpenRouter model through `model_selector.py` and gives that model access to a Python function called `add_numbers`.

The example asks the agent to add two numbers, and the model can call the Python tool to perform the calculation.

---

## Project Structure

The expected project structure is:

```text
google-adk-agents/
├── .env
├── model_selector.py
└── 02/
    └── tool.py
```

### Files

| File                | Purpose                                                       |
| ------------------- | ------------------------------------------------------------- |
| `.env`              | Stores the OpenRouter API key                                 |
| `model_selector.py` | Finds and selects an available free model that supports tools |
| `02/tool.py`        | Creates the ADK agent and demonstrates tool calling           |

---

## What This Example Demonstrates

This example combines several Google ADK concepts:

* Google ADK `Agent`
* `InMemoryRunner`
* LiteLLM
* OpenRouter
* Dynamic model selection
* Python function tools
* Function calling
* Async agent execution
* Environment variables
* Basic error handling

The overall flow is:

```text
User Prompt
     │
     ▼
Google ADK Agent
     │
     ▼
Selected OpenRouter Model
     │
     ▼
Model decides to call tool
     │
     ▼
add_numbers(25, 17)
     │
     ▼
42
     │
     ▼
Agent Response
```

---

# 1. Environment Configuration

The application loads environment variables using `python-dotenv`:

```python
from dotenv import load_dotenv

load_dotenv()
```

It then reads the API key:

```python
API_KEY = os.getenv("API_KEY")
```

If the API key is not available, the program raises an error:

```python
if not API_KEY:
    raise RuntimeError(
        "API_KEY is missing. "
        "Please add your OpenRouter API key to the .env file."
    )
```

Create a `.env` file in the project root:

```env
API_KEY=your_openrouter_api_key_here
```

The API key is then provided to LiteLLM through:

```python
os.environ["OPENROUTER_API_KEY"] = API_KEY
```

> Do not commit your `.env` file or expose your API key in source control.

---

# 2. Project Root Import

The `tool.py` file is inside the `02/` directory, while `model_selector.py` is in the project root.

The structure is:

```text
google-adk-agents/
├── model_selector.py
└── 02/
    └── tool.py
```

Because of this structure, `tool.py` adds the project root to Python's import path:

```python
PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
```

This allows the following import:

```python
from model_selector import select_model
```

The model-selection logic therefore remains separate from the agent implementation.

---

# 3. Dynamic Model Selection

The agent does not hard-code a specific OpenRouter model.

Instead, it imports:

```python
from model_selector import select_model
```

and calls:

```python
model_id = select_model()
```

The selected model is then displayed:

```python
print(
    f"[AGENT] Using model: {model_id}"
)
```

The model is passed to LiteLLM using:

```python
model=LiteLlm(
    model=f"openrouter/{model_id}"
)
```

This allows the agent to use a model selected dynamically by `model_selector.py`.

The exact model depends on the models currently available to the selector.

---

# 4. Creating a Custom Tool

The main purpose of this example is to demonstrate a Python function being used as an agent tool.

The tool is:

```python
def add_numbers(a: int, b: int) -> int:
    """
    Add two numbers and return the result.
    """

    result = a + b

    print(
        f"\n[TOOL CALLED] add_numbers({a}, {b}) = {result}"
    )

    return result
```

The function:

1. Accepts two integers.
2. Adds them together.
3. Prints a message showing that the tool was called.
4. Returns the result.

For example:

```python
add_numbers(25, 17)
```

returns:

```text
42
```

The print statement also produces:

```text
[TOOL CALLED] add_numbers(25, 17) = 42
```

---

# 5. Creating the ADK Agent

The agent is created inside:

```python
def create_agent():
```

First, the model selector is called:

```python
model_id = select_model()
```

Then the Google ADK agent is created:

```python
agent = Agent(
    name="test_agent",

    model=LiteLlm(
        model=f"openrouter/{model_id}"
    ),

    instruction=(
        "You are a helpful assistant. "
        "Answer briefly and clearly. "
        "When the user asks you to add numbers, "
        "use the add_numbers tool."
    ),

    tools=[
        add_numbers
    ],
)
```

There are three important parts here.

### Agent Name

```python
name="test_agent"
```

This gives the ADK agent its name.

### Model

```python
model=LiteLlm(
    model=f"openrouter/{model_id}"
)
```

The selected OpenRouter model is connected to ADK through LiteLLM.

### Tools

```python
tools=[
    add_numbers
]
```

This makes the Python function available to the agent.

The agent can therefore decide to call `add_numbers` when the user's request requires addition.

---

# 6. Agent Instructions

The agent receives the following instruction:

```text
You are a helpful assistant.
Answer briefly and clearly.
When the user asks you to add numbers,
use the add_numbers tool.
```

The important instruction for this example is:

```text
When the user asks you to add numbers, use the add_numbers tool.
```

This tells the model that addition requests should be handled using the registered Python function.

---

# 7. Registering the Tool

The tool is registered with the agent using:

```python
tools=[
    add_numbers
]
```

This is the key connection between the Python function and the ADK agent.

Conceptually:

```text
Python Function
      │
      ▼
add_numbers()
      │
      ▼
ADK Agent
      │
      ▼
Model can call the function
```

The model does not need to implement the addition itself when it chooses to use the tool.

---

# 8. Running the Agent

The example uses:

```python
InMemoryRunner
```

The runner is created with:

```python
runner = InMemoryRunner(
    agent=agent
)
```

The agent is then executed asynchronously:

```python
events = await runner.run_debug(
    "Please add 25 and 17 using the add_numbers tool."
)
```

The prompt explicitly asks the agent to use the tool.

---

# 9. Processing Agent Events

The program processes the returned events:

```python
for event in events:

    if not event.content:
        continue

    for part in event.content.parts:

        if part.text and not part.thought:
            print(part.text)
```

This does the following:

1. Iterates through the events generated by the runner.
2. Ignores events without content.
3. Iterates through the content parts.
4. Prints text responses.
5. Skips parts marked as thoughts.

The output therefore focuses on the agent's visible response.

---

# 10. Example Execution

Run the example from the project root:

```powershell
uv run .\02\tool.py
```

The application first selects a model:

```text
[AGENT] Using model: provider/model-name:free
```

When the agent calls the tool, you should see something similar to:

```text
[TOOL CALLED] add_numbers(25, 17) = 42
```

The agent then produces its response.

The exact model name and wording of the response can vary depending on the OpenRouter model selected at runtime.

---

# 11. Installing Dependencies

If the project uses `uv`, install the required dependencies with:

```bash
uv add google-adk litellm python-dotenv requests
```

Or, if the dependencies are already defined in the project:

```bash
uv sync
```

The `requests` package is used by `model_selector.py` to query the OpenRouter model catalog.

---

# 12. Complete Execution Flow

The complete execution flow is:

```text
Start
  │
  ▼
Load .env
  │
  ▼
Read API_KEY
  │
  ▼
Configure OPENROUTER_API_KEY
  │
  ▼
create_agent()
  │
  ▼
select_model()
  │
  ▼
Select OpenRouter model
  │
  ▼
Create LiteLLM model
  │
  ▼
Create Google ADK Agent
  │
  ├── Instructions
  │
  └── add_numbers tool
  │
  ▼
Create InMemoryRunner
  │
  ▼
run_debug()
  │
  ▼
"Please add 25 and 17 using the add_numbers tool."
  │
  ▼
Model requests add_numbers()
  │
  ▼
add_numbers(25, 17)
  │
  ▼
42
  │
  ▼
Agent response
```

---

# 13. Why Tool Calling Is Useful

A model can generate text, but tools allow an agent to interact with external Python functionality.

For example, a tool could later perform:

```text
Calculations
     │
     ├── add_numbers()
     ├── calculate_tax()
     └── convert_currency()

Data
     │
     ├── search_database()
     ├── get_user()
     └── fetch_records()

Applications
     │
     ├── send_email()
     ├── create_file()
     └── call_api()
```

The current example keeps things simple by using only:

```python
add_numbers()
```

---

# 14. Model Requirements

Because this example uses an ADK tool, the selected model needs to support tool calling.

The project's `model_selector.py` is responsible for finding models that meet the required conditions.

This is important because not every available model necessarily supports the same capabilities.

The tool-calling example therefore follows this architecture:

```text
OpenRouter Model Catalog
          │
          ▼
   Model Selector
          │
          ├── Free
          │
          └── Tool-capable
          │
          ▼
    Selected Model
          │
          ▼
       LiteLLM
          │
          ▼
      Google ADK
          │
          ▼
       Tool Call
```

---

# 15. Error Handling

The main execution is wrapped in a `try`/`except` block:

```python
try:
    ...
except Exception as error:
    print("\nSomething went wrong:")
    print(error)
```

If an exception occurs while selecting the model, creating the agent, calling the model, or processing the response, the error is displayed instead of silently failing.

---

# 16. LiteLLM Debug Output

The example disables additional LiteLLM debug information:

```python
litellm.suppress_debug_info = True
```

This keeps the console output focused on the example's important information.

---

# 17. Key Concepts Learned

This example demonstrates the relationship between several components:

### Google ADK

Responsible for:

```text
Agent
Runner
Tools
Events
```

### LiteLLM

Provides the model interface:

```text
Google ADK
    ↓
LiteLlm
    ↓
OpenRouter
    ↓
Selected Model
```

### OpenRouter

Provides access to the model selected by `model_selector.py`.

### Python Tool

Provides functionality that the agent can call:

```python
add_numbers(a, b)
```

### Model Selector

Keeps model discovery and selection separate from the agent code.

---

# 18. Next Possible Experiments

This example can be extended by adding more tools.

For example:

```python
def multiply_numbers(a: int, b: int) -> int:
    return a * b
```

Then both functions could be registered:

```python
tools=[
    add_numbers,
    multiply_numbers,
]
```

Other possible experiments include:

* Multiple tools
* Tools with optional parameters
* Tools that call external APIs
* File-based tools
* Database tools
* Web-search tools
* Multiple agents
* Agent-to-agent communication
* Tool error handling
* More advanced model-selection rules
* Tool execution logging

---

# Summary

This example demonstrates a basic **Google ADK agent with Python tool calling**.

The architecture is:

```text
.env
 │
 ▼
API Key
 │
 ▼
model_selector.py
 │
 ▼
Free + Tool-Capable Model
 │
 ▼
LiteLLM
 │
 ▼
Google ADK Agent
 │
 ├── Instructions
 │
 └── add_numbers()
       │
       ▼
     25 + 17
       │
       ▼
       42
```

The main idea is that the **agent decides when to use a registered Python function**, while the actual operation is performed by Python.

In this example:

```text
User
  │
  ▼
"Please add 25 and 17"
  │
  ▼
ADK Agent
  │
  ▼
add_numbers(25, 17)
  │
  ▼
42
```

This provides a simple foundation for learning how tools and function calling work in Google ADK.
