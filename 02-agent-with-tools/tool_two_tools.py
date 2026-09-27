# ============================================================
# TWO-TOOL AGENT
# ============================================================
# This program creates a Google ADK agent with TWO tools:
#
# 1. add_numbers(a, b)
#    - Adds two numbers and returns the result.
#
# 2. multiply_numbers(a, b)
#    - Multiplies two numbers and returns the result.
#
# The agent decides which tool to use based on the user's request.
# For example:
#   - "Add 25 and 17"      -> uses add_numbers
#   - "Multiply 5 and 6"   -> uses multiply_numbers
#
# The rest of the program follows the same structure as the
# original one-tool example.
# ============================================================

import os
import sys
import asyncio

# ============================================================
# ADD PROJECT ROOT TO PYTHON PATH
# ============================================================

# tool.py is inside:
#
# google-adk-agents/
#     ├── model_selector.py
#     └── 02/
#          └── tool.py
#
# So we need to add the parent directory of this file
# to Python's import path.

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


# ============================================================
# IMPORTS
# ============================================================

import litellm
from dotenv import load_dotenv

from google.adk.agents import Agent
from google.adk.runners import InMemoryRunner
from google.adk.models.lite_llm import LiteLlm

from model_selector import select_model


# ============================================================
# 1. LOAD ENVIRONMENT
# ============================================================

load_dotenv()


# ============================================================
# 2. GET API KEY
# ============================================================

API_KEY = os.getenv("API_KEY")

if not API_KEY:
    raise RuntimeError(
        "API_KEY is missing. "
        "Please add your OpenRouter API key to the .env file."
    )


# LiteLLM expects this variable.
os.environ["OPENROUTER_API_KEY"] = API_KEY


# ============================================================
# 3. REDUCE LITELLM DEBUG OUTPUT
# ============================================================

litellm.suppress_debug_info = True


# ============================================================
# 4. CREATE TWO TOOLS
# ============================================================

# ------------------------------------------------------------
# TOOL 1: ADD NUMBERS
# ------------------------------------------------------------

def add_numbers(a: int, b: int) -> int:
    """
    Add two numbers and return the result.
    """

    result = a + b

    print(
        f"\n[TOOL CALLED] add_numbers({a}, {b}) = {result}"
    )

    return result


# ------------------------------------------------------------
# TOOL 2: MULTIPLY NUMBERS
# ------------------------------------------------------------

def multiply_numbers(a: int, b: int) -> int:
    """
    Multiply two numbers and return the result.
    """

    result = a * b

    print(
        f"\n[TOOL CALLED] multiply_numbers({a}, {b}) = {result}"
    )

    return result


# ============================================================
# 5. CREATE AGENT
# ============================================================

def create_agent():

    # --------------------------------------------------------
    # Get model from model_selector.py
    # --------------------------------------------------------

    model_id = select_model()

    print(
        f"[AGENT] Using model: {model_id}"
    )

    # --------------------------------------------------------
    # Create ADK agent with TWO tools
    # --------------------------------------------------------

    agent = Agent(
        name="test_agent",

        model=LiteLlm(
            model=f"openrouter/{model_id}"
        ),

        instruction=(
            "You are a helpful assistant. "
            "Answer briefly and clearly. "
            "When the user asks you to add numbers, "
            "use the add_numbers tool. "
            "When the user asks you to multiply numbers, "
            "use the multiply_numbers tool."
        ),

        tools=[
            add_numbers,
            multiply_numbers
        ],
    )

    return agent


# ============================================================
# 6. RUN AGENT
# ============================================================

async def main():

    try:

        agent = create_agent()

        runner = InMemoryRunner(
            agent=agent
        )

        # Test both tools.
        events = await runner.run_debug(
            "Please add 25 and 17 using the add_numbers tool, "
            "then multiply 5 and 6 using the multiply_numbers tool."
        )

        print("\nAgent response:")
        print("-" * 60)

        for event in events:

            if not event.content:
                continue

            for part in event.content.parts:

                if part.text and not part.thought:
                    print(part.text)

        print("-" * 60)

    except Exception as error:

        print("\nSomething went wrong:")
        print(error)


# ============================================================
# 7. START PROGRAM
# ============================================================

if __name__ == "__main__":
    asyncio.run(main())
