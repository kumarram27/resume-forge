"""
validator.py - Validate a ResumeDocument and surface clear, actionable errors.

Severity levels
---------------
- "error"   → blocks PDF generation (SystemExit(1) is raised after reporting)
- "warning" → printed to stdout but does NOT prevent generation
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass

from .model import ResumeDocument

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@dataclass
class ValidationError:
    field: str
    message: str
    severity: str  # "error" or "warning"

    def __str__(self) -> str:
        icon = "✖" if self.severity == "error" else "⚠"
        return f"  {icon} [{self.field}] {self.message}"


def validate(doc: ResumeDocument) -> list[ValidationError]:
    """
    Validate *doc* and return a (possibly empty) list of ValidationError objects.

    Errors are also printed immediately so CI logs show them without needing
    the caller to iterate the list.
    """
    errors: list[ValidationError] = []

    def _err(field: str, msg: str) -> None:
        errors.append(ValidationError(field=field, message=msg, severity="error"))

    def _warn(field: str, msg: str) -> None:
        errors.append(ValidationError(field=field, message=msg, severity="warning"))

    # ── Required fields ──────────────────────────────────────────────────────
    if not doc.profile.name.strip():
        _err("profile.name", "Name is required but is empty.")

    if not doc.profile.email.strip():
        _err("profile.email", "Email address is required but is empty.")
    elif not _EMAIL_RE.match(doc.profile.email.strip()):
        _err(
            "profile.email",
            f"'{doc.profile.email}' does not look like a valid email address.",
        )

    # ── Warnings ─────────────────────────────────────────────────────────────
    if not doc.profile.title.strip():
        _warn("profile.title", "Job title / headline is empty - consider adding one.")

    if not doc.summary.strip():
        _warn("summary", "Summary section is empty - a brief summary helps ATS scanners.")

    if not doc.experience and not doc.education:
        _warn(
            "experience/education",
            "Resume has neither Experience nor Education entries - it may look sparse.",
        )

    for exp in doc.experience:
        if not exp.bullets:
            _warn(
                "experience.bullets",
                f"Experience entry for '{exp.company}' has no bullet points.",
            )

    # ── Report ────────────────────────────────────────────────────────────────
    hard_errors = [e for e in errors if e.severity == "error"]
    warnings = [e for e in errors if e.severity == "warning"]

    if warnings:
        print("\nResumeForge warnings:")
        for w in warnings:
            print(str(w))
        print()

    if hard_errors:
        print("\nResumeForge validation errors (generation aborted):")
        for e in hard_errors:
            print(str(e))
        print()
        sys.exit(1)

    return errors

