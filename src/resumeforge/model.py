"""Resume document model - stdlib only (dataclasses + typing)."""

from __future__ import annotations

from dataclasses import dataclass, field as dc_field


@dataclass
class ContactLink:
    """An arbitrary labelled hyperlink shown in the contact row."""

    label: str
    url: str


@dataclass
class ExperienceEntry:
    """A single job / role in the work-experience section."""

    company: str
    title: str
    start: str
    end: str  # "Present" is valid
    location: str = ""
    bullets: list[str] = dc_field(default_factory=list)


@dataclass
class EducationEntry:
    """A single institution / credential in the education section."""

    institution: str
    degree: str
    study_field: str = ""   # renamed from `field` to avoid shadowing dc_field
    start: str = ""
    end: str = ""
    gpa: str = ""
    notes: list[str] = dc_field(default_factory=list)


@dataclass
class ProjectEntry:
    """A single project entry."""

    name: str
    description: str = ""
    bullets: list[str] = dc_field(default_factory=list)
    url: str = ""
    tech: list[str] = dc_field(default_factory=list)


@dataclass
class CertificationEntry:
    """A single certification / credential entry."""

    name: str
    issuer: str = ""
    date: str = ""
    url: str = ""


@dataclass
class ResumeProfile:
    """Contact / identity information shown at the top of the resume."""

    name: str
    title: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""
    website: str = ""
    linkedin: str = ""
    github: str = ""
    links: list[ContactLink] = dc_field(default_factory=list)


@dataclass
class ResumeDocument:
    """The complete, parsed resume ready for rendering."""

    profile: ResumeProfile
    summary: str = ""
    experience: list[ExperienceEntry] = dc_field(default_factory=list)
    education: list[EducationEntry] = dc_field(default_factory=list)
    # category → list of skills
    skills: dict[str, list[str]] = dc_field(default_factory=dict)
    projects: list[ProjectEntry] = dc_field(default_factory=list)
    certifications: list[CertificationEntry] = dc_field(default_factory=list)
    # heading → list of plain-text items
    custom_sections: dict[str, list[str]] = dc_field(default_factory=dict)
    template: str = "modern"
    accent_color: str = "#2563eb"
    font: str = "inter"
