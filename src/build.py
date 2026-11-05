#!/usr/bin/env python3
"""
build.py - CLI entry point for the ResumeForge GitHub Action.

Inputs are passed via environment variables (set by action.yml):
  RESUME_FILE      Path to the resume Markdown file (relative to workspace)
  OUTPUT_DIR       Directory for generated output (relative to workspace)
  TEMPLATE         Template name (default: modern)
  ACCENT_COLOR     CSS hex accent color (default: #2563eb)
  FONT             Font choice: inter | georgia | source-sans (default: inter)
  VERSIONING       "true" to write a versioned copy (default: false)
  GITHUB_WORKSPACE Repo root; falls back to PWD
  GITHUB_SHA       Current commit SHA (used in versioned filename)
  GITHUB_OUTPUT    Path to the $GITHUB_OUTPUT file for action output variables
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Resolve workspace root
# ---------------------------------------------------------------------------

workspace = Path(os.environ.get("GITHUB_WORKSPACE", os.getcwd()))

# ---------------------------------------------------------------------------
# Read and normalise inputs
# ---------------------------------------------------------------------------

resume_file_rel = os.environ.get("RESUME_FILE", "resume.md")
output_dir_rel = os.environ.get("OUTPUT_DIR", "resume-output")
template = os.environ.get("TEMPLATE", "modern")
accent_color = os.environ.get("ACCENT_COLOR", "#2563eb")
font = os.environ.get("FONT", "inter")
versioning_raw = os.environ.get("VERSIONING", "false").strip().lower()
versioning = versioning_raw in ("1", "true", "yes")
git_sha = os.environ.get("GITHUB_SHA", "")

resume_file = workspace / resume_file_rel
output_dir = workspace / output_dir_rel

# ---------------------------------------------------------------------------
# Validate the input file exists before handing off to the pipeline
# ---------------------------------------------------------------------------

if not resume_file.exists():
    print(
        f"[ResumeForge] ERROR: Resume file not found: {resume_file}\n"
        f"  Set the 'resume_file' action input to the correct path, or add a "
        f"'{resume_file_rel}' file to your repo root."
    )
    sys.exit(1)

# ---------------------------------------------------------------------------
# Add src/ to the Python path so `resumeforge` is importable when invoked
# directly (outside of an installed package).
# ---------------------------------------------------------------------------

src_dir = Path(__file__).parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

# ---------------------------------------------------------------------------
# Run the pipeline
# ---------------------------------------------------------------------------

from resumeforge import builder  # noqa: E402  (after sys.path manipulation)

result = builder.run({
    "resume_file": str(resume_file),
    "output_dir": str(output_dir),
    "template": template,
    "accent_color": accent_color,
    "font": font,
    "versioning": versioning,
    "git_sha": git_sha,
})

# ---------------------------------------------------------------------------
# Write action outputs to $GITHUB_OUTPUT
# ---------------------------------------------------------------------------

github_output = os.environ.get("GITHUB_OUTPUT", "")
if github_output:
    pdf_rel = Path(result["pdf_path"]).relative_to(workspace)
    with open(github_output, "a") as fh:
        fh.write(f"pdf_path={pdf_rel}\n")
        fh.write(f"version={result['version']}\n")

print(f"[ResumeForge] Done. PDF → {result['pdf_path']}")

