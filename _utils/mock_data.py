from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher
import os
import re
from typing import Any
from uuid import NAMESPACE_URL, uuid5

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@dataclass(frozen=True)
class Candidate:
    id: str
    name: str
    title: str
    location: str
    skills: tuple[str, ...]
    years_experience: int
    resume_url: str
    summary: str


@dataclass(frozen=True)
class JobPosting:
    id: str
    title: str
    company: str
    location: str
    skills: tuple[str, ...]
    employment_type: str
    apply_url: str
    summary: str


CANDIDATES: tuple[Candidate, ...] = (
    Candidate(
        id="cand-001",
        name="Ava Martinez",
        title="Senior Backend Engineer",
        location="Remote-US",
        skills=("python", "fastapi", "sqlalchemy", "aws", "docker"),
        years_experience=8,
        resume_url="https://example.com/resumes/cand-001.pdf",
        summary="Builds resilient Python APIs with cloud-native delivery.",
    ),
    Candidate(
        id="cand-002",
        name="Noah Kim",
        title="Staff Full-Stack Engineer",
        location="San Francisco, CA",
        skills=("python", "typescript", "react", "postgres", "kubernetes"),
        years_experience=10,
        resume_url="https://example.com/resumes/cand-002.pdf",
        summary="Leads hiring-scale platforms and full-stack architecture.",
    ),
    Candidate(
        id="cand-003",
        name="Liam O'Brien",
        title="Machine Learning Engineer",
        location="Remote-US",
        skills=("python", "pytorch", "airflow", "fastapi", "mlops"),
        years_experience=6,
        resume_url="https://example.com/resumes/cand-003.pdf",
        summary="Delivers ML-powered ranking services and evaluation pipelines.",
    ),
    Candidate(
        id="cand-004",
        name="Sophia Patel",
        title="Platform Engineer",
        location="Austin, TX",
        skills=("go", "python", "terraform", "aws", "observability"),
        years_experience=7,
        resume_url="https://example.com/resumes/cand-004.pdf",
        summary="Automates platform operations with reliability-first practices.",
    ),
    Candidate(
        id="cand-005",
        name="Ethan Johnson",
        title="Data Engineer",
        location="New York, NY",
        skills=("python", "spark", "dbt", "sql", "airflow"),
        years_experience=5,
        resume_url="https://example.com/resumes/cand-005.pdf",
        summary="Builds clean data models and high-throughput pipelines.",
    ),
    Candidate(
        id="cand-006",
        name="Mia Chen",
        title="Site Reliability Engineer",
        location="Seattle, WA",
        skills=("go", "python", "kubernetes", "terraform", "observability"),
        years_experience=9,
        resume_url="https://example.com/resumes/cand-006.pdf",
        summary="Improves system reliability with automation, metrics, and incident response.",
    ),
    Candidate(
        id="cand-007",
        name="Daniel Rivera",
        title="Frontend Engineer",
        location="Los Angeles, CA",
        skills=("react", "typescript", "graphql", "nodejs", "css"),
        years_experience=6,
        resume_url="https://example.com/resumes/cand-007.pdf",
        summary="Builds performant web interfaces and partners closely with design teams.",
    ),
    Candidate(
        id="cand-008",
        name="Priya Nair",
        title="Cloud Security Engineer",
        location="Remote-US",
        skills=("python", "aws", "security", "iam", "go"),
        years_experience=8,
        resume_url="https://example.com/resumes/cand-008.pdf",
        summary="Hardens cloud infrastructure and implements secure-by-default workflows.",
    ),
    Candidate(
        id="cand-009",
        name="Lucas Brown",
        title="DevOps Engineer",
        location="Denver, CO",
        skills=("docker", "kubernetes", "terraform", "aws", "jenkins"),
        years_experience=7,
        resume_url="https://example.com/resumes/cand-009.pdf",
        summary="Builds CI/CD and infrastructure automation for fast, reliable releases.",
    ),
    Candidate(
        id="cand-010",
        name="Grace Wilson",
        title="QA Automation Engineer",
        location="Boston, MA",
        skills=("python", "playwright", "selenium", "api", "testing"),
        years_experience=5,
        resume_url="https://example.com/resumes/cand-010.pdf",
        summary="Leads test automation strategy across API and end-to-end product flows.",
    ),
    Candidate(
        id="cand-011",
        name="Aram Vardanyan",
        title="Agentic AI Engineer",
        location="Remote-US",
        skills=("python", "llm", "langchain", "fastapi", "mlops"),
        years_experience=8,
        resume_url=os.path.join(_REPO_ROOT, "samples", "aram_vardanyan_cv.pdf"),
        summary="Designs and builds autonomous AI agents, multi-agent orchestration systems, and LLM-powered workflows.",
    ),
)

JOB_POSTINGS: tuple[JobPosting, ...] = (
    JobPosting(
        id="job-001",
        title="Node.js Backend Engineer",
        company="Atlas Payments",
        location="Remote-US",
        skills=("nodejs", "typescript", "postgres", "aws"),
        employment_type="Full-time",
        apply_url="https://jobs.example.com/openings/job-001",
        summary="Build APIs and payment orchestration services with Node.js.",
    ),
    JobPosting(
        id="job-002",
        title="Senior JavaScript Platform Engineer",
        company="Northstar Cloud",
        location="Austin, TX",
        skills=("javascript", "nodejs", "kubernetes", "redis"),
        employment_type="Full-time",
        apply_url="https://jobs.example.com/openings/job-002",
        summary="Scale high-throughput backend services for developer platforms.",
    ),
    JobPosting(
        id="job-003",
        title="Python FastAPI Backend Engineer",
        company="Nimbus Health",
        location="Remote-US",
        skills=("python", "fastapi", "sqlalchemy", "docker"),
        employment_type="Full-time",
        apply_url="https://jobs.example.com/openings/job-003",
        summary="Own backend APIs and data services for healthcare workflows.",
    ),
    JobPosting(
        id="job-004",
        title="Frontend Engineer (React/TypeScript)",
        company="Cedar Commerce",
        location="San Francisco, CA",
        skills=("react", "typescript", "nodejs", "graphql"),
        employment_type="Full-time",
        apply_url="https://jobs.example.com/openings/job-004",
        summary="Develop modern web apps and collaborate on API contracts.",
    ),
    JobPosting(
        id="job-005",
        title="ML Platform Engineer",
        company="Verge AI",
        location="Remote-US",
        skills=("python", "mlops", "airflow", "kubernetes"),
        employment_type="Full-time",
        apply_url="https://jobs.example.com/openings/job-005",
        summary="Productionize model training and deployment infrastructure.",
    ),
    JobPosting(
        id="job-006",
        title="Data Engineer (Spark/DBT)",
        company="Lumen Data",
        location="New York, NY",
        skills=("python", "spark", "dbt", "sql"),
        employment_type="Full-time",
        apply_url="https://jobs.example.com/openings/job-006",
        summary="Build analytics pipelines and data products for internal teams.",
    ),
    JobPosting(
        id="job-007",
        title="Senior Go Platform Engineer",
        company="Peak Infrastructure",
        location="Remote-US",
        skills=("go", "kubernetes", "terraform", "aws"),
        employment_type="Full-time",
        apply_url="https://jobs.example.com/openings/job-007",
        summary="Design platform services and improve reliability for distributed systems.",
    ),
    JobPosting(
        id="job-008",
        title="Cloud Security Engineer",
        company="ShieldCore",
        location="Remote-US",
        skills=("python", "aws", "security", "iam"),
        employment_type="Full-time",
        apply_url="https://jobs.example.com/openings/job-008",
        summary="Own cloud security controls, access policies, and detection workflows.",
    ),
    JobPosting(
        id="job-009",
        title="Senior Frontend Engineer",
        company="Pulse UX",
        location="Los Angeles, CA",
        skills=("react", "typescript", "graphql", "nodejs"),
        employment_type="Full-time",
        apply_url="https://jobs.example.com/openings/job-009",
        summary="Ship high-quality React applications and collaborate on API design.",
    ),
    JobPosting(
        id="job-010",
        title="DevOps Engineer (CI/CD)",
        company="Granite Systems",
        location="Denver, CO",
        skills=("docker", "kubernetes", "terraform", "jenkins"),
        employment_type="Full-time",
        apply_url="https://jobs.example.com/openings/job-010",
        summary="Maintain CI/CD pipelines and automate infrastructure for engineering teams.",
    ),
    JobPosting(
        id="job-011",
        title="Agentic AI Engineer",
        company="Nimbus Health",
        location="Remote-US",
        skills=("python", "llm", "langchain", "fastapi", "mlops"),
        employment_type="Full-time",
        apply_url="https://www.jotform.com/form-templates/preview/21115036573546/classic",
        summary="Design and build autonomous AI agents and multi-agent orchestration systems.",
    ),
)


def _normalize(text: str) -> str:
    lowered = re.sub(r"[^a-z0-9\+\#]+", " ", text.lower())
    return re.sub(r"\s+", " ", lowered).strip()


def _tokens(text: str) -> set[str]:
    return {t for t in _normalize(text).split() if t}


def _norm_set(values: list[str] | tuple[str, ...]) -> set[str]:
    return {v.strip().lower() for v in values if v.strip()}


def candidate_to_dict(c: Candidate) -> dict[str, Any]:
    return {
        "id": c.id, "name": c.name, "title": c.title, "location": c.location,
        "skills": list(c.skills), "years_experience": c.years_experience,
        "resume_url": c.resume_url, "summary": c.summary,
    }


def job_to_dict(j: JobPosting, score: float) -> dict[str, Any]:
    return {
        "id": j.id, "title": j.title, "company": j.company, "location": j.location,
        "skills": list(j.skills), "employment_type": j.employment_type,
        "apply_url": j.apply_url, "summary": j.summary, "match_score": round(score, 2),
    }


def search_jobs(
    query: str = "",
    location: str = "",
    limit: int = 5,
) -> dict[str, Any]:
    nq = _normalize(query)
    qt = _tokens(nq)
    loc = location.strip().lower()

    if not nq:
        return {"jobs": [job_to_dict(j, 1.0) for j in JOB_POSTINGS], "query_used": ""}

    limit = max(1, min(limit, len(JOB_POSTINGS)))
    ranked = []
    for j in JOB_POSTINGS:
        jt = _tokens(f"{j.title} {j.company} {' '.join(j.skills)} {j.summary}")
        overlap = len(qt & jt)
        denom = max(1, len(qt))
        tok_score = overlap / denom
        fuzzy = max(
            SequenceMatcher(None, nq, _normalize(j.title)).ratio(),
            SequenceMatcher(None, nq, _normalize(j.summary)).ratio(),
        )
        loc_bonus = 0.1 if loc and loc in j.location.lower() else 0.0
        score = 0.5 * tok_score + 0.3 * fuzzy + 0.2 * loc_bonus
        ranked.append((score, overlap, j))

    ranked.sort(key=lambda x: (x[0], x[1]), reverse=True)
    jobs = [job_to_dict(j, s) for s, o, j in ranked if s >= 0.15][:limit]
    return {"jobs": jobs, "query_used": nq}


def _active_candidates() -> list[Candidate]:
    return [c for c in CANDIDATES if c.id not in _DELETED_CANDIDATES]


def search_candidates(
    skills: list[str],
    location: str = "",
    limit: int = 5,
) -> dict[str, Any]:
    wanted = _norm_set(skills)
    loc = location.strip().lower()
    pool = _active_candidates() + _ADDED_CANDIDATES  # type: ignore[operator]

    def rank(c: Any) -> tuple[int, int]:
        c_skills = c.skills if isinstance(c, Candidate) else c.get("skills", [])
        c_loc = c.location if isinstance(c, Candidate) else c.get("location", "")
        c_exp = c.years_experience if isinstance(c, Candidate) else c.get("years_experience", 0)
        overlap = len(wanted & _norm_set(c_skills))
        bonus = 1 if loc and loc in c_loc.lower() else 0
        return overlap + bonus, c_exp

    ranked = sorted(pool, key=rank, reverse=True)
    selected = ranked[:max(1, min(limit, len(ranked)))] if ranked else []

    def to_dict(c: Any) -> dict[str, Any]:
        return candidate_to_dict(c) if isinstance(c, Candidate) else c

    return {"candidates": [to_dict(c) for c in selected]}


def score_candidate(candidate_id: str, job_description: str) -> dict[str, Any]:
    cand = next((c for c in CANDIDATES if c.id == candidate_id), None)
    if cand is None:
        raise ValueError(f"Unknown candidate_id: {candidate_id}")
    desc_tokens = _norm_set(job_description.split())
    overlap = len(desc_tokens & _norm_set(cand.skills))
    score = min(99, 60 + overlap * 7 + cand.years_experience)
    return {
        "candidate_id": cand.id,
        "score": score,
        "reasoning": f"{cand.name} matches {overlap} requested skills and has {cand.years_experience} years of experience.",
    }


def shortlist_candidate(candidate_id: str, reason: str) -> dict[str, Any]:
    shortlist_id = f"short-{uuid5(NAMESPACE_URL, f'{candidate_id}:{reason}')}"
    return {"shortlist_id": shortlist_id}


_DELETED_CANDIDATES: set[str] = set()
_ADDED_CANDIDATES: list[dict[str, Any]] = []


def delete_candidate(candidate_id: str, reason: str = "") -> dict[str, Any]:
    """Permanently remove a candidate from the system."""
    if candidate_id in _DELETED_CANDIDATES:
        raise ValueError(f"Candidate {candidate_id} was already deleted.")
    cand = next((c for c in CANDIDATES if c.id == candidate_id), None)
    if cand is None:
        raise ValueError(f"Unknown candidate_id: {candidate_id}")
    _DELETED_CANDIDATES.add(candidate_id)
    msg = f"Candidate {cand.name} ({candidate_id}) has been permanently deleted from the system."
    if reason:
        msg += f" Reason: {reason}"
    return {"deleted": True, "candidate_id": candidate_id, "name": cand.name, "message": msg}


def add_candidate(
    name: str,
    title: str,
    location: str,
    skills: str,
    years_experience: int,
    summary: str,
) -> dict[str, Any]:
    """Add a new candidate parsed from a CV."""
    candidate_id = f"cand-{len(CANDIDATES) + len(_ADDED_CANDIDATES) + 1:03d}"
    skill_list = [s.strip().lower() for s in skills.split(",") if s.strip()]
    record = {
        "id": candidate_id,
        "name": name,
        "title": title,
        "location": location,
        "skills": skill_list,
        "years_experience": years_experience,
        "summary": summary,
    }
    _ADDED_CANDIDATES.append(record)
    return {"added": True, "candidate": record}


def apply_to_job(candidate_id: str, job_id: str) -> dict[str, Any]:
    cand = next((c for c in CANDIDATES if c.id == candidate_id), None)
    if cand is None:
        raise ValueError(f"Unknown candidate_id: {candidate_id}")
    job = next((j for j in JOB_POSTINGS if j.id == job_id), None)
    if job is None:
        raise ValueError(f"Unknown job_id: {job_id}")
    return {
        "task": {
            "candidate_id": cand.id,
            "job_id": job.id,
            "apply_url": job.apply_url,
            "resume_url": cand.resume_url,
        }
    }
