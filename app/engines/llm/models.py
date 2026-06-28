"""Shared response dataclasses for all LLM providers."""

from dataclasses import dataclass, field
from typing import List


@dataclass
class ExplanationResponse:
    """Plain English explanation of an accessibility violation."""
    explanation: str
    affected_users: str
    why_it_matters: str

    def to_dict(self) -> dict:
        return {
            "explanation": self.explanation,
            "affected_users": self.affected_users,
            "why_it_matters": self.why_it_matters,
        }


@dataclass
class FixResponse:
    """
    AI-generated remediation suggestion for an accessibility violation.

    Contains structured information about the problem, recommended fix,
    code example, implementation steps, and priority level.

    This richer format is used by FixGeneratorService to populate the
    ai_fix JSON column on violation records.
    """
    problem: str
    recommended_fix: str
    code_example: str
    implementation_steps: List[str] = field(default_factory=list)
    priority: str = "moderate"

    def to_dict(self) -> dict:
        return {
            "problem": self.problem,
            "recommended_fix": self.recommended_fix,
            "code_example": self.code_example,
            "implementation_steps": self.implementation_steps,
            "priority": self.priority,
        }


@dataclass
class AffectedGroup:
    """A disability group and the impact a violation has on them."""
    disability: str
    impact: str


@dataclass
class SimulationResponse:
    """
    AI-generated disability simulation for a specific rule_id.

    Describes how different disability groups are affected by an
    accessibility violation, along with a severity explanation,
    the simulated user experience, and the impact on general users.
    """
    affected_groups: List[AffectedGroup] = field(default_factory=list)
    severity_explanation: str = ""
    user_experience: str = ""
    general_user_impact: str = ""

    def to_dict(self) -> dict:
        return {
            "affected_groups": [
                {"disability": g.disability, "impact": g.impact}
                for g in self.affected_groups
            ],
            "severity_explanation": self.severity_explanation,
            "user_experience": self.user_experience,
            "general_user_impact": self.general_user_impact,
        }
