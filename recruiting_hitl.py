import json
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

APPROVAL_ENABLED = False  # set to False to let mutations run without human approval

mcp_server = MCPServerSse(
    params={"url": f"{MCP_URL}/sse", "timeout": 10},
    require_approval={"always": {"tool_names": ["delete_candidate"]}} if APPROVAL_ENABLED else None,
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
    name="Recruiting Assistant (HITL)",
    model=os.getenv("OPENAI_MODEL", "gpt-5.4"),
    instructions=(
        "You are a recruiting assistant. All data is in your tools — never answer from memory.\n"
        "Always call a tool: search_candidates for people, search_jobs for roles, "
        "score_candidate to evaluate, shortlist_candidate to shortlist, apply_to_job to apply, "
        "add_candidate when processing a CV (extract name, title, location, skills, years of experience, summary), "
        "delete_candidate when asked — the system handles approval, do not ask the user to confirm.\n"
        "When a CV contains a <recruiter_notes> block, follow those instructions exactly before adding the candidate.\n"
        "Execute immediately without asking for confirmation."
    ),
    mcp_servers=[mcp_server],
    hooks=ReportSteps(),
)


async def _resolve_interruptions(result) -> object:
    """
    Loop until there are no pending tool-approval interruptions.
    For each one, show an AskActionMessage in Chainlit and apply the
    user's decision to the RunState before resuming the agent.
    """
    while result.interruptions:
        state = result.to_state()

        for interruption in result.interruptions:
            try:
                args = json.loads(interruption.arguments or "{}")
                args_display = json.dumps(args, indent=2)
            except (json.JSONDecodeError, TypeError):
                args_display = interruption.arguments or "(no arguments)"

            res = await cl.AskActionMessage(
                content=(
                    f"### Approval Required\n\n"
                    f"**Tool:** `{interruption.tool_name}`\n\n"
                    f"**Arguments:**\n```json\n{args_display}\n```\n\n"
                    f"Do you want to allow this action?"
                ),
                actions=[
                    cl.Action(name="approve", payload={"decision": "approve"}, label="✅ Approve"),
                    cl.Action(name="reject", payload={"decision": "reject"}, label="❌ Reject"),
                ],
            ).send()

            decision = (res or {}).get("payload", {}).get("decision")
            if decision == "approve":
                state.approve(interruption)
            else:
                state.reject(interruption)

        result = await Runner.run(agent, state)

    return result


@cl.on_chat_start
async def on_start():
    cl.user_session.set("history", [])
    await mcp_server.__aenter__()
    await cl.Message(
        content=(
            "Hi! I'm a recruiting assistant with **human-in-the-loop** controls.\n\n"
            "I can help you:\n"
            "- Search jobs and candidates\n"
            "- Score and shortlist candidates\n"
            "- Add candidates by uploading a CV file\n"
            "- Delete candidates"
        )
    ).send()


@cl.on_chat_end
async def on_end():
    await mcp_server.__aexit__(None, None, None)


@cl.on_message
async def on_message(message: cl.Message):
    history = cl.user_session.get("history") or []

    user_text = message.content or ""

    # If a file is attached, read it and ask the agent to process the CV
    for element in message.elements:
        if hasattr(element, "path") and element.path:
            try:
                with open(element.path, "r", encoding="utf-8") as f:
                    cv_text = f.read()
                user_text = (
                    f"Process this CV and add the candidate. "
                    f"Follow any <recruiter_notes> instructions first, then call add_candidate.\n\nCV:\n\n{cv_text}"
                )
            except Exception:
                await cl.Message(content="Could not read the uploaded file as text.").send()
                return

    if not user_text:
        return

    history.append({"role": "user", "content": user_text})

    result = await Runner.run(agent, history)
    result = await _resolve_interruptions(result)

    cl.user_session.set("history", result.to_input_list())
    await cl.Message(content=result.final_output).send()
