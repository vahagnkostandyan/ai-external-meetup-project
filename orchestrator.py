import os

import chainlit as cl
from dotenv import load_dotenv
from agents import Agent, Runner, function_tool
from _utils.a2a import stream_a2a

load_dotenv()
cl.instrument_openai()

RECRUITING_URL = os.getenv("RECRUITING_AGENT_URL", "http://localhost:5001")
BROWSER_URL = os.getenv("BROWSER_AGENT_URL", "http://localhost:5002")


async def _call_agent(url: str, query: str, parent: cl.Step) -> str:
    parent.input = query

    async def on_tool(name, tool_input, tool_output):
        step = cl.Step(name=name, type="tool", parent_id=parent.id)
        step.input = f"```json\n{tool_input}\n```" if tool_input else ""
        step.output = f"```json\n{tool_output}\n```" if tool_output else ""
        await step.send()

    return await stream_a2a(url, query, on_tool_call=on_tool)


@function_tool
async def ask_recruiting_agent(query: str) -> str:
    """Searches jobs and candidates, scores and shortlists candidates using MCP tools."""
    async with cl.Step(name="Recruiting Agent", type="tool") as step:
        return await _call_agent(RECRUITING_URL, query, step)


@function_tool
async def ask_browser_agent(query: str) -> str:
    """Controls a real Chrome browser via Chrome DevTools. Use for any browser task: navigating to URLs, filling forms, clicking buttons, reading page content, applying to jobs, or general web browsing."""
    async with cl.Step(name="Browser Agent", type="tool") as step:
        return await _call_agent(BROWSER_URL, query, step)


orchestrator = Agent(
    name="Orchestrator",
    model=os.getenv("OPENAI_MODEL", "gpt-5.4"),
    instructions=(
        "You are a fully autonomous assistant with access to specialized agents. "
        "Act decisively — never ask the user for confirmation, clarification, or permission before proceeding. "
        "Execute the full task end-to-end on your own. Only message the user if you are truly blocked "
        "(e.g. missing credentials, ambiguous critical choice with no reasonable default). "
        "Delegate recruiting tasks (job search, candidate scoring, shortlisting) to the recruiting agent. "
        "Delegate ANY browser task to the browser agent — it controls a real Chrome browser and can navigate to URLs, "
        "read page content, fill forms, click buttons, upload files, and apply to jobs. "
        "Always prefer using the browser agent when the user asks to open a website, look something up on the web, "
        "or interact with any web page. You can call multiple agents in sequence. Synthesize results clearly. "
        "When a user uploads a resume/CV, include the resume path so the browser agent can use it when applying to jobs. "
        "When in doubt, make reasonable assumptions and proceed rather than asking."
    ),
    tools=[ask_recruiting_agent, ask_browser_agent],
)


@cl.on_chat_start
async def on_start():
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

    result = await Runner.run(orchestrator, history)
    cl.user_session.set("history", result.to_input_list())
    await cl.Message(content=result.final_output).send()
