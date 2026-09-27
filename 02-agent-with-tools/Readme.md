# Lesson 2 — Tool Calling

This example demonstrates how to build a **Google ADK agent with custom Python tools** using **LiteLLM** and **OpenRouter**.

The examples show how an agent can decide when to call a Python function to perform an operation instead of generating the result itself.

## What Is a Tool?

A tool is a capability that an agent can invoke to perform an action or obtain information.

For example:

```text
Agent
  │
  ├── Calculator
  ├── Weather API
  ├── Database
  ├── Web search
  ├── Python function
  ├── Image model
  └── Company API
```

The important distinction is:

```text
LLM
  → Generates or reasons about text

Tool
  → Actually performs an operation
```

Suppose the user asks:

> What is 127 multiplied by 348?

The model can decide that a calculation tool is appropriate. Instead of the model having to perform the arithmetic itself, it can call a registered Python function.

For example:

```python
calculate(127, 348, "multiply")
```

The Python function performs the operation and returns the result to the agent.

---

## Why Is the Tool Docstring Important?

A tool's description helps the model understand what the tool does and when it should be used.

For example:

```python
def calculate(a, b, operation):
    """Perform a mathematical calculation on two numbers."""
```

A clear tool description makes it easier for the model to select the appropriate tool and provide the correct arguments.

In this project, the agent dynamically selects an available OpenRouter model through [`model_selector.py`](./model_selector.py) and gives that model access to Python functions registered as tools.

---

## Tool Examples

There are two tool-calling examples in the `02/` directory:

- [`tool_single.py`](./02/tool_single.py) — Demonstrates an agent with a single Python tool. The example asks the agent to add two numbers, and the model can call the tool to perform the calculation.

- [`tool_two_tools.py`](./02/tool_two_tools.py) — Demonstrates an agent with two Python tools. The example asks the agent to add two numbers using `tool_1` or multiply two numbers using `tool_2`. The model can select the appropriate tool for the requested operation.

---

## Project Structure

The expected project structure is:

```text
google-adk-agents/
├── .env
├── model_selector.py
└── 02/
    ├── tool_single.py
    └── tool_two_tools.py
```

### Files

| File | Purpose |
| --- | --- |
| `.env` | Stores the OpenRouter API key. |
| [`model_selector.py`](./model_selector.py) | Finds and selects an available model that supports the required capabilities. |
| [`02/tool_single.py`](./02/tool_single.py) | Creates an ADK agent and demonstrates single-tool calling. |
| [`02/tool_two_tools.py`](./02/tool_two_tools.py) | Creates an ADK agent and demonstrates calling two separate tools. |

---

## What This Example Demonstrates

This example combines several Google ADK concepts:

- Google ADK `Agent`
- `InMemoryRunner`
- LiteLLM
- OpenRouter
- Dynamic model selection
- Python function tools
- Function calling
- Asynchronous agent execution
- Environment variables
- Basic error handling

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
Model decides to call a tool
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

> **Security:** Never commit your `.env` file or expose your API key in source control.

---

# 2. Project Root Import

The example scripts are inside the `02/` directory, while `model_selector.py` is in the project root.

The structure is:

```text
google-adk-agents/
├── model_selector.py
└── 02/
    ├── tool_single.py
    └── tool_two_tools.py
```

Because of this structure, `tool_single.py` adds the project root to Python's import path:

```python
PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
```

This allows the script to import:

```python
from model_selector import select_model
```

The model-selection logic can therefore remain separate from the agent implementation.

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

The exact model depends on the models available to the selector at runtime.

---

# 4. Creating a Custom Tool

The main purpose of this example is to demonstrate how a Python function can be used as an agent tool.

The single-tool example defines:

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

The agent receives instructions similar to:

```text
You are a helpful assistant.
Answer briefly and clearly.
When the user asks you to add numbers, use the add_numbers tool.
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

The model does not need to implement the addition itself when it chooses to use the tool. The registered Python function performs the operation and returns the result.

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

Run the single-tool example from the project root:

```powershell
uv run .\02\tool_single.py
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

The exact model name and response wording can vary depending on the OpenRouter model selected at runtime.

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

For example, tools could later perform operations such as:

```text
Calculations
  ├── add_numbers()
  ├── calculate_tax()
  └── convert_currency()

Data
  ├── search_database()
  ├── get_user()
  └── fetch_records()

Applications
  ├── send_email()
  ├── create_file()
  └── call_api()
```

The current single-tool example keeps things simple by using:

```python
add_numbers()
```

The two-tool example extends the same idea by giving the agent two separate tools that it can select based on the user's request.

---

# 14. Model Requirements

Because this example uses ADK tools, the selected model needs to support tool calling.

The project's `model_selector.py` is responsible for finding models that meet the required conditions.

This is important because available models can support different capabilities.

The tool-calling architecture is therefore:

```text
OpenRouter Model Catalog
          │
          ▼
     Model Selector
          │
          ├── Available model
          │
          └── Tool-capable model
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

This keeps the console output focused on the important information produced by the example.

---

# 17. Key Concepts Learned

This example demonstrates the relationship between several components.

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
    │
    ▼
 LiteLlm
    │
    ▼
OpenRouter
    │
    ▼
Selected Model
```

### OpenRouter

Provides access to the model selected by `model_selector.py`.

### Python Tools

Provide functionality that the agent can call:

```python
add_numbers(a, b)
```

The two-tool example demonstrates the same concept with multiple registered functions.

### Model Selector

Keeps model discovery and selection separate from the agent implementation.

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

- Multiple tools
- Tools with optional parameters
- Tools that call external APIs
- File-based tools
- Database tools
- Web-search tools
- Multiple agents
- Agent-to-agent communication
- Tool error handling
- More advanced model-selection rules
- Tool execution logging

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
Selected Tool-Capable Model
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

The single-tool example provides a simple foundation for learning how Python tools and function calling work in Google ADK. The two-tool example builds on the same pattern by allowing the model to choose between multiple Python tools.
