# ResumeForge

A reusable GitHub Action for packaging, versioning, and publishing compiled LaTeX resumes.

ResumeForge handles the publishing preparation. It does not compile LaTeX or deploy GitHub Pages.

## Features

- Validates an existing compiled PDF.
- Creates uniquely versioned PDF archives.
- Maintains a `latest.json` manifest.
- Generates a responsive HTML PDF viewer.
- Exposes paths and version information as action outputs.
- Preserves existing archives without deleting previous versions.

## Usage

Compile your resume first, then run ResumeForge:

```yaml

- name: Package resume
  uses: kumarram27/resume-forge@v1
  with:
    pdf_file: resume.pdf
    output_dir: public
    resume_name: My Resume
```

## Inputs

| Input | Description | Default |
|---|---|---|
| `pdf_file` | Compiled PDF path, relative to workspace or absolute | `resume.pdf` |
| `output_dir` | Output directory | `public` |
| `resume_name` | Name shown in viewer | `My Resume` |
| `generate_viewer` | Generate HTML viewer | `true` |
| `archive_versions` | Save uniquely versioned PDFs | `true` |

## Outputs

| Output | Description |
|---|---|
| `pdf_path` | Absolute path to generated PDF |
| `version` | Generated version identifier |
| `site_dir` | Absolute path to output directory |

## Generated structure

```text
public/
├── index.html
├── latest.json
└── versions/
    ├── resume-<version-1>.pdf
    └── resume-<version-2>.pdf
```

## Version persistence

ResumeForge never deletes previous versions.

To preserve archives across GitHub Actions runs, commit the generated `public/` directory to your repository or store it in another persistent storage system.

GitHub Actions artifacts alone are temporary and do not automatically preserve files between workflow runs.

## License

MIT