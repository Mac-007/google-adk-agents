import os
import asyncio

import litellm
from dotenv import load_dotenv

from google.adk.agents import Agent
from google.adk.runners import InMemoryRunner
from google.adk.models.lite_llm import LiteLlm


# ============================================================
# 1. LOAD ENVIRONMENT VARIABLES
# ============================================================
# load_dotenv() reads variables from your .env file and makes
# them available through os.getenv().
#
# Example .env file:
#     API_KEY=your_openrouter_api_key
#
# Keeping API keys in .env is safer than writing them directly
# inside your Python source code.
load_dotenv()


# ============================================================
# 2. GET THE OPENROUTER API KEY
# ============================================================
# Read the API key from the environment.
API_KEY = os.getenv("API_KEY")

# Stop the program early if the API key is not available.
# This gives a clear error instead of failing later when
# LiteLLM tries to contact OpenRouter.
if not API_KEY:
    raise RuntimeError(
        "API_KEY is missing. Please add your OpenRouter API key "
        "to the .env file."
    )


# ============================================================
# 3. CONFIGURE OPENROUTER
# ============================================================
# LiteLLM expects the OpenRouter key in the
# OPENROUTER_API_KEY environment variable.
#
# We read our custom API_KEY variable above and then expose
# it using the variable name expected by LiteLLM.
os.environ["OPENROUTER_API_KEY"] = API_KEY


# ============================================================
# 4. REDUCE LITELLM DEBUG OUTPUT
# ============================================================
# LiteLLM can print additional debugging information.
# We disable that here to keep the terminal output clean.
litellm.suppress_debug_info = True


# ============================================================
# 5. CREATE THE ADK AGENT
# ============================================================
# LiteLlm allows Google ADK to communicate with models
# supported through LiteLLM.
#
# The model below is hosted through OpenRouter.
agent = Agent(
    name="test_agent",

    model=LiteLlm(
        model="openrouter/nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free"
    ),

    # This instruction tells the model how it should behave.
    instruction=(
        "You are a helpful assistant. "
        "Answer briefly and clearly."
    ),
)


# ============================================================
# 6. CREATE AN IN-MEMORY RUNNER
# ============================================================
# InMemoryRunner is useful for testing and small applications.
#
# The conversation/session data is kept in memory rather than
# being stored in an external database.
runner = InMemoryRunner(agent=agent)


# ============================================================
# 7. RUN THE AGENT
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

        # ----------------------------------------------------
        # Process the events returned by ADK
        # ----------------------------------------------------
        for event in events:

            # Some events may not contain content.
            # Therefore, check before accessing event.content.
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
    # 8. HANDLE COMMON API ERRORS
    # ========================================================
    except Exception as error:

        # Convert the exception to a string so we can inspect
        # the HTTP status code or error message.
        error_message = str(error)

        # HTTP 429 usually means the model/API is rate-limited.
        if "429" in error_message or "rate-limited" in error_message.lower():
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
# 9. START THE PROGRAM
# ============================================================
# asyncio.run() starts Python's asynchronous event loop and
# executes our main() coroutine.
if __name__ == "__main__":
    asyncio.run(main())