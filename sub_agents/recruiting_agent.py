import os
import sys

import uvicorn
from dotenv import load_dotenv
from agents import Agent
from agents.mcp import MCPServerSse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _utils.a2a import run_agent_streamed

from a2a.server.agent_execution import AgentExecutor
from a2a.server.agent_execution.context import RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.server.tasks.task_updater import TaskUpdater
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.server.apps.jsonrpc.starlette_app import A2AStarletteApplication
from a2a.types import AgentCard, AgentCapabilities, AgentSkill, Part, TextPart

load_dotenv()

MCP_URL = os.getenv("MCP_URL", "http://localhost:5003")
AGENT_HOST = "0.0.0.0"
AGENT_PORT = 5001

SYSTEM_PROMPT = (
    "You are a fully autonomous recruiting assistant. All data is in your tools — never answer from memory.\n"
    "Always call a tool: search_candidates for people, search_jobs for roles, "
    "score_candidate to evaluate, shortlist_candidate to shortlist, apply_to_job to apply.\n"
    "Execute end-to-end without asking for confirmation. Make reasonable assumptions when details are missing."
)


class RecruitingExecutor(AgentExecutor):

    async def execute(self, context: RequestContext, event_queue: EventQueue):
        updater = TaskUpdater(event_queue, context.task_id, context.context_id)
        await updater.start_work(message=updater.new_agent_message(
            parts=[Part(root=TextPart(text="Connecting to recruiting tools..."))]
        ))

        async with MCPServerSse(params={"url": f"{MCP_URL}/sse", "timeout": 10}) as server:
            agent = Agent(
                name="Recruiting Agent",
                model=os.getenv("OPENAI_MODEL", "gpt-5.4"),
                instructions=SYSTEM_PROMPT,
                mcp_servers=[server],
            )
            answer = await run_agent_streamed(agent, context.get_user_input(), updater)

        await updater.complete(message=updater.new_agent_message(
            parts=[Part(root=TextPart(text=answer))]
        ))

    async def cancel(self, context: RequestContext, event_queue: EventQueue):
        updater = TaskUpdater(event_queue, context.task_id, context.context_id)
        await updater.cancel()


agent_card = AgentCard(
    name="Recruiting Agent",
    description="Search for job postings by keyword, title, location, or tech stack. Find candidates and talent by skills and location. Score and rank candidates against job descriptions. Shortlist candidates. Prepare job application tasks.",
    url=f"http://localhost:{AGENT_PORT}",
    version="1.0.0",
    capabilities=AgentCapabilities(streaming=True),
    default_input_modes=["text/plain"],
    default_output_modes=["text/plain"],
    skills=[
        AgentSkill(id="search-jobs", name="Search Jobs", description="Search job postings by keyword, title, or tech stack.", tags=["jobs", "search"]),
        AgentSkill(id="search-candidates", name="Search Candidates", description="Find candidates by skills and location.", tags=["candidates", "search"]),
        AgentSkill(id="score-candidate", name="Score Candidate", description="Score a candidate's fit against a job description.", tags=["candidates", "scoring"]),
        AgentSkill(id="shortlist", name="Shortlist Candidate", description="Add a candidate to the shortlist.", tags=["candidates", "shortlist"]),
        AgentSkill(id="apply", name="Prepare Application", description="Prepare an application task for a candidate.", tags=["apply"]),
    ],
)

handler = DefaultRequestHandler(
    agent_executor=RecruitingExecutor(),
    task_store=InMemoryTaskStore(),
)

app = A2AStarletteApplication(agent_card=agent_card, http_handler=handler).build()

if __name__ == "__main__":
    uvicorn.run(app, host=AGENT_HOST, port=AGENT_PORT)
