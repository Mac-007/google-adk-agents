# Lesson 4 — Sessions, Events, State & Context

This lesson introduces four important concepts in ADK:

- **Session**
- **Event**
- **State**
- **Context**

So far, the mental model has been:

```text
User
 ↓
Agent
 ↓
LLM
 ↓
Tool
 ↓
LLM
 ↓
Answer
```

That is enough for a simple demonstration.

However, a real agent needs to maintain continuity across an interaction. For example:

```text
User: My name is Amit.

Agent: Nice to meet you, Amit.

User: What's my name?

Agent: Your name is Amit.
```

The question is:

> Where did the agent get `"Amit"` from?

This is where sessions, events, state, and context become important.

---

# 1. The Four Concepts

Keep these four concepts separate:

```text
┌─────────────────────────────────────────────┐
│                  SESSION                    │
│                                             │
│   ┌───────────────┐                         │
│   │    EVENTS     │                         │
│   └───────┬───────┘                         │
│           │                                 │
│           ↓                                 │
│        STATE                                │
│           │                                 │
│           ↓                                 │
│       CONTEXT                               │
└─────────────────────────────────────────────┘
```

A useful mental model is:

| Concept | Think of it as |
|---|---|
| **Session** | One conversation/run context |
| **Event** | Something that happened |
| **State** | Information currently stored |
| **Context** | Information available to an agent while executing |

The goal of this lesson is first to understand the architecture. The exact ADK API is not the focus yet.

---

# 2. What Is a Session?

Imagine a conversation:

```text
Session
│
├── User: My name is Amit.
├── Agent: Nice to meet you.
├── User: I work on computer vision.
├── Agent: That's interesting.
└── User: What do I work on?
```

The entire conversational interaction can be thought of as a **session**.

Conceptually:

```text
Session = container for an interaction
```

A session can be visualized as:

```text
                     SESSION
                         │
          ┌──────────────┼──────────────┐
          ↓              ↓              ↓
        Event          Event          Event
          │              │              │
       User msg       Agent msg       Tool call
```

A session allows the agent system to maintain continuity.

---

# 3. What Is an Event?

An **event** represents something that happened during execution.

For example:

```text
User message
     ↓
Agent response
     ↓
Tool call
     ↓
Tool result
     ↓
Agent response
```

Think of an event as part of an execution timeline.

For example:

```text
Event 1
User → "Calculate 10 × 5"

Event 2
Agent → decides to use calculator

Event 3
Tool → calculate(10, 5)

Event 4
Tool → 50

Event 5
Agent → "The answer is 50."
```

Events are particularly useful when debugging an agent.

Instead of only asking:

> Why did my agent produce this answer?

you can inspect:

```text
What did the user say?
       ↓
What did the model decide?
       ↓
Which tool was selected?
       ↓
What arguments were passed?
       ↓
What did the tool return?
       ↓
What did the model do next?
```

This is **agent observability**.

---

# 4. What Is State?

State is information that your agent or application wants to maintain.

For example:

```text
state = {
    "user_name": "Amit",
    "preferred_language": "English",
    "current_project": "Medical AI"
}
```

Conceptually:

```text
                   SESSION
                      │
                      ↓
                    STATE
                 ┌──────┼──────┐
                 ↓      ↓      ↓
             user_name language project
```

An important distinction is:

> **State is not the same thing as the entire conversation history.**

Conversation history contains events and messages.

State contains information that your application deliberately maintains.

---

# 5. Why State Becomes Powerful

Consider a shopping agent.

The user says:

```text
"I want a laptop."
```

The agent asks:

```text
"What is your budget?"
```

The user replies:

```text
"₹1 lakh."
```

The application could maintain:

```text
{
    "product": "laptop",
    "budget": 100000
}
```

Later, the user says:

```text
"Show me something lightweight."
```

The agent can use the maintained information:

```text
product = laptop
budget = ₹100,000
```

while handling the new request.

State therefore provides application-maintained information that can be useful during later parts of an interaction.

---

# 6. Context

Context is slightly more subtle.

A useful way to think about it is:

> **Context is the information/resources available to an agent during execution.**

Conceptually:

```text
                     Agent execution
                           │
              ┌────────────┼────────────┐
              ↓            ↓            ↓
            State        Events       Runtime
              │            │            │
              └────────────┼────────────┘
                           ↓
                        Context
                           ↓
                       Agent/Tool
```

Context can allow agents and tools to access information relevant to the current execution.

This becomes particularly important when working with multiple agents:

```text
Root Agent
   │
   ├── Research Agent
   │
   ├── Coding Agent
   │
   └── Review Agent
```

At that point, an important question becomes:

> What information does each agent get?

---

# 7. A Realistic Research Assistant Example

Suppose we build a research assistant:

```text
User
 │
 ↓
Research Agent
 │
 ├── Search papers
 │
 ├── Analyze paper
 │
 └── Generate summary
```

The user says:

> I'm researching vision-language models.

We might maintain:

```text
STATE

topic = "vision-language models"
```

The research agent then searches for papers.

A search event occurs:

```text
EVENT

Tool:
search_papers("vision-language models")
```

The tool returns:

```text
EVENT

Found 10 papers
```

The agent then summarizes them:

```text
EVENT

Agent:
Generate literature summary
```

Finally:

```text
EVENT

Agent:
"Here is your literature review..."
```

This example shows why sessions, events, and state work together.

---

# 8. The Execution Lifecycle

A useful mental model for an ADK agent is:

```text
                    USER
                      │
                      ▼
                   SESSION
                      │
                      ▼
                    AGENT
                      │
                      ▼
                     LLM
                      │
                ┌─────┴─────┐
                │           │
          Direct answer   Tool call
                │           │
                │           ▼
                │          TOOL
                │           │
                │           ▼
                │         RESULT
                │           │
                │           ▼
                └────────── LLM
                            │
                            ▼
                         RESPONSE
```

Throughout this process:

```text
              ┌─────────────────┐
              │     EVENTS      │
              └─────────────────┘
                       │
                       ↓
                execution history

              ┌─────────────────┐
              │      STATE      │
              └─────────────────┘
                       │
                       ↓
                persistent context
```

This is the architecture to keep in mind while learning ADK.

---

# 9. Why This Matters for Multi-Agent Systems

Consider a multi-agent system:

```text
                     Root Agent
                         │
             ┌───────────┼───────────┐
             ↓           ↓           ↓
         Research      Coding      Critic
          Agent         Agent       Agent
```

Suppose the Research Agent discovers:

```text
10 papers
```

How does the Coding Agent know about them?

The system needs mechanisms involving concepts such as:

```text
State
Context
Events
Agent communication/delegation
```

Without understanding these concepts, multi-agent systems can become difficult to reason about.

---

# 10. State vs Memory

You will often encounter terms such as:

```text
state
memory
session
context
history
```

These terms should not automatically be treated as interchangeable.

A useful simplified distinction is:

### Session

```text
"Which interaction are we in?"
```

### Events

```text
"What happened?"
```

### State

```text
"What information does the application currently maintain?"
```

### Context

```text
"What information is available during this execution?"
```

### Memory

```text
"What information should be retrievable beyond the immediate interaction?"
```

Memory becomes especially important when information needs to be retrieved across different sessions.

For example:

```text
Monday:
User discusses VLM research.

        ↓

Tuesday:
User starts another session.

        ↓

Agent retrieves relevant previous information.
```

Memory mechanisms are intentionally left for a later lesson rather than mixed into this one.

---

# 11. Think Like an AI Engineer

Consider a normal machine-learning pipeline:

```text
Input
 ↓
Preprocessing
 ↓
Model
 ↓
Postprocessing
 ↓
Output
```

An agent system is more dynamic:

```text
Input
 ↓
Agent
 ↓
Decision
 ↓
Action
 ↓
Observation
 ↓
Decision
 ↓
Action
 ↓
Observation
 ↓
...
 ↓
Output
```

A useful mental model is:

```text
Agent
  │
  ├── perception/context
  ├── decision
  ├── action/tool
  ├── observation
  └── next decision
```

The important transition is to stop thinking of an agent as simply:

```text
input → model → output
```

and start thinking in terms of an ongoing loop involving decisions, actions, observations, and context.

---

# 12. Lesson 5 Example Code

The accompanying Python example provides a small teaching implementation around these concepts.

It defines a session model containing:

```python
@dataclass
class ResearchSession:
    session_id: str
    state: dict[str, Any]
    events: list[str]
```

The session provides methods for maintaining state and recording events:

```python
session.set_state("user_name", "Amit")
```

and:

```python
session.add_event(
    'User provided their name: "Amit"'
)
```

The example tools demonstrate how application-maintained state can be used:

```text
remember_user_name()
        ↓
      STATE
        ↓
get_user_name()
```

It also records important actions as events.

The example then runs several requests within the same session, allowing you to observe how state and events accumulate during the interaction.

> **Important:** The Python session model in this lesson is a simplified teaching model of the concepts. It is intentionally kept easy to understand rather than introducing every ADK session/context API detail at once.

---

# 13. Exercise — Design a Research Assistant

The lesson's exercise is intentionally architectural rather than code-heavy.

Consider:

> **Build an AI research assistant that helps you investigate a research topic.**

Design these four things.

## Session

What constitutes one session?

For example:

```text
One research interaction with the assistant
```

---

## State

What information should the application maintain?

For example:

```text
topic
research_goal
papers_found
```

---

## Tools

What tools should the agent have?

For example:

```text
search_papers()
download_paper()
analyze_paper()
```

---

## Events

What important things might happen?

For example:

```text
User asks research question
Agent searches
Search returns papers
Agent analyzes paper
Agent generates summary
```

The objective is not to implement the complete research assistant yet.

The objective is to think about its architecture.

---

# 14. One Concept to Remember

If you remember only one thing from this lesson, remember:

```text
SESSION
   │
   ├── EVENTS → what happened
   │
   └── STATE  → what information we're maintaining
                  │
                  ↓
                CONTEXT
                  │
                  ↓
                AGENT
```

These concepts provide the foundation for understanding how an agent maintains continuity and how information moves through an agent execution.

---

# 15. Next Lesson

The next lesson moves from architecture to actually running and debugging an ADK agent.

### Lesson 6 — Running & Debugging ADK

The upcoming environment will look conceptually like:

```text
                     Your Computer
                          │
                     ADK Dev Server
                          │
                ┌─────────┴─────────┐
                ↓                   ↓
            Agent Code        Developer UI
                │                   │
                └─────────┬─────────┘
                          ↓
                        Gemini
                          ↓
                        Tools
```

The focus will be on:

- Sending messages to the agent
- Inspecting execution
- Seeing tool calls
- Running the agent through the ADK development environment

This moves the concepts from this lesson into an observable, running agent workflow.
