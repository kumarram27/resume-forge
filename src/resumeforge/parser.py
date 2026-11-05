"""
parser.py - Parse a Markdown + YAML front-matter file into a ResumeDocument.

Markdown body conventions
--------------------------
- `# Section Name`   → top-level section heading (case-insensitive)
- Known sections     : summary, experience, education, skills, projects, certifications
- Unknown `#` headings become custom sections

Experience
  ## Company Name     → company
  **Job Title**       → title  (bold-only line)
  March 2022 – Present → start / end  (regex date range)
  _Location_          → location (italic-only line)
  - bullet            → bullet point

Education
  ## Institution      → institution
  **Degree in Field** → degree + field
  Date line           → start / end
  GPA: 3.8            → gpa
  - note              → notes

Skills
  **Category:** s1, s2, s3  → dict entry
  - skill             → uncategorised entry

Projects
  ## Project Name     → name
  First paragraph     → description
  **Tech:** t1, t2    → tech tags
  - bullet            → bullets
  [url](url)          → url

Summary
  Raw text block      → summary string

Certifications
  ## Cert Name        → name
  **Issuer** text     → issuer
  Date line           → date
  [url](url)          → url
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import frontmatter
from markdown_it import MarkdownIt

from .model import (
    CertificationEntry,
    ContactLink,
    EducationEntry,
    ExperienceEntry,
    ProjectEntry,
    ResumeDocument,
    ResumeProfile,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_DATE_RANGE_RE = re.compile(
    r"""
    (?P<start>
        (?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|
           Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)
        [\s,]*\d{4}
        | \d{4}
    )
    \s*[-–—]{1,2}\s*
    (?P<end>
        (?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|
           Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)
        [\s,]*\d{4}
        | \d{4}
        | [Pp]resent
        | [Cc]urrent
    )
    """,
    re.VERBOSE,
)

_GPA_RE = re.compile(r"GPA\s*[:：]\s*([0-9.]+)", re.IGNORECASE)
_BOLD_ONLY_RE = re.compile(r"^\*\*(.+?)\*\*\s*$")
_ITALIC_ONLY_RE = re.compile(r"^[_*](.+?)[_*]\s*$")
_TECH_PREFIX_RE = re.compile(r"^\*\*Tech(?:nologies)?[:：]\*\*\s*(.+)$", re.IGNORECASE)
_SKILL_CATEGORY_RE = re.compile(r"^\*\*(.+?)[:：]\*\*\s*(.+)$")
_INLINE_URL_RE = re.compile(r"\[(?:[^\]]+)?\]\(([^)]+)\)")


def _strip_inline_md(text: str) -> str:
    """Remove common inline Markdown markup from a plain-text string."""
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"\*(.+?)\*", r"\1", text)
    text = re.sub(r"__(.+?)__", r"\1", text)
    text = re.sub(r"_(.+?)_", r"\1", text)
    text = re.sub(r"`(.+?)`", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    return text.strip()


def _extract_url(text: str) -> str:
    m = _INLINE_URL_RE.search(text)
    return m.group(1) if m else ""


def _parse_date_range(text: str) -> tuple[str, str]:
    """Return (start, end) strings or ("", "") if no date range found."""
    m = _DATE_RANGE_RE.search(text)
    if m:
        return m.group("start").strip(), m.group("end").strip()
    return "", ""


# ---------------------------------------------------------------------------
# Token-stream walker
# ---------------------------------------------------------------------------

class _TokenWalker:
    """
    Walk a markdown-it token list and expose simple navigation helpers.
    We collect raw inline content so we can parse it ourselves rather than
    relying on rendered HTML.
    """

    def __init__(self, tokens: list) -> None:
        self._tokens = tokens
        self._pos = 0

    def peek(self):
        if self._pos < len(self._tokens):
            return self._tokens[self._pos]
        return None

    def next(self):
        tok = self._tokens[self._pos]
        self._pos += 1
        return tok

    def done(self) -> bool:
        return self._pos >= len(self._tokens)

    def skip_until(self, *types: str):
        while not self.done() and self.peek().type not in types:
            self.next()

    def collect_inline_content(self) -> str:
        """
        Consume an inline token and return its raw text content.
        Handles nested children by joining their content.
        """
        tok = self.peek()
        if tok is None:
            return ""
        if tok.type == "inline":
            self.next()
            return tok.content if tok.content else ""
        return ""

    def consume_block(self, open_type: str, close_type: str) -> list:
        """Consume tokens between open_type and close_type and return them."""
        collected: list = []
        if self.peek() and self.peek().type == open_type:
            self.next()  # skip open
        while not self.done() and self.peek().type != close_type:
            collected.append(self.next())
        if not self.done():
            self.next()  # skip close
        return collected


# ---------------------------------------------------------------------------
# Section parsers
# ---------------------------------------------------------------------------

def _parse_summary(tokens: list) -> str:
    """Extract all paragraph text from a summary section's tokens."""
    parts: list[str] = []
    w = _TokenWalker(tokens)
    while not w.done():
        tok = w.next()
        if tok.type == "paragraph_open":
            content = w.collect_inline_content()
            parts.append(_strip_inline_md(content))
        elif tok.type == "inline":
            parts.append(_strip_inline_md(tok.content))
    return " ".join(p for p in parts if p)


def _parse_experience(tokens: list) -> list[ExperienceEntry]:
    entries: list[ExperienceEntry] = []
    current: dict[str, Any] = {}

    def _flush():
        if current.get("company"):
            entries.append(ExperienceEntry(
                company=current.get("company", ""),
                title=current.get("title", ""),
                start=current.get("start", ""),
                end=current.get("end", ""),
                location=current.get("location", ""),
                bullets=list(current.get("bullets", [])),
            ))

    w = _TokenWalker(tokens)
    while not w.done():
        tok = w.next()

        if tok.type == "heading_open" and tok.tag == "h2":
            _flush()
            current = {"company": "", "title": "", "start": "", "end": "",
                       "location": "", "bullets": []}
            content = w.collect_inline_content()
            current["company"] = _strip_inline_md(content)

        elif tok.type == "paragraph_open" and current:
            content = w.collect_inline_content()
            raw = content.strip()

            # Bold-only line → job title
            if _BOLD_ONLY_RE.match(raw) and not current.get("title"):
                current["title"] = _BOLD_ONLY_RE.match(raw).group(1).strip()
                continue

            # Italic-only line → location
            if _ITALIC_ONLY_RE.match(raw) and not current.get("location"):
                current["location"] = _ITALIC_ONLY_RE.match(raw).group(1).strip()
                continue

            # Date range line
            start, end = _parse_date_range(raw)
            if start and not current.get("start"):
                current["start"] = start
                current["end"] = end
                continue

        elif tok.type == "bullet_list_open" and current:
            # Consume list items as bullets
            while not w.done() and w.peek().type != "bullet_list_close":
                inner = w.next()
                if inner.type == "list_item_open":
                    # next paragraph_open → inline
                    while not w.done() and w.peek().type not in ("list_item_close",):
                        li_tok = w.next()
                        if li_tok.type == "inline":
                            current["bullets"].append(_strip_inline_md(li_tok.content))
                        elif li_tok.type == "paragraph_open":
                            lc = w.collect_inline_content()
                            current["bullets"].append(_strip_inline_md(lc))
            if not w.done():
                w.next()  # consume bullet_list_close

    _flush()
    return entries


def _parse_education(tokens: list) -> list[EducationEntry]:
    entries: list[EducationEntry] = []
    current: dict[str, Any] = {}

    def _flush():
        if current.get("institution"):
            entries.append(EducationEntry(
                institution=current.get("institution", ""),
                degree=current.get("degree", ""),
                study_field=current.get("study_field", ""),
                start=current.get("start", ""),
                end=current.get("end", ""),
                gpa=current.get("gpa", ""),
                notes=list(current.get("notes", [])),
            ))

    w = _TokenWalker(tokens)
    while not w.done():
        tok = w.next()

        if tok.type == "heading_open" and tok.tag == "h2":
            _flush()
            current = {"institution": "", "degree": "", "study_field": "",
                       "start": "", "end": "", "gpa": "", "notes": []}
            content = w.collect_inline_content()
            current["institution"] = _strip_inline_md(content)

        elif tok.type == "paragraph_open" and current:
            content = w.collect_inline_content()
            raw = content.strip()

            # Bold line → degree (possibly "Degree in Field")
            if _BOLD_ONLY_RE.match(raw) and not current.get("degree"):
                degree_raw = _BOLD_ONLY_RE.match(raw).group(1)
                if " in " in degree_raw:
                    parts = degree_raw.split(" in ", 1)
                    current["degree"] = parts[0].strip()
                    current["study_field"] = parts[1].strip()
                else:
                    current["degree"] = degree_raw.strip()
                continue

            # GPA line
            gpa_m = _GPA_RE.search(raw)
            if gpa_m:
                current["gpa"] = gpa_m.group(1)
                continue

            # Date range
            start, end = _parse_date_range(raw)
            if start and not current.get("start"):
                current["start"] = start
                current["end"] = end
                continue

        elif tok.type == "bullet_list_open" and current:
            while not w.done() and w.peek().type != "bullet_list_close":
                inner = w.next()
                if inner.type == "list_item_open":
                    while not w.done() and w.peek().type not in ("list_item_close",):
                        li_tok = w.next()
                        if li_tok.type == "inline":
                            current["notes"].append(_strip_inline_md(li_tok.content))
                        elif li_tok.type == "paragraph_open":
                            lc = w.collect_inline_content()
                            current["notes"].append(_strip_inline_md(lc))
            if not w.done():
                w.next()

    _flush()
    return entries


def _parse_skills(tokens: list) -> dict[str, list[str]]:
    skills: dict[str, list[str]] = {}
    uncategorised: list[str] = []
    w = _TokenWalker(tokens)

    while not w.done():
        tok = w.next()

        if tok.type == "paragraph_open":
            content = w.collect_inline_content()
            raw = content.strip()
            m = _SKILL_CATEGORY_RE.match(raw)
            if m:
                cat = m.group(1).strip()
                items = [s.strip() for s in m.group(2).split(",") if s.strip()]
                skills[cat] = items

        elif tok.type == "bullet_list_open":
            while not w.done() and w.peek().type != "bullet_list_close":
                inner = w.next()
                if inner.type == "list_item_open":
                    while not w.done() and w.peek().type not in ("list_item_close",):
                        li_tok = w.next()
                        if li_tok.type == "inline":
                            uncategorised.append(_strip_inline_md(li_tok.content))
                        elif li_tok.type == "paragraph_open":
                            lc = w.collect_inline_content()
                            uncategorised.append(_strip_inline_md(lc))
            if not w.done():
                w.next()

    if uncategorised and not skills:
        skills["Skills"] = uncategorised
    elif uncategorised:
        skills.setdefault("Other", []).extend(uncategorised)

    return skills


def _parse_projects(tokens: list) -> list[ProjectEntry]:
    entries: list[ProjectEntry] = []
    current: dict[str, Any] = {}

    def _flush():
        if current.get("name"):
            entries.append(ProjectEntry(
                name=current.get("name", ""),
                description=current.get("description", ""),
                bullets=list(current.get("bullets", [])),
                url=current.get("url", ""),
                tech=list(current.get("tech", [])),
            ))

    w = _TokenWalker(tokens)
    while not w.done():
        tok = w.next()

        if tok.type == "heading_open" and tok.tag == "h2":
            _flush()
            current = {"name": "", "description": "", "bullets": [], "url": "", "tech": []}
            content = w.collect_inline_content()
            # Name may contain a URL: [Name](url)
            url = _extract_url(content)
            if url:
                current["url"] = url
            current["name"] = _strip_inline_md(content)

        elif tok.type == "paragraph_open" and current:
            content = w.collect_inline_content()
            raw = content.strip()

            # Tech line: **Tech:** t1, t2
            tech_m = _TECH_PREFIX_RE.match(raw)
            if tech_m:
                current["tech"] = [t.strip() for t in tech_m.group(1).split(",") if t.strip()]
                continue

            # URL-only line
            url = _extract_url(raw)
            if url and not current.get("url"):
                current["url"] = url

            # First description paragraph
            plain = _strip_inline_md(raw)
            if plain and not current.get("description"):
                current["description"] = plain

        elif tok.type == "bullet_list_open" and current:
            while not w.done() and w.peek().type != "bullet_list_close":
                inner = w.next()
                if inner.type == "list_item_open":
                    while not w.done() and w.peek().type not in ("list_item_close",):
                        li_tok = w.next()
                        if li_tok.type == "inline":
                            raw = li_tok.content.strip()
                            url = _extract_url(raw)
                            if url and re.match(r"^\*{0,2}GitHub\b", raw, re.IGNORECASE):
                                current["url"] = url
                            else:
                                current["bullets"].append(_strip_inline_md(raw))
                        elif li_tok.type == "paragraph_open":
                            raw = w.collect_inline_content().strip()
                            url = _extract_url(raw)
                            if url and re.match(r"^\*{0,2}GitHub\b", raw, re.IGNORECASE):
                                current["url"] = url
                            else:
                                current["bullets"].append(_strip_inline_md(raw))
            if not w.done():
                w.next()

    _flush()
    return entries


def _parse_certifications(tokens: list) -> list[CertificationEntry]:
    entries: list[CertificationEntry] = []
    current: dict[str, Any] = {}

    def _flush():
        if current.get("name"):
            entries.append(CertificationEntry(
                name=current.get("name", ""),
                issuer=current.get("issuer", ""),
                date=current.get("date", ""),
                url=current.get("url", ""),
            ))

    w = _TokenWalker(tokens)
    while not w.done():
        tok = w.next()

        if tok.type == "heading_open" and tok.tag == "h2":
            _flush()
            current = {"name": "", "issuer": "", "date": "", "url": ""}
            content = w.collect_inline_content()
            current["name"] = _strip_inline_md(content)
            url = _extract_url(content)
            if url:
                current["url"] = url

        elif tok.type == "paragraph_open" and current:
            content = w.collect_inline_content()
            raw = content.strip()

            # URL
            url = _extract_url(raw)
            if url and not current.get("url"):
                current["url"] = url

            # Bold-only → issuer
            if _BOLD_ONLY_RE.match(raw) and not current.get("issuer"):
                current["issuer"] = _BOLD_ONLY_RE.match(raw).group(1).strip()
                continue

            # Date range or single year
            start, end = _parse_date_range(raw)
            if start:
                current["date"] = f"{start} – {end}" if end else start
                continue

            # Plain text that looks like an issuer
            plain = _strip_inline_md(raw)
            if plain and not current.get("issuer"):
                current["issuer"] = plain

    _flush()
    return entries


def _parse_custom(tokens: list) -> list[str]:
    items: list[str] = []
    w = _TokenWalker(tokens)
    while not w.done():
        tok = w.next()
        if tok.type == "paragraph_open":
            content = w.collect_inline_content()
            plain = _strip_inline_md(content)
            if plain:
                items.append(plain)
        elif tok.type == "bullet_list_open":
            while not w.done() and w.peek().type != "bullet_list_close":
                inner = w.next()
                if inner.type == "list_item_open":
                    while not w.done() and w.peek().type not in ("list_item_close",):
                        li_tok = w.next()
                        if li_tok.type == "inline":
                            items.append(_strip_inline_md(li_tok.content))
                        elif li_tok.type == "paragraph_open":
                            lc = w.collect_inline_content()
                            items.append(_strip_inline_md(lc))
            if not w.done():
                w.next()
    return items


# ---------------------------------------------------------------------------
# Front-matter → ResumeProfile
# ---------------------------------------------------------------------------

def _build_profile(meta: dict) -> ResumeProfile:
    links_raw = meta.get("links", [])
    links: list[ContactLink] = []
    if isinstance(links_raw, dict):
        link_items = [
            {"text": label, "url": url}
            for label, url in links_raw.items()
        ]
    elif isinstance(links_raw, list):
        link_items = links_raw
    elif links_raw is None:
        link_items = []
    else:
        raise ValueError("Front matter 'links' must be a list or label-to-URL mapping.")

    for index, item in enumerate(link_items, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"Front matter link #{index} must contain text and url.")

        label = item.get("text", item.get("label", ""))
        url = item.get("url", item.get("href", ""))
        if not isinstance(label, str) or not label.strip():
            raise ValueError(f"Front matter link #{index} is missing its display text.")
        if not isinstance(url, str) or not url.strip():
            raise ValueError(f"Front matter link #{index} is missing its URL.")

        links.append(ContactLink(label=label.strip(), url=url.strip()))

    return ResumeProfile(
        name=meta.get("name", ""),
        title=meta.get("title", ""),
        email=meta.get("email", ""),
        phone=str(meta.get("phone", "")),
        location=meta.get("location", ""),
        website=meta.get("website", ""),
        linkedin=meta.get("linkedin", ""),
        github=meta.get("github", ""),
        links=links,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

_KNOWN_SECTIONS = {"summary", "experience", "education", "skills", "projects", "certifications"}


def parse_file(path: str | Path) -> ResumeDocument:
    """Parse a Markdown + YAML front-matter file into a ResumeDocument."""
    path = Path(path)
    post = frontmatter.load(str(path))
    meta: dict = dict(post.metadata)
    body: str = post.content

    profile = _build_profile(meta)
    template = meta.get("template", "modern")
    accent_color = meta.get("accent_color", "#2563eb")
    font = meta.get("font", "inter")

    # Tokenise the Markdown body
    md = MarkdownIt("commonmark")
    tokens = md.parse(body)

    # Split tokens by h1 headings into named sections
    sections: dict[str, list] = {}
    current_section: str | None = None
    section_tokens: list = []

    for tok in tokens:
        if tok.type == "heading_open" and tok.tag == "h1":
            # The next inline token is the heading text
            continue
        if tok.type == "inline" and current_section is None:
            # Check if this is the first heading label
            sections.setdefault("__pending__", []).append(tok)
            continue
        if tok.type == "heading_close" and tok.tag == "h1":
            continue

        # Detect heading_open h1 → we need to look ahead for the label
        # markdown-it emits: heading_open, inline, heading_close
        # We handle this by finding inline tokens whose preceding sibling was heading_open h1
        if tok.type == "heading_open" and tok.tag == "h1":
            if current_section is not None:
                sections[current_section] = section_tokens
            section_tokens = []
            current_section = "__next_label__"
            continue

        if current_section == "__next_label__":
            if tok.type == "inline":
                label = tok.content.strip().lower()
                # If there was already a section saved for current_section, merge
                if current_section in sections:
                    sections[current_section] = section_tokens
                current_section = label
                section_tokens = []
                continue
            # Unexpected token while looking for label
            section_tokens.append(tok)
            continue

        section_tokens.append(tok)

    if current_section and current_section not in ("__next_label__", "__pending__"):
        sections[current_section] = section_tokens

    # ------- Re-parse using a simpler single-pass approach -------
    # The above nested state machine is fragile; use a cleaner pass:
    sections = _split_by_h1(tokens)

    # Parse each section
    summary = _parse_summary(sections.get("summary", []))
    experience = _parse_experience(sections.get("experience", []))
    education = _parse_education(sections.get("education", []))
    skills = _parse_skills(sections.get("skills", []))
    projects = _parse_projects(sections.get("projects", []))
    certifications = _parse_certifications(sections.get("certifications", []))

    custom_sections: dict[str, list[str]] = {}
    for key, toks in sections.items():
        if key not in _KNOWN_SECTIONS:
            items = _parse_custom(toks)
            if items:
                # Capitalise the heading nicely
                custom_sections[key.title()] = items

    return ResumeDocument(
        profile=profile,
        summary=summary,
        experience=experience,
        education=education,
        skills=skills,
        projects=projects,
        certifications=certifications,
        custom_sections=custom_sections,
        template=template,
        accent_color=accent_color,
        font=font,
    )


def _split_by_h1(tokens: list) -> dict[str, list]:
    """
    Walk a flat markdown-it token list and split into named sections at
    every `# Heading` (h1) boundary.  Returns {section_name: [tokens]}.
    """
    sections: dict[str, list] = {}
    current_name: str | None = None
    buf: list = []
    i = 0
    n = len(tokens)

    while i < n:
        tok = tokens[i]
        if tok.type == "heading_open" and tok.tag == "h1":
            # Save previous section
            if current_name is not None:
                sections[current_name] = buf
            buf = []
            # Next token should be inline with the heading text
            if i + 1 < n and tokens[i + 1].type == "inline":
                current_name = tokens[i + 1].content.strip().lower()
                i += 2  # skip inline
                # Skip heading_close
                if i < n and tokens[i].type == "heading_close":
                    i += 1
                continue
        else:
            buf.append(tok)
        i += 1

    if current_name is not None:
        sections[current_name] = buf

    return sections
