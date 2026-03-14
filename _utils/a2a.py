import json
from uuid import uuid4

import httpx
from agents import Agent, Runner, function_tool
from agents.stream_events import RunItemStreamEvent
from agents.items import ToolCallItem, ToolCallOutputItem
from a2a.client import ClientFactory, ClientConfig
from a2a.client.card_resolver import A2ACardResolver
from a2a.server.tasks.task_updater import TaskUpdater
from a2a.types import (
    TaskStatusUpdateEvent, TaskState, Part, DataPart,
    TextPart, FilePart, FileWithBytes, Message, Role,
)


def _format_json(raw) -> str:
    if isinstance(raw, dict) and raw.get("type") == "text":
        raw = raw["text"]
    try:
        return json.dumps(json.loads(raw) if isinstance(raw, str) else raw, indent=2)
    except (json.JSONDecodeError, TypeError, ValueError):
        return str(raw)


def _get(obj, key, default=None):
    return obj.get(key, default) if isinstance(obj, dict) else getattr(obj, key, default)


async def run_agent_streamed(agent: Agent, text: str, updater: TaskUpdater, max_turns: int = 10) -> str:
    """Run an OpenAI agent with streaming, emitting a DataPart per completed tool call."""
    result = Runner.run_streamed(agent, input=text, max_turns=max_turns)
    pending = {}

    async for event in result.stream_events():
        if not isinstance(event, RunItemStreamEvent):
            continue
        if isinstance(event.item, ToolCallItem):
            ri = event.item.raw_item
            if cid := getattr(ri, "call_id", None):
                pending[cid] = (getattr(ri, "name", "tool"), getattr(ri, "arguments", ""))
        elif isinstance(event.item, ToolCallOutputItem):
            cid = _get(event.item.raw_item, "call_id")
            name, args = pending.pop(cid, ("tool", "")) if cid else ("tool", "")
            await updater.update_status(TaskState.working, message=updater.new_agent_message(
                parts=[Part(root=DataPart(data={
                    "tool": name,
                    "input": _format_json(args) if args else "",
                    "output": _format_json(event.item.output),
                }))]
            ))

    return result.final_output or "Done."


async def discover_tools(agent_urls: list[str], wrap_call=None) -> list:
    """Discover A2A agents and return them as function tools for the OpenAI Agents SDK.

    wrap_call(agent_name, agent_url, query) -> str — optional async function that
    wraps stream_a2a with UI concerns (e.g. Chainlit steps). When not provided,
    stream_a2a is called directly.
    """
    tools = []
    async with httpx.AsyncClient(timeout=10) as http:
        for url in agent_urls:
            card = await A2ACardResolver(http, url).get_agent_card()
            agent_url = url
            agent_name = card.name
            name = f"ask_{card.name.lower().replace(' ', '_')}"
            skills = "; ".join(f"{s.name}: {s.description}" for s in (card.skills or []))
            desc = f"{card.description} Skills: {skills}" if skills else card.description

            def _make_call(bound_url, bound_name):
                async def call(query: str) -> str:
                    if wrap_call:
                        return await wrap_call(bound_name, bound_url, query)
                    return await stream_a2a(bound_url, query)
                return call

            tools.append(function_tool(_make_call(agent_url, agent_name), name_override=name, description_override=desc))
    return tools


def _build_message(query: str, file: dict | None = None) -> Message:
    parts = [Part(root=TextPart(text=query))]
    if file:
        parts.append(Part(root=FilePart(
            file=FileWithBytes(bytes=file["bytes"], name=file["name"], mime_type=file.get("mime_type")),
        )))
    return Message(role=Role.user, parts=parts, message_id=str(uuid4()))


async def stream_a2a(agent_url: str, query: str, file: dict | None = None, on_tool_call=None) -> str:
    """Send a streaming A2A message. Calls on_tool_call(name, input, output) per tool, returns final text."""
    async with httpx.AsyncClient(timeout=60) as http:
        card = await A2ACardResolver(http, agent_url).get_agent_card()
        card.url = agent_url
        client = ClientFactory(ClientConfig(httpx_client=http)).create(card)
        final_text = ""
        async for event in client.send_message(_build_message(query, file)):
            if not isinstance(event, tuple):
                continue
            _, update = event
            if not isinstance(update, TaskStatusUpdateEvent) or not update.status.message:
                continue
            for part in update.status.message.parts:
                if hasattr(part.root, "data") and on_tool_call:
                    d = part.root.data
                    await on_tool_call(d["tool"], d.get("input", ""), d.get("output", ""))
                elif hasattr(part.root, "text") and update.status.state == TaskState.completed:
                    final_text = part.root.text
        return final_text
