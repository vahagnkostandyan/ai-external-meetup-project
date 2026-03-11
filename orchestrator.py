import os

import chainlit as cl
from dotenv import load_dotenv
from agents import Agent, Runner
from _utils.a2a import discover_tools, stream_a2a

load_dotenv()
cl.instrument_openai()

AGENT_URLS = [
    url.strip()
    for url in os.getenv("AGENT_URLS").split(",")
    if url.strip()
]


async def _call_agent(agent_name: str, agent_url: str, query: str) -> str:
    async with cl.Step(name=agent_name, type="tool") as parent:
        parent.input = query

        async def on_tool(name, tool_input, tool_output):
            step = cl.Step(name=name, type="tool", parent_id=parent.id)
            step.input = f"```json\n{tool_input}\n```" if tool_input else ""
            step.output = f"```json\n{tool_output}\n```" if tool_output else ""
            await step.send()

        return await stream_a2a(agent_url, query, on_tool_call=on_tool)


@cl.on_chat_start
async def on_start():
    tools = await discover_tools(AGENT_URLS, wrap_call=_call_agent)

    agent = Agent(
        name="Orchestrator",
        model=os.getenv("OPENAI_MODEL", "gpt-5.4"),
        instructions=(
            "You are a fully autonomous assistant with access to specialized agents. "
            "Act decisively — never ask the user for confirmation, clarification, or permission before proceeding. "
            "Execute the full task end-to-end on your own. Only message the user if you are truly blocked "
            "(e.g. missing credentials, ambiguous critical choice with no reasonable default). "
            "You can call multiple agents in sequence. Synthesize results clearly. "
            "When a user uploads a resume/CV, include the resume path so the browser agent can use it when applying to jobs. "
            "When in doubt, make reasonable assumptions and proceed rather than asking."
        ),
        tools=tools,
    )

    cl.user_session.set("agent", agent)
    cl.user_session.set("history", [])
    await cl.Message(content="Hi! I'm GPT-5.4. How can I help you today?").send()


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
