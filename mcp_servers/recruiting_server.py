import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp.server.fastmcp import FastMCP
from _utils import mock_data

mcp = FastMCP("Recruiting Tools", host="0.0.0.0", port=5003)


@mcp.tool()
def search_jobs(query: str = "", location: str = "", limit: int = 5) -> dict:
    """Search for job postings by keyword, title, or tech stack. Returns matching jobs ranked by relevance."""
    return mock_data.search_jobs(query=query, location=location, limit=limit)


@mcp.tool()
def search_candidates(skills: str = "", location: str = "", limit: int = 5) -> dict:
    """Search for candidates by skills and location. Skills should be comma-separated (e.g. 'python,fastapi,aws')."""
    skill_list = [s.strip() for s in skills.split(",") if s.strip()]
    return mock_data.search_candidates(skills=skill_list, location=location, limit=limit)


@mcp.tool()
def score_candidate(candidate_id: str = "", job_description: str = "") -> dict:
    """Score a candidate against a job description. Returns a numeric fit score and reasoning."""
    return mock_data.score_candidate(candidate_id=candidate_id, job_description=job_description)


@mcp.tool()
def shortlist_candidate(candidate_id: str = "", reason: str = "") -> dict:
    """Add a candidate to the shortlist with a reason for the selection."""
    return mock_data.shortlist_candidate(candidate_id=candidate_id, reason=reason)


@mcp.tool()
def apply_to_job(candidate_id: str = "", job_id: str = "") -> dict:
    """Prepare an application task for a candidate to apply to a specific job."""
    return mock_data.apply_to_job(candidate_id=candidate_id, job_id=job_id)


if __name__ == "__main__":
    mcp.run(transport="sse")
