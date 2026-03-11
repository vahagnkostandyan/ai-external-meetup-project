.PHONY: install run run-simple run-mcp run-recruiting run-browser run-orchestrator stop

PIDS_FILE := .running_pids
PORTS := 5001 5002 5003 8000

install:
	pip install -r requirements.txt

run: stop
	@echo "Starting A2A Workshop Demo..."
	@echo ""
	@> $(PIDS_FILE)

	@echo "[1/4] MCP Server        → http://localhost:5003"
	@python mcp_servers/recruiting_server.py &  echo $$! >> $(PIDS_FILE)
	@sleep 1

	@echo "[2/4] Recruiting Agent  → http://localhost:5001"
	@python sub_agents/recruiting_agent.py &  echo $$! >> $(PIDS_FILE)
	@sleep 1

	@echo "[3/4] Browser Agent     → http://localhost:5002"
	@python sub_agents/browser_agent.py &  echo $$! >> $(PIDS_FILE)
	@sleep 1

	@echo "[4/4] Orchestrator UI   → http://localhost:8000"
	@echo ""
	@echo "All services running. Use 'make stop' to shut down."
	@echo ""
	chainlit run orchestrator.py --port 8000

run-simple:
	@echo "Starting Simple Agent → http://localhost:8000"
	chainlit run simple_agent.py --port 8000

run-mcp:
	@echo "Starting MCP Server → http://localhost:5003"
	python mcp_servers/recruiting_server.py

run-recruiting:
	@echo "Starting MCP Server        → http://localhost:5003"
	@python mcp_servers/recruiting_server.py &  echo $$! > $(PIDS_FILE)
	@sleep 1
	@echo "Starting Recruiting Agent  → http://localhost:5001"
	python sub_agents/recruiting_agent.py

run-browser:
	@echo "Starting Browser Agent → http://localhost:5002"
	python sub_agents/browser_agent.py

run-orchestrator:
	@echo "Starting Orchestrator UI → http://localhost:8000"
	chainlit run orchestrator.py --port 8000

stop:
	@echo "Stopping services..."
	@if [ -f $(PIDS_FILE) ]; then \
		while read pid; do kill $$pid 2>/dev/null || true; done < $(PIDS_FILE); \
		rm -f $(PIDS_FILE); \
	fi
	@for port in $(PORTS); do \
		lsof -ti:$$port 2>/dev/null | xargs kill 2>/dev/null || true; \
	done
	@echo "Stopped."
