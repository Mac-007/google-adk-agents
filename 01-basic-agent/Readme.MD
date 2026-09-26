# Basic Google ADK Agent

Creates and runs a basic Google ADK agent using `LiteLlm`, OpenRouter, and `InMemoryRunner`.

### What the Code Does

* Loads the API configuration from `.env`
* Configures LiteLLM for model access
* Creates a Google ADK agent with a model and system instruction
* Runs the agent using `InMemoryRunner`
* Sends a prompt to the agent
* Processes the response events returned by ADK
* Prints only the generated text response
* Filters out thought/reasoning content
* Handles common authentication, rate-limit, and model errors

---

## 1. Import the Required Libraries

```python
import os
import asyncio

import litellm
from dotenv import load_dotenv

from google.adk.agents import Agent
from google.adk.runners import InMemoryRunner
from google.adk.models.lite_llm import LiteLlm
```

The first two imports are standard Python modules.

```python
import os
```

`os` provides access to operating-system functionality. In this example, it is mainly used to work with environment variables.

The API key is retrieved using:

```python
os.getenv("API_KEY")
```

It is also used later to set another environment variable required by LiteLLM.

```python
import asyncio
```

The agent is executed asynchronously. Therefore, `asyncio` is used to run the asynchronous `main()` function at the end of the program.

---

The next imports are third-party libraries.

```python
import litellm
```

LiteLLM is used as the model interface in this example. The code also uses it to suppress additional debug information.

```python
from dotenv import load_dotenv
```

`load_dotenv()` loads environment variables from a `.env` file. This allows the API key to be kept outside the Python source code.

---

The remaining imports come from Google ADK:

```python
from google.adk.agents import Agent
```

`Agent` is used to create the ADK agent.

```python
from google.adk.runners import InMemoryRunner
```

`InMemoryRunner` is used to execute the agent while keeping the relevant session information in memory.

```python
from google.adk.models.lite_llm import LiteLlm
```

`LiteLlm` is used to configure the model that the ADK agent will use through LiteLLM.

---

## 2. Load Environment Variables

```python
load_dotenv()
```

This line loads the variables defined in the `.env` file into the application's environment.

For example, the `.env` file can contain:

```text
API_KEY=your_openrouter_api_key
```

Instead of writing the API key directly into the Python code, the program reads it from the environment.

This keeps configuration separate from the application code.

The important point here is that `load_dotenv()` does not itself retrieve the API key into the `API_KEY` Python variable. It makes the values available as environment variables. The code retrieves the value in the next step.

---

## 3. Read the API Key

```python
API_KEY = os.getenv("API_KEY")
```

`os.getenv()` reads the value of an environment variable.

Here, the code asks for:

```text
API_KEY
```

and stores the resulting value in the Python variable:

```python
API_KEY
```

At this point, the program has the API key available in memory.

The code then checks whether a value was actually provided:

```python
if not API_KEY:
    raise RuntimeError(
        "API_KEY is missing. Please add your OpenRouter API key "
        "to the .env file."
    )
```

This check is useful because the rest of the program requires the API key to communicate with the model.

If the variable is missing or empty, the program stops immediately by raising a `RuntimeError`.

Instead of allowing the program to continue and fail later with a potentially less obvious authentication error, the code gives a clear message explaining what needs to be configured.

---

## 4. Configure the OpenRouter API Key for LiteLLM

```python
os.environ["OPENROUTER_API_KEY"] = API_KEY
```

The application initially reads the key from:

```text
API_KEY
```

However, the LiteLLM configuration expects the OpenRouter API key to be available through:

```text
OPENROUTER_API_KEY
```

Therefore, this line takes the value stored in `API_KEY` and assigns it to the `OPENROUTER_API_KEY` environment variable.

Conceptually, the flow is:

```text
.env
  ↓
API_KEY
  ↓
OPENROUTER_API_KEY
  ↓
LiteLLM
  ↓
OpenRouter
```

This allows the model configuration later in the code to use OpenRouter through LiteLLM without putting the API key directly into the model configuration.

---

## 5. Suppress LiteLLM Debug Information

```python
litellm.suppress_debug_info = True
```

LiteLLM can produce additional information while making model requests.

For this learning example, the intention is to keep the terminal output focused on the actual agent response.

Setting:

```python
litellm.suppress_debug_info = True
```

reduces the additional LiteLLM debug output.

This does not change the agent's instructions or the model itself. It only controls the amount of debug information displayed by LiteLLM.

---

## 6. Create the Google ADK Agent

```python
agent = Agent(
    name="test_agent",

    model=LiteLlm(
        model="openrouter/nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free"
    ),

    instruction=(
        "You are a helpful assistant. "
        "Answer briefly and clearly."
    ),
)
```

This is the central part of the example.

The `Agent` object represents the agent that will receive the user's request and use the configured model to generate a response.

There are three important pieces of configuration here:

### Agent name

```python
name="test_agent"
```

This gives the agent the name `test_agent`.

The name identifies this particular agent configuration.

### Model

```python
model=LiteLlm(
    model="openrouter/nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free"
)
```

The `model` parameter tells the ADK agent which model interface to use.

Here, `LiteLlm` is used as the interface between Google ADK and the model.

The model identifier specifies the model being accessed through OpenRouter.

So rather than the `Agent` directly containing an OpenRouter-specific API call, the model is configured through:

```text
Google ADK Agent
       ↓
    LiteLlm
       ↓
   OpenRouter
       ↓
     Model
```

### Instruction

```python
instruction=(
    "You are a helpful assistant. "
    "Answer briefly and clearly."
)
```

The `instruction` defines how the agent should behave.

In this example, the instruction tells the model two things:

1. Behave as a helpful assistant.
2. Keep its answers brief and clear.

The instruction is part of the agent configuration. It is not the actual user request that will be sent later.

The distinction is:

```text
instruction
    ↓
Defines how the agent should behave

user request
    ↓
Defines what the agent should do
```

---

## 7. Create an In-Memory Runner

```python
runner = InMemoryRunner(agent=agent)
```

After creating the agent, the code creates a runner and passes the agent to it.

The runner is responsible for executing the agent.

In this example, `InMemoryRunner` is used because this is a simple learning and testing program. The session-related information is kept in memory rather than being stored in an external database.

The relationship between the two objects is:

```text
Agent
  ↓
InMemoryRunner
  ↓
Agent execution
```

The agent defines what should be executed, while the runner provides the mechanism for actually running it.

---

## 8. Define the Main Function

```python
async def main():
    """
    Run the ADK agent and print its text response.
    """
```

The main execution logic is placed inside an asynchronous function called `main()`.

The function is defined using:

```python
async def
```

rather than the normal:

```python
def
```

because the agent execution later uses `await`.

The documentation string explains the purpose of the function: run the agent and print its text response.

---

## 9. Run the Agent

```python
events = await runner.run_debug(
    "Say hello and tell me that you are working."
)
```

This is where the agent is actually executed.

The input passed to `run_debug()` is:

```text
Say hello and tell me that you are working.
```

This is the request that the agent receives.

The `await` keyword is required because `run_debug()` is asynchronous.

The returned result is stored in:

```python
events
```

The code then works with these returned events instead of assuming that the result is simply one text string.

Conceptually:

```text
User request
     ↓
run_debug()
     ↓
Agent execution
     ↓
Events
```

---

## 10. Print the Agent Response

```python
print("\nAgent response:")
print("-" * 40)
```

These lines simply make the terminal output easier to read.

The first line prints:

```text
Agent response:
```

The second line prints a separator made from 40 hyphens.

---

The code then loops through the events:

```python
for event in events:
```

The runner can return multiple events, so the code examines them one by one.

Before accessing the event's content, it checks:

```python
if not event.content:
    continue
```

Not every event necessarily contains content that needs to be displayed.

If an event does not contain content, `continue` skips that event and moves to the next one.

---

## 11. Process Content Parts

```python
for part in event.content.parts:
```

An event can contain content, and that content can contain multiple parts.

The code therefore loops through:

```text
events
  ↓
event
  ↓
event.content
  ↓
event.content.parts
  ↓
part
```

Each `part` is then inspected.

---

## 12. Print Only Normal Text

```python
if part.text and not part.thought:
    print(part.text)
```

This condition makes sure that the code prints the appropriate text content.

First:

```python
part.text
```

checks whether the part contains text.

Then:

```python
not part.thought
```

ensures that the part is not marked as a thought.

Only when both conditions are satisfied does the code execute:

```python
print(part.text)
```

This means the program displays the normal text response while avoiding thought content.

The important idea is that the code does not simply print every piece of content returned by the runner. It explicitly checks what type of content it is dealing with.

---

## 13. Finish the Response Output

```python
print("-" * 40)
```

After processing the events, another separator is printed.

This simply marks the end of the displayed agent response in the terminal.

---

## 14. Handle Errors

The agent execution is wrapped in a `try` block:

```python
try:
    ...
except Exception as error:
```

The purpose is to prevent an exception from producing an unstructured traceback as the only useful information for the user.

If something goes wrong, the exception is captured in:

```python
error
```

The code converts it into a string:

```python
error_message = str(error)
```

This makes it possible to inspect the message and identify several common error cases.

---

## 15. Handle Rate-Limit Errors

```python
if "429" in error_message or "rate-limited" in error_message.lower():
    print(
        "\nThe model is temporarily rate-limited. "
        "Please try again later."
    )
```

The code checks whether the error message contains either:

```text
429
```

or:

```text
rate-limited
```

If so, it prints a message explaining that the model is temporarily rate-limited.

This provides a more understandable message than simply displaying the raw exception.

---

## 16. Handle Authentication or Permission Errors

```python
elif "401" in error_message or "403" in error_message:
    print(
        "\nAuthentication or permission error. "
        "Please check your OpenRouter API key."
    )
```

The code checks for HTTP status codes:

```text
401
403
```

In this example, these are treated as authentication or permission-related problems.

The user is instructed to check the OpenRouter API key.

---

## 17. Handle Model Not Found Errors

```python
elif "404" in error_message:
    print(
        "\nModel not found. "
        "Please check the OpenRouter model name."
    )
```

If the error contains `404`, the program reports that the configured model could not be found.

This points the user toward checking the model identifier:

```python
model="openrouter/nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free"
```

---

## 18. Handle Unexpected Errors

```python
else:
    print("\nSomething went wrong:")
    print(error_message)
```

If the error does not match any of the specific cases above, the program prints the actual error message.

This is useful during exploration because unexpected errors can still be inspected directly from the terminal.

---

## 19. Start the Program

```python
if __name__ == "__main__":
    asyncio.run(main())
```

This is the entry point of the Python file.

The condition:

```python
if __name__ == "__main__":
```

checks whether this file is being executed directly.

If it is, the following line runs:

```python
asyncio.run(main())
```

`main()` is an asynchronous function, so `asyncio.run()` is used to start it.

This begins the complete execution flow:

```text
Start program
    ↓
load_dotenv()
    ↓
Read API key
    ↓
Configure OpenRouter
    ↓
Create Agent
    ↓
Create InMemoryRunner
    ↓
Run agent
    ↓
Receive events
    ↓
Inspect event content
    ↓
Print text response
```

---

## Complete Picture

The important pieces of this example work together as follows:

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
          LiteLlm
              │
              ▼
        OpenRouter
              │
              ▼
            Model
              │
              ▼
         ADK Agent
              │
              ▼
      InMemoryRunner
              │
              ▼
        run_debug()
              │
              ▼
           events
              │
              ▼
      event.content.parts
              │
              ▼
        Text response
```

The key learning from this code is the complete execution path: the program first prepares the model credentials, creates an ADK agent with a model and instruction, gives that agent to a runner, executes a request, receives events, and finally extracts and prints the agent's text response.