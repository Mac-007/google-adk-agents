# Lesson 4 — Tool Schemas, Parameters, Return Values, and Errors

This lesson explains how an agent understands a tool and how Python functions become usable capabilities for an ADK agent.

The key idea is:

> **The LLM decides. Python executes.**

A Python function may look ordinary to a developer, but an agent effectively sees a structured tool with a name, description, inputs, and output.

---

## 1. How an Agent Understands a Tool

Consider a simple function:

```python
def get_temperature(city: str) -> str:
    """Returns the current temperature for a given city."""
```

A Python developer sees a normal function.

The agent effectively sees something closer to:

```text
Tool: get_temperature

Description:
    Returns the current temperature for a given city.

Input:
    city: string

Output:
    string
```

This is the **tool schema**.

The function's name, type hints, return type, and docstring all help describe the capability to the agent.

---

## 2. Why the Function Signature Matters

Consider:

```python
def get_temperature(city: str) -> str:
```

There are three important pieces:

```text
get_temperature
       │
       ├── city: str
       │
       └── → str
```

### Function name

```python
get_temperature
```

The function name tells the model what capability is available.

### Parameter

```python
city: str
```

The parameter tells the model that the tool needs a city and that the expected value is text.

### Return type

```python
-> str
```

The return type describes the kind of result produced by the tool.

Type hints are therefore useful beyond IDE support—they help describe the interface of the tool.

---

# 3. Multiple Parameters

A tool can accept multiple parameters.

For example:

```python
def calculate(
    a: float,
    b: float,
    operation: str
) -> float:
    """
    Performs a mathematical operation on two numbers.

    Args:
        a: First number.
        b: Second number.
        operation: Operation to perform.
            Supported operations are add,
            subtract, multiply, and divide.
    """
```

The conceptual schema is:

```text
calculate
│
├── a          float
├── b          float
└── operation  string
       │
       ↓
     float
```

The LLM can construct values such as:

```text
a = 10
b = 5
operation = "multiply"
```

and invoke the tool.

---

# 4. Tool Selection Is Separate from Tool Execution

This is an important concept.

Suppose the agent has:

```python
tools=[
    get_temperature,
    calculate,
]
```

If the user asks:

> What is 25 × 4?

the model needs to determine which tool is appropriate:

```text
Which tool?

get_temperature ❌
calculate       ✅
```

It can then construct an invocation conceptually equivalent to:

```python
calculate(
    a=25,
    b=4,
    operation="multiply"
)
```

The Python function executes and returns the result.

The overall flow is:

```text
          LLM
           │
           │ decides
           ↓
      Tool selection
           │
           ↓
      Tool invocation
           │
           ↓
      Python function
           │
           ↓
         Result
```

### Remember

**The LLM decides. Python executes.**

The model determines which capability is needed and what parameters should be supplied. The Python function performs the actual operation.

This distinction becomes especially important when thinking about security and production agents.

---

# 5. What Happens When a Tool Fails?

A tool can fail during execution.

For example:

```python
def divide(a: float, b: float) -> float:
    """Divides a by b."""
    return a / b
```

If the user asks:

> Divide 10 by 0.

Python produces a:

```text
ZeroDivisionError
```

A production agent should handle meaningful tool failures instead of allowing the operation to fail without context.

For example:

```python
def divide(a: float, b: float) -> float:
    """Divides a by b."""

    if b == 0:
        raise ValueError("Cannot divide by zero.")

    return a / b
```

Now the tool communicates a clear failure:

```text
Cannot divide by zero.
```

The generated example also validates unsupported calculator operations and raises a `ValueError` when an invalid operation is supplied.

---

# 6. Tool Design Principle

A useful design principle from this lesson is:

> **One tool should ideally represent one clear capability.**

### Avoid overly broad tools

A tool such as:

```python
def do_everything(
    user_request,
    database,
    api,
    files,
    calculation,
):
    ...
```

represents too many unrelated capabilities in one interface.

### Prefer smaller capabilities

For example:

```text
search_database()
get_customer()
calculate_revenue()
send_email()
generate_report()
```

This gives the agent smaller and clearer capabilities.

Conceptually:

```text
                    Agent
                      │
          ┌───────────┼────────────┐
          ↓           ↓            ↓
  search_database  calculate  generate_report
```

Clear tools make it easier for the agent to determine which capability is appropriate for a request.

---

# 7. First Realistic Mini-Agent

The lesson combines the concepts into a small ADK agent with multiple tools.

The first tool provides temperature information:

```python
def get_temperature(city: str) -> str:
    """
    Returns the temperature for a city.

    Args:
        city: Name of the city.
    """

    temperatures = {
        "Mumbai": "31°C",
        "Delhi": "34°C",
        "Pune": "28°C",
        "Kolhapur": "27°C",
    }

    return temperatures.get(
        city,
        "Temperature unavailable."
    )
```

The second tool performs calculations:

```python
def calculate(
    a: float,
    b: float,
    operation: str
) -> float:
    """
    Performs a mathematical operation on two numbers.

    Args:
        a: First number.
        b: Second number.
        operation: add, subtract, multiply, or divide.
    """

    if operation == "add":
        return a + b

    if operation == "subtract":
        return a - b

    if operation == "multiply":
        return a * b

    if operation == "divide":
        if b == 0:
            raise ValueError("Cannot divide by zero.")

        return a / b

    raise ValueError(
        f"Unsupported operation: {operation}"
    )
```

The agent exposes both capabilities through its `tools` parameter.

The generated code additionally includes the exercise tool from the lesson:

```python
def get_research_area(topic: str) -> str:
    """
    Return the main research area associated with a topic.
    """
```

It supports:

```text
computer vision       → Computer Vision
large language models → NLP / Generative AI
reinforcement learning → Reinforcement Learning
medical imaging       → Medical AI
```

The resulting agent has three clear capabilities:

```text
                    Agent
                      │
        ┌─────────────┼───────────────┐
        ↓             ↓               ↓
   Temperature     Calculator    Research Area
```

---

# 8. Testing Tool Selection

The lesson uses several examples to demonstrate how the agent selects tools.

## Query 1 — Temperature

User:

> What's the temperature in Pune?

The agent should select:

```text
get_temperature
```

with:

```python
city="Pune"
```

The example data returns:

```text
28°C
```

---

## Query 2 — Calculation

User:

> Calculate 25 × 8.

The agent should select:

```text
calculate
```

with values equivalent to:

```python
a=25
b=8
operation="multiply"
```

The calculation returns:

```text
200
```

---

## Query 3 — Multiple Tools

User:

> What's the temperature in Pune and calculate 25 × 8?

The agent may need two tool calls:

```text
             User
              │
              ↓
            Agent
            /    \
           ↓      ↓
  temperature    calculate
           ↓      ↓
         28°C    200
           \      /
            ↓    ↓
             Agent
               ↓
             Answer
```

This is the beginning of **agentic orchestration**.

The agent is no longer limited to selecting one capability. It can determine that different parts of a request require different tools.

---

# 9. The Temperature Example Is Fake Data

The temperature tool in this lesson uses a fixed dictionary:

```python
temperatures = {
    "Mumbai": "31°C",
    "Delhi": "34°C",
    "Pune": "28°C",
    "Kolhapur": "27°C",
}
```

This is demonstration data, not a live weather service.

A real agent could replace the implementation with a weather API:

```text
Agent
  ↓
get_temperature()
  ↓
Weather API
  ↓
JSON
  ↓
Agent
```

The agent does not need to understand all of the API implementation details.

It only needs to know that it has a tool capable of providing the temperature for a city.

This illustrates one of the important benefits of tools: they expose capabilities to the agent without requiring the agent to know how those capabilities are implemented internally.

---

# 10. Tool ≠ Agent

Do not confuse a **tool** with an **agent**.

## Tool

For example:

```python
def calculate(...):
    ...
```

A tool executes an operation.

It does not perform the overall reasoning process.

## Agent

For example:

```python
Agent(
    ...
)
```

The agent can use the model to determine:

```text
What does the user want?
        ↓
Can I answer directly?
        ↓
Should I use a tool?
        ↓
Which tool?
        ↓
What parameters?
        ↓
What should I do with the result?
```

This is why an agent can orchestrate multiple tools.

---

# 11. The Three Tools in This Example

The generated Python example provides three focused capabilities.

### `get_temperature`

```python
get_temperature(city: str) -> str
```

Used for city temperature questions.

### `calculate`

```python
calculate(
    a: float,
    b: float,
    operation: str
) -> float
```

Supports:

```text
add
subtract
multiply
divide
```

It explicitly prevents division by zero and rejects unsupported operations.

### `get_research_area`

```python
get_research_area(topic: str) -> str
```

Maps the lesson's example topics to their associated research areas:

```text
computer vision
    → Computer Vision

large language models
    → NLP / Generative AI

reinforcement learning
    → Reinforcement Learning

medical imaging
    → Medical AI
```

Together, these tools demonstrate how one agent can select different capabilities based on the user's request.

---

# 12. Key Concepts to Remember

## Tool Schema

A tool schema describes the capability exposed to the agent, including information such as:

```text
Tool name
Description
Parameters
Parameter types
Return type
```

## Function Signature

The signature communicates the expected inputs and output:

```python
def calculate(
    a: float,
    b: float,
    operation: str
) -> float:
```

## Docstring

The docstring explains what the tool does and what its parameters mean:

```python
"""
Performs a mathematical operation on two numbers.

Args:
    a: First number.
    b: Second number.
    operation: Operation to perform.
"""
```

## Tool Selection

The model decides which available capability is appropriate for the user's request.

## Tool Execution

Python executes the selected function.

## Error Handling

Tools should communicate meaningful failures, such as:

```python
raise ValueError("Cannot divide by zero.")
```

## Focused Tool Design

A tool should ideally represent one clear capability rather than trying to do everything.

---

# 13. Exercise

Add or experiment with the research-area tool:

```python
def get_research_area(topic: str) -> str:
    """
    Returns the main research area associated
    with a given topic.
    """
```

Make it support:

```text
computer vision → Computer Vision
large language models → NLP / Generative AI
reinforcement learning → Reinforcement Learning
medical imaging → Medical AI
```

Then try:

> What research area does medical imaging belong to?

After that, test multi-tool selection:

> What is the temperature in Pune and what research area does medical imaging belong to?

The goal is to observe how the agent selects one or more tools based on the request.

---

# 14. What Comes Next

The next lesson moves deeper into what actually happens inside an ADK agent.

The flow introduced is:

```text
User Message
     ↓
Session
     ↓
Agent
     ↓
LLM Request
     ↓
Tool Call?
   ↙       ↘
 No        Yes
 ↓          ↓
Answer     Tool
             ↓
        Tool Result
             ↓
            LLM
             ↓
           Answer
```

The next concepts include:

- Sessions
- Events
- State
- Context
- The internal flow between an agent, LLM, tools, and tool results

These concepts help explain the difference between a simple tool-calling demonstration and a more complete agent system.

---

## Summary

The central lesson is that **tools provide focused capabilities that an agent can select and invoke**.

A well-designed tool should have:

1. A clear function name.
2. Explicit parameter types.
3. A meaningful return type.
4. A useful docstring.
5. Clear error handling.
6. One focused capability.

The agent determines **which tool to use and what parameters to provide**, while the Python function performs the actual work.
