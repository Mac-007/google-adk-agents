import os
import asyncio

from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.runners import InMemoryRunner
from google.adk.models.lite_llm import LiteLlm
import litellm


load_dotenv()

API_KEY = os.getenv("API_KEY")

if not API_KEY:
    print("API_KEY is missing. Please check your .env file.")
    exit(1)

os.environ["OPENROUTER_API_KEY"] = API_KEY

# Disable LiteLLM logging
litellm.suppress_debug_info = True


agent = Agent(
    name="test_agent",
    model=LiteLlm(
        #model="openrouter/google/gemma-4-31b-it:free"
        model ="openrouter/nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free"
    ),
    instruction="You are a helpful assistant. Answer briefly.",
)

runner = InMemoryRunner(agent=agent)


async def main():
    try:
        response = await runner.run_debug(
            "Say hello and tell me that you are working."
        )

        print("\nAgent response:")

        for event in response:
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text and not part.thought:
                        print(part.text)

    except Exception as e:
        error_message = str(e)

        if "429" in error_message or "rate-limited" in error_message:
            print("\nModel is temporarily busy. Please try again in a moment.")

        elif "401" in error_message or "403" in error_message:
            print("\nAPI key is invalid or does not have permission.")

        elif "404" in error_message:
            print("\nModel was not found. Please check the model name.")

        else:
            print("\nSomething went wrong while contacting the AI model.")


if __name__ == "__main__":
    asyncio.run(main())