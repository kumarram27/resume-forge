"""
pdf.py - Convert an HTML string to a PDF file using WeasyPrint.

WeasyPrint may fail to fetch remote fonts in restricted CI environments.
The templates use system-font fallbacks so the PDF will still render cleanly
even when the Google Fonts CDN is unreachable.
"""

from __future__ import annotations

from pathlib import Path


def generate_pdf(html: str, output_path: str | Path, base_url: str | None = None) -> Path:
    """
    Render *html* to a PDF file at *output_path*.

    Parameters
    ----------
    html:
        Complete HTML document string.
    output_path:
        Destination file path (parent directories must exist).
    base_url:
        Base URL / filesystem path that WeasyPrint uses to resolve relative
        URLs (CSS, fonts).  Defaults to the templates directory embedded in
        the renderer package.

    Returns
    -------
    Path
        Absolute path to the written PDF.

    Raises
    ------
    SystemExit(1)
        On WeasyPrint failure, a human-readable error is printed and the
        process exits with code 1.  A raw stack trace is intentionally
        suppressed so CI logs stay readable.
    """
    from pathlib import Path as _Path  # local import to defer weasyprint load

    output_path = _Path(output_path).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if base_url is None:
        # Default: templates directory next to this package
        base_url = str(_Path(__file__).parent.parent / "templates")

    # Ensure base_url is a proper file:// URL so WeasyPrint resolves correctly
    if not base_url.startswith(("http://", "https://", "file://")):
        base_url = _Path(base_url).as_uri() + "/"

    try:
        from weasyprint import HTML  # type: ignore[import]

        print(f"[ResumeForge] Generating PDF → {output_path}")
        HTML(string=html, base_url=base_url).write_pdf(str(output_path))
        print(f"[ResumeForge] PDF written successfully ({output_path.stat().st_size // 1024} KB)")
        return output_path

    except ImportError:
        import sys
        print(
            "[ResumeForge] ERROR: WeasyPrint is not installed.\n"
            "  Run: pip install weasyprint"
        )
        sys.exit(1)

    except Exception as exc:  # noqa: BLE001
        import sys
        # Extract a short, readable summary from the exception
        msg = str(exc)
        if len(msg) > 300:
            msg = msg[:297] + "..."
        print(
            f"[ResumeForge] ERROR: PDF generation failed.\n"
            f"  Reason: {msg}\n"
            f"  Output path: {output_path}\n"
            f"  Tip: Check that your resume Markdown is valid and the template CSS is correct."
        )
        sys.exit(1)

