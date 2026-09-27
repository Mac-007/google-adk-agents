import os
import sys
import asyncio
from dataclasses import dataclass, field
from typing import Any


# ============================================================
# ADD PROJECT ROOT TO PYTHON PATH
# ============================================================

# sessions_events_state_context.py is expected to be inside a
# lesson directory under the project root:
#
# google-adk-agents/
#     ├── model_selector.py
#     └── 04/
#          └── sessions_events_state_context.py
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

# LiteLLM expects this variable.
os.environ["OPENROUTER_API_KEY"] = API_KEY


# ============================================================
# 3. REDUCE LITELLM DEBUG OUTPUT
# ============================================================

litellm.suppress_debug_info = True


# ============================================================
# 4. SESSION, STATE, AND EVENTS
# ============================================================

@dataclass
class ResearchSession:
    """
    Small application-level model for demonstrating the concepts
    introduced in Lesson 5.

    Session:
        Represents one interaction/run context.

    State:
        Stores information that the application deliberately
        maintains.

    Events:
        Records important things that happened during execution.

    Context:
        In this lesson, the current session object represents the
        information available to the tools while they execute.

    Note:
        This is a teaching model of the concepts. It intentionally
        keeps the implementation simple rather than introducing the
        complete ADK session/context API before those APIs are
        covered in detail.
    """

    session_id: str
    state: dict[str, Any] = field(default_factory=dict)
    events: list[str] = field(default_factory=list)

    def add_event(self, event: str) -> None:
        """
        Record an event in the current session.

        Args:
            event: Human-readable description of what happened.
        """

        self.events.append(event)
        print(f"[EVENT] {event}")

    def set_state(self, key: str, value: Any) -> None:
        """
        Store information maintained by the application.

        Args:
            key: Name of the state value.
            value: Value to store.
        """

        self.state[key] = value
        print(f"[STATE] {key} = {value!r}")

    def get_state(self, key: str, default: Any = None) -> Any:
        """
        Retrieve information from the current session state.

        Args:
            key: State key to retrieve.
            default: Value returned when the key is not present.

        Returns:
            The stored state value or the supplied default.
        """

        return self.state.get(key, default)


# ============================================================
# 5. CREATE LESSON TOOLS
# ============================================================

# The active session is intentionally kept outside the tool
# functions so the example stays easy to understand.
#
# In a production ADK application, session/state/context should
# be managed through the appropriate ADK mechanisms.

CURRENT_SESSION: ResearchSession | None = None


def remember_user_name(name: str) -> str:
    """
    Store the user's name in application state.

    Args:
        name: The user's name.

    Returns:
        A confirmation message.
    """

    if CURRENT_SESSION is None:
        raise RuntimeError("No active session.")

    CURRENT_SESSION.add_event(
        f'User provided their name: "{name}"'
    )

    CURRENT_SESSION.set_state(
        "user_name",
        name
    )

    return f"Nice to meet you, {name}."


def get_user_name() -> str:
    """
    Retrieve the user's name from the current session state.

    Returns:
        The stored user name, or a message when no name is stored.
    """

    if CURRENT_SESSION is None:
        raise RuntimeError("No active session.")

    CURRENT_SESSION.add_event(
        "Agent requested the user's name from state."
    )

    name = CURRENT_SESSION.get_state("user_name")

    if not name:
        return "I don't have your name stored in this session."

    return f"Your name is {name}."


def set_research_topic(topic: str) -> str:
    """
    Store the current research topic in session state.

    Args:
        topic: Research topic being investigated.

    Returns:
        A confirmation message.
    """

    if CURRENT_SESSION is None:
        raise RuntimeError("No active session.")

    CURRENT_SESSION.add_event(
        f'Research topic received: "{topic}"'
    )

    CURRENT_SESSION.set_state(
        "topic",
        topic
    )

    return f"Research topic set to {topic}."


def record_research_action(action: str) -> str:
    """
    Record an important research action as an event.

    Args:
        action: Description of the research action.

    Returns:
        Confirmation that the event was recorded.
    """

    if CURRENT_SESSION is None:
        raise RuntimeError("No active session.")

    CURRENT_SESSION.add_event(
        f"Research action: {action}"
    )

    return f"Recorded research action: {action}"


def get_session_state() -> str:
    """
    Return the current application state.

    Returns:
        A readable representation of the session state.
    """

    if CURRENT_SESSION is None:
        raise RuntimeError("No active session.")

    CURRENT_SESSION.add_event(
        "Agent inspected current session state."
    )

    if not CURRENT_SESSION.state:
        return "No state has been stored yet."

    return str(CURRENT_SESSION.state)


# ============================================================
# 6. CREATE AGENT
# ============================================================

def create_agent():
    """
    Create the Lesson 5 ADK agent.

    The agent is given tools that demonstrate the relationship
    between session state and execution events.
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
        name="session_state_agent",

        model=LiteLlm(
            model=f"openrouter/{model_id}"
        ),

        instruction=(
            "You are a helpful research assistant. "
            "This lesson demonstrates sessions, events, and state. "
            "When the user tells you their name, use "
            "remember_user_name. "
            "When they ask for their name, use get_user_name. "
            "When they provide a research topic, use "
            "set_research_topic. "
            "Use record_research_action when an important research "
            "action should be recorded. "
            "Use get_session_state when the user asks what "
            "information is currently stored. "
            "Do not invent stored state or tool results."
        ),

        tools=[
            remember_user_name,
            get_user_name,
            set_research_topic,
            record_research_action,
            get_session_state,
        ],
    )

    return agent


# ============================================================
# 7. RUN ONE SESSION
# ============================================================

async def run_session(
    runner: InMemoryRunner,
    session: ResearchSession,
    message: str,
) -> None:
    """
    Send one message through the agent and display its response.

    Args:
        runner: ADK in-memory runner.
        session: Current lesson session.
        message: User message to send.
    """

    global CURRENT_SESSION

    CURRENT_SESSION = session

    session.add_event(
        f'User message: "{message}"'
    )

    events = await runner.run_debug(message)

    print("\nAgent response:")
    print("-" * 60)

    for event in events:

        if not event.content:
            continue

        for part in event.content.parts:

            if part.text and not part.thought:
                print(part.text)

    print("-" * 60)


# ============================================================
# 8. RUN AGENT
# ============================================================

async def main():
    """
    Demonstrate session continuity, state, and events.

    The sequence mirrors the lesson's core example:

        User: My name is Amit.
        Agent: Nice to meet you, Amit.
        User: What's my name?
        Agent: Your name is Amit.

    A research-topic example is then used to show how application
    state can hold information across multiple requests.
    """

    try:

        agent = create_agent()

        runner = InMemoryRunner(
            agent=agent
        )

        # ----------------------------------------------------
        # Create one session.
        # ----------------------------------------------------

        session = ResearchSession(
            session_id="lesson-5-demo"
        )

        print("\n" + "=" * 60)
        print("LESSON 5 - SESSION / EVENTS / STATE DEMO")
        print("=" * 60)

        # ----------------------------------------------------
        # Conversation continuity example.
        # ----------------------------------------------------

        await run_session(
            runner,
            session,
            "My name is Amit."
        )

        await run_session(
            runner,
            session,
            "What's my name?"
        )

        # ----------------------------------------------------
        # Research assistant example.
        # ----------------------------------------------------

        await run_session(
            runner,
            session,
            "I'm researching vision-language models."
        )

        await run_session(
            runner,
            session,
            "What research information do you currently have?"
        )

        # ----------------------------------------------------
        # Display the lesson-level state and event timeline.
        # ----------------------------------------------------

        print("\nSESSION STATE")
        print("-" * 60)
        print(session.state)

        print("\nEVENT TIMELINE")
        print("-" * 60)

        for index, event in enumerate(
            session.events,
            start=1
        ):
            print(f"{index}. {event}")

        print("-" * 60)

        # ----------------------------------------------------
        # Important architecture reminder.
        # ----------------------------------------------------

        print(
            "\nConceptual model:"
            "\n"
            "SESSION"
            "\n  ├── EVENTS -> what happened"
            "\n  └── STATE  -> what information is maintained"
            "\n                 ↓"
            "\n              CONTEXT"
            "\n                 ↓"
            "\n               AGENT"
        )

    except Exception as error:

        print("\nSomething went wrong:")
        print(error)


# ============================================================
# 9. START PROGRAM
# ============================================================

if __name__ == "__main__":
    asyncio.run(main())
