from __future__ import annotations

from skillbridge_common.career import (
    analyze_skill_gap,
    build_learning_path,
    parse_resume_text,
    write_career_report,
)


def test_parse_resume_text_extracts_profile_facts() -> None:
    profile = parse_resume_text(
        """
        Sandeep Singh
        sandeep@example.com
        214-555-1212
        5 years building Python SQL Excel dashboards on Google Cloud.
        Built portfolio project for stakeholder reporting.
        Bachelor of Science, Example University
        """
    )

    assert profile.candidate_name == "Sandeep Singh"
    assert profile.email == "sandeep@example.com"
    assert "python" in profile.skills
    assert "sql" in profile.skills
    assert "excel" in profile.skills
    assert profile.years_experience == 5
    assert profile.education
    assert profile.projects


def test_analyze_skill_gap_scores_target_role() -> None:
    analysis = analyze_skill_gap(["Python", "SQL", "Excel"], "data analyst")

    assert analysis["target_role"] == "data analyst"
    assert analysis["fit_score"] == 0.5
    assert analysis["readiness_level"] == "near_ready"
    assert "data visualization" in analysis["skill_gaps"]
    assert "sql" in analysis["strengths"]


def test_build_learning_path_caps_weeks_and_returns_artifacts() -> None:
    path = build_learning_path(["sql", "python", "communication"], weeks=20)

    assert path["duration_weeks"] == 12
    assert path["steps"][0]["focus"] == "sql"
    assert "portfolio" in path["success_metrics"][0]


def test_write_career_report_uses_gap_analysis() -> None:
    report = write_career_report(
        {"candidate_name": "Sandeep"},
        {
            "target_role": "data analyst",
            "fit_score": 0.5,
            "readiness_level": "near_ready",
            "strengths": ["sql"],
            "skill_gaps": ["python"],
        },
    )

    assert report["headline"] == "Sandeep career readiness plan for data analyst"
    assert report["priority_gaps"] == ["python"]
    assert report["fit_score"] == 0.5

