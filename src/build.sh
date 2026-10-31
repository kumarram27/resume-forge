
#!/usr/bin/env bash
set -euo pipefail

WORKSPACE="${GITHUB_WORKSPACE:-$PWD}"

PDF_FILE="${PDF_FILE:-resume.pdf}"
OUTPUT_DIR="${OUTPUT_DIR:-public}"

if [[ "$PDF_FILE" = /* ]]; then
    PDF_SOURCE="$PDF_FILE"
else
    PDF_SOURCE="$WORKSPACE/$PDF_FILE"
fi

if [[ ! -s "$PDF_SOURCE" ]]; then
    echo "::error::Compiled PDF not found or empty: $PDF_SOURCE"
    exit 1
fi

if [[ "$OUTPUT_DIR" = /* ]]; then
    SITE_DIR="$OUTPUT_DIR"
else
    SITE_DIR="$WORKSPACE/$OUTPUT_DIR"
fi

mkdir -p "$SITE_DIR"

TIMESTAMP="$(date -u +%Y%m%d-%H%M%S)"
SHORT_SHA="${GITHUB_SHA:-local}"
SHORT_SHA="${SHORT_SHA:0:7}"

VERSION="${TIMESTAMP}-${SHORT_SHA}"
PDF_NAME="resume-${VERSION}.pdf"
PDF_DEST="$SITE_DIR/$PDF_NAME"

# Remove previously generated ResumeForge PDFs.
find "$SITE_DIR" -maxdepth 1 -type f -name 'resume-*.pdf' -delete

cp "$PDF_SOURCE" "$PDF_DEST"

UPDATED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

python3 - "$SITE_DIR/latest.json" "$VERSION" "$PDF_NAME" "$UPDATED_AT" <<'PY'
import json
import sys

output, version, filename, updated_at = sys.argv[1:]

manifest = {
    "version": version,
    "file": filename,
    "updated_at": updated_at,
}

with open(output, "w", encoding="utf-8") as f:
    json.dump(manifest, f, indent=2)
    f.write("\n")
PY

if [[ -n "${GITHUB_OUTPUT:-}" ]]; then
    {
        echo "pdf_path=$PDF_DEST"
        echo "version=$VERSION"
        echo "site_dir=$SITE_DIR"
    } >> "$GITHUB_OUTPUT"
fi

echo "ResumeForge packaging completed."
echo "Version: $VERSION"
echo "PDF: $PDF_DEST"
echo "Output directory: $SITE_DIR"
