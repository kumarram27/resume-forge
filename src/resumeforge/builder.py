"""
builder.py - Orchestrate the full parse → validate → render → PDF pipeline.
"""

from __future__ import annotations

import hashlib
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def run(config: dict[str, Any]) -> dict[str, Any]:
    """
    Execute the ResumeForge pipeline.

    Parameters
    ----------
    config : dict
        Keys:
          - resume_file   : str  - path to the resume Markdown file
          - output_dir    : str  - directory to write generated files into
          - template      : str  - template name (default "modern")
          - accent_color  : str  - CSS hex color (default "#2563eb")
          - font          : str  - font choice (default "inter")
          - versioning    : bool - whether to also write a versioned copy
          - git_sha       : str  - current commit SHA (for versioned filename)

    Returns
    -------
    dict
        - pdf_path : str - absolute path to the generated PDF
        - version  : str - versioned filename (empty string when versioning=False)
    """
    from .parser import parse_file
    from .validator import validate
    from .renderer import render_html
    from .pdf import generate_pdf

    resume_file = Path(config["resume_file"])
    output_dir = Path(config["output_dir"])
    template = config.get("template", "modern")
    accent_color = config.get("accent_color", "#2563eb")
    font = config.get("font", "inter")
    versioning = bool(config.get("versioning", False))
    git_sha: str = config.get("git_sha", "")

    # ── 1. Parse ─────────────────────────────────────────────────────────────
    print(f"[ResumeForge] Parsing {resume_file} …")
    doc = parse_file(resume_file)

    # Override template/theming from action inputs (action inputs take precedence
    # over values embedded in the front matter)
    if template:
        doc.template = template
    if accent_color:
        doc.accent_color = accent_color
    if font:
        doc.font = font

    # ── 2. Validate ───────────────────────────────────────────────────────────
    print("[ResumeForge] Validating …")
    validate(doc)  # exits on hard errors

    # ── 3. Render ─────────────────────────────────────────────────────────────
    print("[ResumeForge] Rendering HTML …")
    html = render_html(doc)

    # ── 4. Generate PDF ───────────────────────────────────────────────────────
    output_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = output_dir / "resume.pdf"
    generate_pdf(html, pdf_path)

    # ── 5. Versioning (optional) ──────────────────────────────────────────────
    version_filename = ""
    if versioning:
        versions_dir = output_dir / "versions"
        versions_dir.mkdir(parents=True, exist_ok=True)

        ts = datetime.now(tz=timezone.utc).strftime("%Y%m%d-%H%M%S")
        sha7 = (git_sha[:7] if git_sha else _file_sha7(pdf_path))
        version_filename = f"resume-{ts}-{sha7}.pdf"
        versioned_path = versions_dir / version_filename
        shutil.copy2(pdf_path, versioned_path)
        print(f"[ResumeForge] Versioned copy → {versioned_path}")

    return {
        "pdf_path": str(pdf_path),
        "version": version_filename,
    }


def _file_sha7(path: Path) -> str:
    """Return first 7 chars of the SHA-256 of a file's contents."""
    h = hashlib.sha256(path.read_bytes()).hexdigest()
    return h[:7]

