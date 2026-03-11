import os

import chainlit as cl
from dotenv import load_dotenv
from agents import Agent, Runner
from agents.lifecycle import AgentHooks
from agents.mcp import MCPServerSse
from agents.tool import Tool

load_dotenv()
cl.instrument_openai()

MCP_URL = os.getenv("MCP_URL", "http://localhost:5003")

mcp_server = MCPServerSse(params={"url": f"{MCP_URL}/sse", "timeout": 10})


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
    name="Recruiting Assistant",
    model=os.getenv("OPENAI_MODEL", "gpt-5.4"),
    instructions=(
        "You are a helpful recruiting assistant. Use the available tools to search for jobs, "
        "find candidates, score candidates against job descriptions, and shortlist candidates. "
        "Be concise and helpful."
    ),
    mcp_servers=[mcp_server],
    hooks=ReportSteps(),
)


@cl.on_chat_start
async def on_start():
    cl.user_session.set("history", [])
    await mcp_server.__aenter__()
    await cl.Message(content="Hi! I'm a recruiting assistant. Ask me about jobs or candidates.").send()


@cl.on_chat_end
async def on_end():
    await mcp_server.__aexit__(None, None, None)


@cl.on_message
async def on_message(message: cl.Message):
    history = cl.user_session.get("history") or []
    history.append({"role": "user", "content": message.content})

    result = await Runner.run(agent, history)
    cl.user_session.set("history", result.to_input_list())
    await cl.Message(content=result.final_output).send()
