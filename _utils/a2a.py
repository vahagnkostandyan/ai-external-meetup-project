import json

import httpx
from agents import Agent, Runner
from agents.stream_events import RunItemStreamEvent
from agents.items import ToolCallItem, ToolCallOutputItem
from a2a.client import ClientFactory, ClientConfig, create_text_message_object
from a2a.client.card_resolver import A2ACardResolver
from a2a.server.tasks.task_updater import TaskUpdater
from a2a.types import TaskStatusUpdateEvent, TaskState, Part, DataPart


def _format_json(raw) -> str:
    if isinstance(raw, dict) and raw.get("type") == "text":
        raw = raw["text"]
    try:
        return json.dumps(json.loads(raw) if isinstance(raw, str) else raw, indent=2)
    except (json.JSONDecodeError, TypeError, ValueError):
        return str(raw)


def _get(obj, key, default=None):
    return obj.get(key, default) if isinstance(obj, dict) else getattr(obj, key, default)


async def run_agent_streamed(agent: Agent, text: str, updater: TaskUpdater) -> str:
    """Run an OpenAI agent with streaming, emitting a DataPart per completed tool call."""
    result = Runner.run_streamed(agent, input=text)
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


async def stream_a2a(agent_url: str, query: str, on_tool_call=None) -> str:
    """Send a streaming A2A message. Calls on_tool_call(name, input, output) per tool, returns final text."""
    async with httpx.AsyncClient(timeout=60) as http:
        card = await A2ACardResolver(http, agent_url).get_agent_card()
        client = ClientFactory(ClientConfig(httpx_client=http)).create(card)
        final_text = ""
        async for event in client.send_message(create_text_message_object(content=query)):
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
