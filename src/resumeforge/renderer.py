"""
renderer.py - Render a ResumeDocument to an HTML string via Jinja2.

The template directory is located relative to this package:
    <package_root>/templates/
"""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .model import ResumeDocument

# Templates live two levels up from this file: src/resumeforge/ → src/templates/
_TEMPLATES_DIR = Path(__file__).parent.parent / "templates"


def render_html(doc: ResumeDocument, template_name: str | None = None) -> str:
    """
    Render *doc* using the named Jinja2 template.

    Parameters
    ----------
    doc:
        The fully-parsed and validated ResumeDocument.
    template_name:
        Template name without extension (default: ``doc.template``).

    Returns
    -------
    str
        Complete HTML document ready to be fed to WeasyPrint.
    """
    name = template_name or doc.template or "modern"
    template_file = f"{name}.html"

    env = Environment(
        loader=FileSystemLoader(str(_TEMPLATES_DIR)),
        autoescape=select_autoescape(["html"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )

    # Expose the templates directory path so the template can reference CSS
    env.globals["templates_dir"] = str(_TEMPLATES_DIR)

    tmpl = env.get_template(template_file)

    # Map font choice to a concrete CSS font-family stack
    font_stacks = {
        "inter": "'Inter', 'Helvetica Neue', Arial, sans-serif",
        "georgia": "Georgia, 'Times New Roman', serif",
        "source-sans": "'Source Sans 3', 'Helvetica Neue', Arial, sans-serif",
    }
    font_family = font_stacks.get(doc.font, font_stacks["inter"])

    html = tmpl.render(
        doc=doc,
        profile=doc.profile,
        accent=doc.accent_color,
        font_family=font_family,
        templates_dir=str(_TEMPLATES_DIR),
    )
    return html

