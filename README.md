# A2A Workshop Demo

Agent-to-Agent (A2A) system with an orchestrator, sub-agents, and MCP tools.

## Architecture

```
User (Browser)
     │
     ▼
┌─────────────────────────────┐
│  Orchestrator (port 8000)   │
│  Chainlit UI + AI Router    │
└──────────┬──────────────────┘
           │  A2A protocol
     ┌─────┴──────┐
     ▼            ▼
┌──────────┐  ┌──────────────┐
│Recruiting│  │Browser Agent │
│  Agent   │  │   (5002)     │
│ (5001)   │  └──────┬───────┘
└────┬─────┘         │ MCP (stdio)
     │ MCP           ▼
     ▼          ┌──────────────┐
┌──────────┐   │chrome-devtools│
│MCP Server│   │    -mcp       │
│ (5003)   │   └──────┬───────┘
└──────────┘          │ CDP
                      ▼
                 ┌─────────┐
                 │ Chrome  │
                 └─────────┘
```

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
# Fill in your OPENAI_API_KEY
```

## Run

```bash
make run
```

Opens the chat UI at http://localhost:8000.

## Stop

```bash
make stop
```

## Project Structure

```
orchestrator.py                 # Chat UI + agent routing (auto-discovers sub-agents)
sub_agents/
  recruiting_agent.py           # Sub-agent with MCP tools (job search, candidates)
  browser_agent.py              # Sub-agent with Chrome DevTools MCP (real browser)
mcp_servers/
  recruiting_server.py          # MCP server with 5 recruiting tools
_utils/
  a2a.py                        # A2A utilities (discovery, streaming, tool bridging)
  mock_data.py                  # Mock candidates & jobs data
```
