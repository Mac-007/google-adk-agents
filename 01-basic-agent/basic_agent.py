import os
import sys
import asyncio


# ============================================================
# 1. ADD PROJECT ROOT TO PYTHON PATH
# ============================================================

# Project structure:
#
# google-adk-agents/
# │
# ├── model_selector.py
# ├── .env
# │
# └── 02/
#     └── basic_agent.py
#
# basic_agent.py is inside the "02" folder.
# We need to add the parent/project-root directory so that
# Python can import model_selector.py.

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


# ============================================================
# 2. IMPORTS
# ============================================================

import litellm
from dotenv import load_dotenv

from google.adk.agents import Agent
from google.adk.runners import InMemoryRunner
from google.adk.models.lite_llm import LiteLlm

# Import our model-selection function from the root folder.
from model_selector import select_model


# ============================================================
# 3. LOAD ENVIRONMENT VARIABLES
# ============================================================

# load_dotenv() reads variables from your .env file and makes
# them available through os.getenv().

load_dotenv()


# ============================================================
# 4. GET THE OPENROUTER API KEY
# ============================================================

# Read the API key from the environment.

API_KEY = os.getenv("API_KEY")


# Stop the program early if the API key is not available.

if not API_KEY:
    raise RuntimeError(
        "API_KEY is missing. Please add your OpenRouter API key "
        "to the .env file."
    )


# ============================================================
# 5. CONFIGURE OPENROUTER
# ============================================================

# LiteLLM expects the OpenRouter key in the
# OPENROUTER_API_KEY environment variable.

os.environ["OPENROUTER_API_KEY"] = API_KEY


# ============================================================
# 6. REDUCE LITELLM DEBUG OUTPUT
# ============================================================

litellm.suppress_debug_info = True


# ============================================================
# 7. SELECT MODEL DYNAMICALLY
# ============================================================

# Instead of manually writing:
#
# model="openrouter/nvidia/..."
#
# we ask model_selector.py to find a suitable free
# tool-capable model.

MODEL_ID = select_model()

print(
    f"\n[MAIN] Model selected: {MODEL_ID}"
)


# ============================================================
# 8. CREATE THE ADK AGENT
# ============================================================

agent = Agent(
    name="test_agent",

    # model_selector.py returns something like:
    #
    # inclusionai/ling-3.0-flash-fin:free
    #
    # LiteLLM needs:
    #
    # openrouter/inclusionai/ling-3.0-flash-fin:free

    model=LiteLlm(
        model=f"openrouter/{MODEL_ID}"
    ),

    # This instruction tells the model how it should behave.

    instruction=(
        "You are a helpful assistant. "
        "Answer briefly and clearly."
    ),
)


# ============================================================
# 9. CREATE AN IN-MEMORY RUNNER
# ============================================================

runner = InMemoryRunner(
    agent=agent
)


# ============================================================
# 10. RUN THE AGENT
# ============================================================

async def main():
    """
    Run the ADK agent and print its text response.
    """

    try:

        # run_debug() is convenient for testing an agent.
        #
        # It returns a collection of events generated while
        # the agent processes the request.

        events = await runner.run_debug(
            "Say hello and tell me that you are working."
        )


        print("\nAgent response:")
        print("-" * 40)


        # ====================================================
        # Process the events returned by ADK
        # ====================================================

        for event in events:

            # Some events may not contain content.

            if not event.content:
                continue


            # An event can contain multiple content parts.

            for part in event.content.parts:

                # We only want normal text responses.
                #
                # Some models may generate "thought" parts.
                # We don't print those because they are not
                # intended to be displayed as the final answer.

                if part.text and not part.thought:
                    print(part.text)


        print("-" * 40)


    # ========================================================
    # 11. HANDLE COMMON API ERRORS
    # ========================================================

    except Exception as error:

        # Convert the exception to a string so we can inspect
        # the HTTP status code or error message.

        error_message = str(error)


        # HTTP 429 usually means the model/API is rate-limited.

        if (
            "429" in error_message
            or "rate-limited" in error_message.lower()
        ):
            print(
                "\nThe model is temporarily rate-limited. "
                "Please try again later."
            )


        # HTTP 401/403 usually indicates an authentication
        # or permission problem.

        elif "401" in error_message or "403" in error_message:
            print(
                "\nAuthentication or permission error. "
                "Please check your OpenRouter API key."
            )


        # HTTP 404 usually means the requested model could
        # not be found.

        elif "404" in error_message:
            print(
                "\nModel not found. "
                "Please check the OpenRouter model name."
            )


        # Handle any other unexpected error.

        else:
            print("\nSomething went wrong:")
            print(error_message)


# ============================================================
# 12. START THE PROGRAM
# ============================================================

if __name__ == "__main__":
    asyncio.run(main())