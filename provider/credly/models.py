"""
Core data models for the Certificate Intelligence Agent.
These are plain dataclasses — no framework dependencies.
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Skill:
    name: str


@dataclass
class Certification:
    id: str
    name: str
    issuer: str
    description: str
    issue_date: Optional[str]
    expiry_date: Optional[str]
    badge_url: str
    image_url: str
    skills: List[Skill] = field(default_factory=list)
    source: str = "credly"          # "credly" | "external"


@dataclass
class Employee:
    user_id: str
    full_name: str
    certifications: List[Certification] = field(default_factory=list)

    @property
    def all_skills(self) -> List[Skill]:
        """
        Return ALL skills across all certifications, preserving duplicates.
        Duplicates matter: a skill appearing in 3 certs shows deeper expertise
        than one that appears once. The AI uses this to reason about learning depth.
        """
        skills = []
        for cert in self.certifications:
            for skill in cert.skills:
                skills.append(skill)
        return skills

    @property
    def unique_skills(self) -> List[Skill]:
        """Deduplicated skill list (for display/counting)."""
        seen = set()
        result = []
        for skill in self.all_skills:
            if skill.name not in seen:
                seen.add(skill.name)
                result.append(skill)
        return result

    @property
    def skill_frequency(self) -> dict:
        """
        Returns {skill_name: count} — how many certs cover each skill.
        Higher count = stronger signal of expertise in that area.
        """
        freq = {}
        for cert in self.certifications:
            for skill in cert.skills:
                freq[skill.name] = freq.get(skill.name, 0) + 1
        return freq


@dataclass
class ExpiryStatus:
    certification: str
    expiry_date: Optional[str]
    days_remaining: Optional[int]
    status: str                     # Healthy | Renew Soon | Expiring Soon | Expired | No Expiry
