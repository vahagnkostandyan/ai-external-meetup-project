import os

import httpx
import chainlit as cl
from dotenv import load_dotenv
from agents import Agent, Runner, function_tool
from _utils.a2a import stream_a2a
from a2a.client.card_resolver import A2ACardResolver

load_dotenv()
cl.instrument_openai()

AGENT_URLS = [
    url.strip()
    for url in os.getenv("AGENT_URLS").split(",")
    if url.strip()
]


async def _call_agent(url: str, query: str, parent: cl.Step) -> str:
    parent.input = query

    async def on_tool(name, tool_input, tool_output):
        step = cl.Step(name=name, type="tool", parent_id=parent.id)
        step.input = f"```json\n{tool_input}\n```" if tool_input else ""
        step.output = f"```json\n{tool_output}\n```" if tool_output else ""
        await step.send()

    return await stream_a2a(url, query, on_tool_call=on_tool)


async def discover_agents(urls: list[str]):
    """Fetch AgentCards from all configured sub-agent URLs via A2A discovery."""
    cards = []
    async with httpx.AsyncClient(timeout=10) as http:
        for url in urls:
            try:
                card = await A2ACardResolver(http, url).get_agent_card()
                cards.append(card)
            except Exception as e:
                print(f"[discovery] Could not reach {url}: {e}")
    return cards


def make_tool(card):
    """Create a function_tool dynamically from a discovered AgentCard."""
    agent_url = str(card.url)
    agent_name = card.name
    skills = "; ".join(f"{s.name}: {s.description}" for s in (card.skills or []))
    description = f"{card.description} Skills: {skills}" if skills else card.description
    tool_name = f"ask_{agent_name.lower().replace(' ', '_')}"

    async def call(query: str) -> str:
        async with cl.Step(name=agent_name, type="tool") as step:
            return await _call_agent(agent_url, query, step)

    return function_tool(call, name_override=tool_name, description_override=description)


def build_instructions(cards):
    """Assemble the orchestrator system prompt from discovered agent cards."""
    agent_lines = []
    for card in cards:
        skills = ", ".join(s.name for s in (card.skills or []))
        agent_lines.append(f"- {card.name}: {card.description} (skills: {skills})")
    agents_info = "\n".join(agent_lines) if agent_lines else "No agents discovered."

    return (
        "You are a fully autonomous assistant with access to specialized agents.\n"
        "Act decisively — never ask the user for confirmation, clarification, or permission before proceeding.\n"
        "Execute the full task end-to-end on your own. Only message the user if you are truly blocked "
        "(e.g. missing credentials, ambiguous critical choice with no reasonable default).\n"
        "You can call multiple agents in sequence. Synthesize results clearly.\n"
        "When a user uploads a resume/CV, include the resume path so the browser agent can use it when applying to jobs.\n"
        "When in doubt, make reasonable assumptions and proceed rather than asking.\n\n"
        f"Available agents:\n{agents_info}"
    )


@cl.on_chat_start
async def on_start():
    cards = await discover_agents(AGENT_URLS)
    tools = [make_tool(card) for card in cards]

    agent = Agent(
        name="Orchestrator",
        model=os.getenv("OPENAI_MODEL", "gpt-5.4"),
        instructions=build_instructions(cards),
        tools=tools,
    )

    cl.user_session.set("agent", agent)
    cl.user_session.set("history", [])

    names = ", ".join(c.name for c in cards)
    await cl.Message(
        content=f"Hi! I discovered **{len(cards)}** agent(s): {names}. How can I help you today?"
    ).send()


@cl.on_message
async def on_message(message: cl.Message):
    if message.elements:
        cl.user_session.set("cv_path", message.elements[0].path)
        await cl.Message(content=f"Resume uploaded: **{message.elements[0].name}**").send()

    text = message.content or ""
    cv_path = cl.user_session.get("cv_path")
    if cv_path:
        text += f"\n[Resume on file: {cv_path}]"

    if not text.strip():
        return

    history = cl.user_session.get("history") or []
    history.append({"role": "user", "content": text})

    agent = cl.user_session.get("agent")
    result = await Runner.run(agent, history)
    cl.user_session.set("history", result.to_input_list())
    await cl.Message(content=result.final_output).send()
