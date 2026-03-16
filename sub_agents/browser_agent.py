import asyncio
import base64
import os
import sys
import tempfile

import uvicorn
from dotenv import load_dotenv
from agents import Agent
from agents.mcp import MCPServerStdio

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _utils.a2a import run_agent_streamed

from a2a.server.agent_execution import AgentExecutor
from a2a.server.agent_execution.context import RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.server.tasks.task_updater import TaskUpdater
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.server.apps.jsonrpc.starlette_app import A2AStarletteApplication
from a2a.types import AgentCard, AgentCapabilities, AgentSkill, Part, TextPart, FilePart

load_dotenv()

AGENT_HOST = "0.0.0.0"
AGENT_PORT = 5002

mcp_server = MCPServerStdio(
    name="Chrome DevTools",
    params={
        "command": "node",
        "args": ["node_modules/.bin/chrome-devtools-mcp"],
    },
    cache_tools_list=True,
    client_session_timeout_seconds=60,
    max_retry_attempts=3,
)

agent = Agent(
    name="Browser Agent",
    model=os.getenv("OPENAI_MODEL", "gpt-5.4"),
    instructions=(
        "You are a fully autonomous browser automation agent using Chrome DevTools to apply to jobs on behalf of candidates.\n"
        "Never ask for confirmation or permission — execute the full task end-to-end without pausing.\n"
        "Make reasonable assumptions when details are missing. Only ask if you are truly blocked.\n"
        "Workflow:\n"
        "1. Use navigate_page to go to the application URL.\n"
        "2. Use take_snapshot to get the page structure and element uids.\n"
        "3. Use fill or fill_form to populate form fields by uid.\n"
        "4. Use upload_file to attach the candidate's resume.\n"
        "5. Use click to submit the form.\n"
        "6. Use wait_for or take_snapshot to confirm submission.\n"
        "Always take a snapshot before interacting with elements. Be concise and report the result."
    ),
    mcp_servers=[mcp_server],
)


def _extract_file(context: RequestContext) -> str | None:
    """If the A2A message contains a FilePart, decode it to a temp file and return the path."""
    if not context.message:
        return None
    for part in context.message.parts:
        if isinstance(part.root, FilePart) and hasattr(part.root.file, "bytes"):
            fp = part.root.file
            suffix = os.path.splitext(fp.name)[1] if fp.name else ""
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix, prefix="resume_")
            tmp.write(base64.b64decode(fp.bytes))
            tmp.close()
            return tmp.name
    return None


class BrowserExecutor(AgentExecutor):

    async def execute(self, context: RequestContext, event_queue: EventQueue):
        updater = TaskUpdater(event_queue, context.task_id, context.context_id)
        await updater.start_work(message=updater.new_agent_message(
            parts=[Part(root=TextPart(text="Starting browser automation..."))]
        ))

        user_input = context.get_user_input()
        file_path = _extract_file(context)
        if file_path:
            user_input += f"\n[Resume file available at: {file_path}]"

        try:
            async with mcp_server:
                answer = await run_agent_streamed(agent, user_input, updater, max_turns=100)
        except Exception as e:
            answer = f"Browser automation failed: {e}"

        await updater.complete(message=updater.new_agent_message(
            parts=[Part(root=TextPart(text=answer))]
        ))

    async def cancel(self, context: RequestContext, event_queue: EventQueue):
        updater = TaskUpdater(event_queue, context.task_id, context.context_id)
        await updater.cancel()


agent_card = AgentCard(
    name="Browser Agent",
    description="Automates real browser interactions via Chrome DevTools to apply to jobs on behalf of candidates. Navigates pages, fills forms, uploads resumes, and submits applications.",
    url=f"http://localhost:{AGENT_PORT}",
    version="1.0.0",
    capabilities=AgentCapabilities(streaming=True),
    default_input_modes=["text/plain"],
    default_output_modes=["text/plain"],
    skills=[AgentSkill(
        id="apply-to-job",
        name="Apply to Job",
        description="Automates the job application process using a real browser via Chrome DevTools MCP — navigates pages, fills forms, uploads resumes, and submits.",
        tags=["browser", "apply", "automation", "chrome-devtools"],
    )],
)

handler = DefaultRequestHandler(
    agent_executor=BrowserExecutor(),
    task_store=InMemoryTaskStore(),
)

app = A2AStarletteApplication(agent_card=agent_card, http_handler=handler).build()

async def main():
    config = uvicorn.Config(app, host=AGENT_HOST, port=AGENT_PORT)
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    asyncio.run(main())
