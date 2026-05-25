#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys


AGENTS = {
    "resume-parser-agent": {
        "description": "Extracts structured experience, education, projects, and skills from resumes.",
        "skills": [
            {
                "id": "parse_resume",
                "name": "Parse Resume",
                "description": "Parses resume text or document metadata into normalized profile facts.",
            }
        ],
    },
    "skill-graph-agent": {
        "description": "Normalizes skills and maps skill gaps against target roles.",
        "skills": [
            {
                "id": "gap_analysis",
                "name": "Skill Gap Analysis",
                "description": "Compares candidate skills with a target role baseline.",
            },
            {
                "id": "normalize_skills",
                "name": "Normalize Skills",
                "description": "Converts raw skills into canonical skill names.",
            },
        ],
    },
    "learning-path-agent": {
        "description": "Builds practical learning plans from skill gaps and career goals.",
        "skills": [
            {
                "id": "build_learning_path",
                "name": "Build Learning Path",
                "description": "Creates a prioritized roadmap for closing skill gaps.",
            }
        ],
    },
    "report-writer-agent": {
        "description": "Turns agent outputs into user-facing career plans and advisor reports.",
        "skills": [
            {
                "id": "write_career_report",
                "name": "Write Career Report",
                "description": "Creates a concise career plan from profile, gap, and learning outputs.",
            }
        ],
    },
    "ops-autocorrect-agent": {
        "description": "Diagnoses observability alerts and proposes controlled remediation actions.",
        "skills": [
            {
                "id": "diagnose_alert",
                "name": "Diagnose Alert",
                "description": "Classifies an incident and returns safe remediation options.",
            }
        ],
    },
}


def service_url(service: str, region: str) -> str:
    command = [
        "gcloud",
        "run",
        "services",
        "describe",
        f"skillbridge-{service}",
        "--region",
        region,
        "--format=value(status.url)",
    ]
    return subprocess.check_output(command, text=True).strip()


def main() -> int:
    region = sys.argv[1] if len(sys.argv) > 1 else "us-south1"
    cards = []
    for service, metadata in AGENTS.items():
        url = service_url(service, region)
        cards.append(
            {
                "name": service,
                "description": metadata["description"],
                "url": url,
                "skills": metadata["skills"],
            }
        )
    print(json.dumps(cards, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
