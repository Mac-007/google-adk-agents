import os
import sys
import asyncio

# ============================================================
# ADD PROJECT ROOT TO PYTHON PATH
# ============================================================

# lesson4_tools.py is expected to be inside a subdirectory of
# the project root:
#
# google-adk-agents/
#     ├── model_selector.py
#     └── 04/
#          └── lesson4_tools.py
#
# Add the project root so model_selector.py can be imported.

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


# LiteLLM expects the OpenRouter API key in this variable.
os.environ["OPENROUTER_API_KEY"] = API_KEY


# ============================================================
# 3. REDUCE LITELLM DEBUG OUTPUT
# ============================================================

litellm.suppress_debug_info = True


# ============================================================
# 4. CREATE TOOLS
# ============================================================

def get_temperature(city: str) -> str:
    """
    Return the temperature for a supported city.

    Args:
        city: Name of the city.

    Returns:
        The temperature for the city, or a message when the
        temperature is unavailable.
    """

    temperatures = {
        "Mumbai": "31°C",
        "Delhi": "34°C",
        "Pune": "28°C",
        "Kolhapur": "27°C",
    }

    result = temperatures.get(
        city,
        "Temperature unavailable."
    )

    print(
        f"\n[TOOL CALLED] get_temperature(city={city!r}) "
        f"-> {result}"
    )

    return result


def calculate(
    a: float,
    b: float,
    operation: str
) -> float:
    """
    Perform a mathematical operation on two numbers.

    Args:
        a: First number.
        b: Second number.
        operation: Operation to perform. Supported operations
            are add, subtract, multiply, and divide.

    Returns:
        The result of the requested mathematical operation.

    Raises:
        ValueError: If the operation is unsupported or division
            by zero is requested.
    """

    if operation == "add":
        result = a + b

    elif operation == "subtract":
        result = a - b

    elif operation == "multiply":
        result = a * b

    elif operation == "divide":
        if b == 0:
            raise ValueError("Cannot divide by zero.")

        result = a / b

    else:
        raise ValueError(
            f"Unsupported operation: {operation}"
        )

    print(
        f"\n[TOOL CALLED] calculate("
        f"a={a}, b={b}, operation={operation!r}) = {result}"
    )

    return result


def get_research_area(topic: str) -> str:
    """
    Return the main research area associated with a topic.

    Args:
        topic: Topic whose research area should be identified.

    Returns:
        The associated research area, or a message when the
        topic is not available in the mapping.
    """

    research_areas = {
        "computer vision": "Computer Vision",
        "large language models": "NLP / Generative AI",
        "reinforcement learning": "Reinforcement Learning",
        "medical imaging": "Medical AI",
    }

    result = research_areas.get(
        topic.lower(),
        "Research area unavailable."
    )

    print(
        f"\n[TOOL CALLED] get_research_area(topic={topic!r}) "
        f"-> {result}"
    )

    return result


# ============================================================
# 5. CREATE AGENT
# ============================================================

def create_agent():
    """
    Create and configure the ADK agent.

    Returns:
        A configured Google ADK Agent with the lesson tools.
    """

    # --------------------------------------------------------
    # Get model from model_selector.py
    # --------------------------------------------------------

    model_id = select_model()

    print(
        f"[AGENT] Using model: {model_id}"
    )

    # --------------------------------------------------------
    # Create ADK agent
    # --------------------------------------------------------

    agent = Agent(
        name="general_assistant",

        model=LiteLlm(
            model=f"openrouter/{model_id}"
        ),

        instruction=(
            "You are a helpful assistant. "
            "Answer briefly and clearly. "
            "Use the available tools whenever they are "
            "appropriate for answering the user's question. "
            "Do not invent tool results. "
            "Use get_temperature for temperature questions, "
            "calculate for mathematical operations, and "
            "get_research_area for research-area questions."
        ),

        tools=[
            get_temperature,
            calculate,
            get_research_area,
        ],
    )

    return agent


# ============================================================
# 6. RUN AGENT
# ============================================================

async def main():
    """
    Run the ADK agent with example multi-tool requests.

    The examples demonstrate both single-tool selection and
    multi-tool selection from the lesson.
    """

    try:

        agent = create_agent()

        runner = InMemoryRunner(
            agent=agent
        )

        # ----------------------------------------------------
        # Example request:
        # The agent should select the temperature tool.
        # ----------------------------------------------------

        events = await runner.run_debug(
            "What's the temperature in Pune?"
        )

        print("\nExample 1 - Agent response:")
        print("-" * 60)

        for event in events:

            if not event.content:
                continue

            for part in event.content.parts:

                if part.text and not part.thought:
                    print(part.text)

        print("-" * 60)

        # ----------------------------------------------------
        # Example request:
        # The agent should select the calculator tool.
        # ----------------------------------------------------

        events = await runner.run_debug(
            "Calculate 25 times 8."
        )

        print("\nExample 2 - Agent response:")
        print("-" * 60)

        for event in events:

            if not event.content:
                continue

            for part in event.content.parts:

                if part.text and not part.thought:
                    print(part.text)

        print("-" * 60)

        # ----------------------------------------------------
        # Example request:
        # The agent may need both tools.
        # ----------------------------------------------------

        events = await runner.run_debug(
            "What's the temperature in Pune and "
            "what research area does medical imaging belong to?"
        )

        print("\nExample 3 - Agent response:")
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
