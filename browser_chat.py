import os

import chainlit as cl
from dotenv import load_dotenv
from agents import Agent, Runner
from agents.lifecycle import AgentHooks
from agents.mcp import MCPServerStdio
from agents.tool import Tool

load_dotenv()
cl.instrument_openai()

mcp_server = MCPServerStdio(
    name="Chrome DevTools",
    params={
        "command": "npx",
        "args": ["chrome-devtools-mcp@latest"],
    },
    cache_tools_list=True,
)


class ReportSteps(AgentHooks):
    async def on_tool_start(self, context, agent, tool: Tool):
        step = cl.Step(name=tool.name, type="tool")
        step.input = f"```json\n{context.tool_arguments}\n```"
        cl.user_session.set(f"step:{context.tool_call_id}", step)
        await step.__aenter__()

    async def on_tool_end(self, context, agent, tool: Tool, result: str):
        step = cl.user_session.get(f"step:{context.tool_call_id}")
        if step:
            if isinstance(result, dict) and "text" in result:
                result = result["text"]
            step.output = f"```json\n{result}\n```"
            await step.__aexit__(None, None, None)


agent = Agent(
    name="Browser Agent",
    model=os.getenv("OPENAI_MODEL", "gpt-5.4"),
    instructions=(
        "You are a fully autonomous browser automation agent with access to a real Chrome browser via DevTools.\n"
        "You can navigate websites, read page content, interact with elements, fill forms, click buttons, "
        "and extract information from any web page.\n"
        "Never ask for confirmation or permission — execute the full task end-to-end.\n"
        "Make reasonable assumptions when details are missing. Only ask if you are truly blocked.\n\n"
        "General workflow:\n"
        "1. Use navigate_page to open a URL.\n"
        "2. Use take_snapshot to understand the current page structure and element uids.\n"
        "3. Use click, fill, or other interaction tools to work with elements by uid.\n"
        "4. Always take a snapshot before interacting with elements so you have current uids.\n"
        "5. Report results concisely after completing each step.\n\n"
        "You can handle tasks like:\n"
        "- Navigating to websites and reading content\n"
        "- Filling out and submitting forms\n"
        "- Clicking links and buttons\n"
        "- Extracting text, data, or information from pages\n"
        "- Taking snapshots of page state\n"
        "- Multi-step workflows across pages"
    ),
    mcp_servers=[mcp_server],
    hooks=ReportSteps(),
)


@cl.on_chat_start
async def on_start():
    cl.user_session.set("history", [])
    await mcp_server.__aenter__()
    await cl.Message(content="Hi! I'm a browser automation agent. Tell me what to do in Chrome.").send()


@cl.on_chat_end
async def on_end():
    await mcp_server.__aexit__(None, None, None)


@cl.on_message
async def on_message(message: cl.Message):
    history = cl.user_session.get("history") or []
    history.append({"role": "user", "content": message.content})

    result = await Runner.run(agent, history, max_turns=50)
    cl.user_session.set("history", result.to_input_list())
    await cl.Message(content=result.final_output).send()
