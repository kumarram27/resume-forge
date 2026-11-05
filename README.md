# ResumeForge

> **Turn your Markdown resume into a polished, ATS-ready PDF - automatically, on every push.**

ResumeForge is a GitHub Action that reads a resume written in plain Markdown (with YAML front matter), renders it through a professional HTML/CSS template, generates a PDF via [WeasyPrint](https://weasyprint.org/), and commits the result back to your repository - no browser, no LaTeX, no local tooling required.

---

## Quick Start

1. **Add your resume** - copy [`examples/resume.md`](examples/resume.md) to your repo root and fill it in.
2. **Add the workflow** - copy [`examples/workflow.yml`](examples/workflow.yml) to `.github/workflows/resume.yml`.
3. **Push to `main`** - the Action runs, generates `resume-output/resume.pdf`, and commits it back.

```yaml
# .github/workflows/resume.yml
name: Build Resume

on:
  push:
    branches: [main]
    paths: ['resume.md']

jobs:
  build-resume:
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - uses: actions/checkout@v4
        with:
          persist-credentials: true

      - uses: kumarram27/resume-forge@v1
        with:
          resume_file: resume.md
          output_dir: resume-output
          accent_color: '#2563eb'
          font: inter
          github_token: ${{ secrets.GITHUB_TOKEN }}
```

---

## Inputs

| Input | Description | Default |
|---|---|---|
| `resume_file` | Path to the resume Markdown file (relative to repo root) | `resume.md` |
| `output_dir` | Directory where generated files are written | `resume-output` |
| `template` | Template name | `modern` |
| `accent_color` | CSS hex color for section accents | `#2563eb` |
| `font` | Font family - `inter`, `georgia`, or `source-sans` | `inter` |
| `versioning` | Also save a timestamped copy in `<output_dir>/versions/` | `false` |
| `commit_output` | Commit and push generated output back to the repo | `true` |
| `github_token` | Token used for the push commit | `${{ github.token }}` |

## Outputs

| Output | Description |
|---|---|
| `pdf_path` | Repo-relative path to the generated PDF (`resume-output/resume.pdf`) |
| `version` | Versioned filename (e.g. `resume-20240315-142300-a1b2c3d.pdf`); empty when `versioning: false` |

---

## Resume Format

Your resume is a single Markdown file with a YAML front matter block followed by section headings.

### Front Matter (contact info + theming)

```yaml
---
name: Alex Rivera
title: Senior Software Engineer
email: alex@example.com
phone: "+1 (415) 555-0192"
location: San Francisco, CA
website: https://alexrivera.dev
linkedin: https://linkedin.com/in/alexrivera
github: https://github.com/alexrivera

# Optional labeled links. `text` is shown in the resume alongside its clickable URL.
links:
  - text: Portfolio
    url: https://alexrivera.dev
  - text: GitHub
    url: https://github.com/alexrivera

# Alternatively, use link text as mapping keys:
# links:
#   Portfolio: https://alexrivera.dev
#   GitHub: https://github.com/alexrivera
#
# The older `label` key is also supported in list entries.
# Link labels and URLs are both printed, and the URL is clickable in the PDF.

# Theming (can also be set via action inputs)
accent_color: "#2563eb"
font: inter
---
```

### Markdown Body Sections

| Heading | Behaviour |
|---|---|
| `# Summary` | Plain text paragraph - rendered as a summary block |
| `# Experience` | `##` sub-headings per company; bold title, date range, italic location, `- bullets` |
| `# Education` | `##` per institution; bold degree, date range, `GPA: x.x`, `- notes` |
| `# Skills` | `**Category:** skill1, skill2` lines, or plain `- skill` bullets |
| `# Projects` | `##` per project; `- GitHub: [Repository](URL)` for its link, `**Tech:** tag1, tag2`, description, and `- bullets` |
| `# Certifications` | `##` per cert; bold issuer, date line, optional URL |
| `# Any Other Heading` | Rendered as a custom labelled bullet list |

#### Experience example

```markdown
# Experience

## Stripe
**Staff Software Engineer**
January 2022 – Present
_San Francisco, CA_

- Led architecture of an internal feature-flag platform serving 400M evaluations/day.
- Reduced CI pipeline duration by 42 % with remote build caching.
```

#### Skills example

```markdown
# Skills

**Languages:** Rust, Go, Python, TypeScript
**Platforms:** Kubernetes, AWS, Cloudflare Workers
```

#### Certifications example

```markdown
# Certifications

## AWS Certified Solutions Architect - Professional
**Amazon Web Services**
March 2023
[https://aws.amazon.com/certification/](https://aws.amazon.com/certification/)
```

---

## Templates & Theming

### Available templates

| Name | Description |
|---|---|
| `modern` | Minimal, single-column, black-and-white layout with labeled, clickable contact and project links |

More templates are planned for Phase 2.

The `modern` template is intentionally black and white; `accent_color` is retained as an action input for compatibility.

### Font options

| Value | Typeface |
|---|---|
| `inter` | Inter (default) - modern geometric sans-serif |
| `georgia` | Georgia - classic serif, strong on paper |
| `source-sans` | Source Sans 3 - humanist sans, highly readable |

Fonts use the selected local font when available, with system sans-serif fallbacks. PDF generation does not fetch fonts from a network CDN.

---

## Generated Output

```
resume-output/
  resume.pdf                          ← always generated
  versions/                           ← only when versioning: true
    resume-20240315-142300-a1b2c3d.pdf
```

The commit message is `chore: update resume [skip ci]` to prevent infinite workflow loops.

---

## Versioning

When `versioning: true`, ResumeForge copies the generated PDF to:

```
resume-output/versions/resume-<YYYYMMDD-HHMMSS>-<sha7>.pdf
```

where `<sha7>` is the first 7 characters of the triggering commit SHA. This gives you a complete history of every version of your resume, useful for tracking changes over time.

---

## License

[MIT](LICENSE)
