from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from typing import Any


SKILL_ALIASES = {
    "js": "javascript",
    "javascript": "javascript",
    "python": "python",
    "py": "python",
    "sql": "sql",
    "excel": "excel",
    "ms excel": "excel",
    "sheets": "spreadsheets",
    "google sheets": "spreadsheets",
    "gcp": "google cloud",
    "google cloud platform": "google cloud",
    "cloud run": "cloud run",
    "bigquery": "bigquery",
    "looker": "looker",
    "tableau": "tableau",
    "power bi": "power bi",
    "linux": "linux",
    "networking": "networking",
    "salesforce": "salesforce",
    "java": "java",
    "leadership": "leadership",
    "communication": "communication",
    "customer support": "customer support",
    "project management": "project management",
    "stakeholder management": "stakeholder management",
    "data visualization": "data visualization",
}

ROLE_BASELINES = {
    "data analyst": {
        "sql",
        "excel",
        "python",
        "data visualization",
        "communication",
        "statistics",
    },
    "cloud support associate": {
        "google cloud",
        "linux",
        "networking",
        "python",
        "customer support",
        "troubleshooting",
    },
    "project coordinator": {
        "communication",
        "excel",
        "planning",
        "stakeholder management",
        "project management",
    },
    "ai solutions associate": {
        "python",
        "google cloud",
        "prompt engineering",
        "api integration",
        "communication",
    },
}

ROLE_KEYWORDS = {
    "data analyst": {"analyst", "dashboard", "sql", "reporting", "analytics"},
    "cloud support associate": {"cloud", "support", "linux", "network", "troubleshoot"},
    "project coordinator": {"coordinator", "project", "stakeholder", "planning", "timeline"},
    "ai solutions associate": {"ai", "agent", "python", "api", "automation"},
}


@dataclass(frozen=True)
class ResumeProfile:
    candidate_name: str | None
    email: str | None
    phone: str | None
    skills: list[str]
    years_experience: int | None
    education: list[str]
    projects: list[str]
    experience_summary: str
    source_quality: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "candidate_name": self.candidate_name,
            "email": self.email,
            "phone": self.phone,
            "skills": self.skills,
            "years_experience": self.years_experience,
            "education": self.education,
            "projects": self.projects,
            "experience_summary": self.experience_summary,
            "source_quality": self.source_quality,
        }


def normalize_skill(skill: str) -> str:
    clean = re.sub(r"\s+", " ", skill.strip().lower())
    return SKILL_ALIASES.get(clean, clean)


def normalize_skills(skills: list[str]) -> list[str]:
    return sorted({normalize_skill(skill) for skill in skills if str(skill).strip()})


def extract_skills(text: str) -> list[str]:
    lowered = text.lower()
    found = []
    for alias, canonical in SKILL_ALIASES.items():
        if re.search(rf"\b{re.escape(alias)}\b", lowered):
            found.append(canonical)
    return normalize_skills(found)


def parse_resume_text(
    text: str,
    *,
    candidate_name: str | None = None,
    experience_summary: str | None = None,
) -> ResumeProfile:
    clean = text.strip()
    lines = [line.strip() for line in clean.splitlines() if line.strip()]
    inferred_name = candidate_name or (lines[0] if lines else None)
    email_match = re.search(r"[\w.\-+]+@[\w.\-]+\.\w+", clean)
    phone_match = re.search(r"(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", clean)
    years_match = re.search(r"(\d+)\+?\s+years?", clean.lower())
    education = [
        line
        for line in lines
        if re.search(r"\b(university|college|bachelor|master|degree|certification)\b", line.lower())
    ]
    projects = [
        line
        for line in lines
        if re.search(r"\b(project|portfolio|built|created|implemented)\b", line.lower())
    ][:5]
    summary = experience_summary or " ".join(lines[:3])
    return ResumeProfile(
        candidate_name=inferred_name,
        email=email_match.group(0) if email_match else None,
        phone=phone_match.group(0) if phone_match else None,
        skills=extract_skills(clean),
        years_experience=int(years_match.group(1)) if years_match else None,
        education=education[:5],
        projects=projects,
        experience_summary=summary[:600],
        source_quality="text" if clean else "missing_resume_text",
    )


def role_required_skills(target_role: str) -> list[str]:
    role = target_role.strip().lower()
    return sorted(ROLE_BASELINES.get(role, ROLE_BASELINES["data analyst"]))


def analyze_skill_gap(skills: list[str], target_role: str) -> dict[str, Any]:
    normalized = normalize_skills(skills)
    required = role_required_skills(target_role)
    normalized_set = set(normalized)
    required_set = set(required)
    gaps = sorted(required_set.difference(normalized_set))
    strengths = sorted(required_set.intersection(normalized_set))
    fit_score = round(len(strengths) / max(len(required), 1), 2)
    return {
        "normalized_skills": normalized,
        "target_role": target_role.strip().lower() or "data analyst",
        "required_skills": required,
        "strengths": strengths,
        "skill_gaps": gaps,
        "fit_score": fit_score,
        "readiness_level": readiness_level(fit_score),
    }


def readiness_level(score: float) -> str:
    if score >= 0.8:
        return "demo_ready"
    if score >= 0.5:
        return "near_ready"
    if score >= 0.25:
        return "needs_guided_practice"
    return "foundation_needed"


def infer_target_roles(text: str, limit: int = 3) -> list[dict[str, Any]]:
    lowered = text.lower()
    scores = Counter()
    for role, keywords in ROLE_KEYWORDS.items():
        scores[role] = sum(1 for keyword in keywords if keyword in lowered)
    ranked = scores.most_common(limit)
    return [{"role": role, "confidence": min(1.0, round(score / 5, 2))} for role, score in ranked if score]


def build_learning_path(skill_gaps: list[str], weeks: int = 8) -> dict[str, Any]:
    capped_weeks = max(1, min(weeks, 12))
    gaps = skill_gaps[:capped_weeks] or ["portfolio project"]
    steps = []
    for index, gap in enumerate(gaps, start=1):
        steps.append(
            {
                "week": index,
                "focus": gap,
                "objective": f"Build practical confidence with {gap}.",
                "practice": f"Complete a small artifact that proves {gap} in a real scenario.",
                "evidence": f"Add a short portfolio note explaining how {gap} was used.",
            }
        )
    return {
        "duration_weeks": capped_weeks,
        "steps": steps,
        "success_metrics": [
            "one portfolio artifact",
            "resume bullet updated with measurable outcome",
            "mock interview answer prepared",
        ],
    }


def write_career_report(
    profile: dict[str, Any],
    gap_analysis: dict[str, Any],
    learning_path: dict[str, Any] | None = None,
) -> dict[str, Any]:
    name = profile.get("candidate_name") or "Candidate"
    gaps = gap_analysis.get("skill_gaps", [])
    strengths = gap_analysis.get("strengths", [])
    target_role = gap_analysis.get("target_role", "target role")
    return {
        "headline": f"{name} career readiness plan for {target_role}",
        "readiness_level": gap_analysis.get("readiness_level", "unknown"),
        "fit_score": gap_analysis.get("fit_score", 0),
        "strengths": strengths,
        "priority_gaps": gaps[:5],
        "next_actions": [
            f"Complete the first learning-path artifact for {gaps[0]}." if gaps else "Polish portfolio proof.",
            "Update resume with the strongest role-aligned evidence.",
            "Practice a two-minute story connecting experience to the target role.",
        ],
        "learning_path": learning_path or {},
        "advisor_notes": "Review recommendations with the candidate before external sharing.",
    }

