"""Build a compact, explicitly selected source and evidence archive without raw data."""

import hashlib
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

ROOT = Path(__file__).resolve().parents[1]
DESTINATION = ROOT / "report" / "swarmtrace_artifact.zip"


def selected_files():
    files = {
        ROOT / p
        for p in ["README.md", "pyproject.toml", "uv.lock", ".python-version", ".gitattributes", ".gitignore"]
    }
    for folder, patterns in {
        "src": ["**/*.py"],
        "tests": ["*.py"],
        "docs": ["*.md", "*.json"],
        "data": ["README.md"],
        "outputs": ["*.csv", "*.json", "*.npz"],
        "outputs/figures": ["paper_*.png", "paper_*.pdf", "paper_*.svg", "figure1_live_surface.png"],
        "report": ["*.py", "*.md", "*.json", "swarmtrace_paper.pdf", "swarmtrace_paper.docx"],
    }.items():
        for pattern in patterns:
            files.update((ROOT / folder).glob(pattern))
    # Keep the personal submission checklist outside the distributable research artifact.
    files.discard(ROOT / "report" / "author-review.md")
    return sorted(files)


def build():
    payload = {str(p.relative_to(ROOT)): p.read_bytes() for p in selected_files()}
    payload["BUNDLE_README.txt"] = (
        b"SwarmTrace source and evidence archive\n\n"
        b"Start with README.md and report/swarmtrace_paper.pdf.\n"
        b"The archive excludes raw data, Git history, caches and the original template.\n"
        b"Read data/README.md for the pinned public source and required hashes.\n"
        b"Run the analysis with --with-temporal-audit to regenerate the large hourly\n"
        b"trace archive, which is omitted here; all hourly summary tables are included.\n"
        b"The source works without Git metadata. The run manifest records the source\n"
        b"hashes at analysis time; it also lists regenerated files outside this bundle.\n"
        b"Rebuilding the paper requires the original local Apart DOCX template.\n"
        b"BUNDLE_MANIFEST.json lists SHA-256 hashes of every other bundled file.\n"
    )
    manifest = {
        name: hashlib.sha256(data).hexdigest() for name, data in sorted(payload.items())
    }
    payload["BUNDLE_MANIFEST.json"] = (json.dumps(manifest, indent=2) + "\n").encode()
    with ZipFile(DESTINATION, "w", compression=ZIP_DEFLATED, compresslevel=9) as archive:
        for name, data in sorted(payload.items()):
            entry = ZipInfo(name, date_time=(2026, 9, 12, 0, 0, 0))
            entry.compress_type = ZIP_DEFLATED
            entry.external_attr = 0o644 << 16
            archive.writestr(entry, data)
    with ZipFile(DESTINATION) as archive:
        assert archive.testzip() is None
        for name, expected in manifest.items():
            assert hashlib.sha256(archive.read(name)).hexdigest() == expected
        assert not any("template" in name.lower() for name in archive.namelist())
    print(f"{DESTINATION}: {len(payload)} files, {DESTINATION.stat().st_size:,} bytes")


if __name__ == "__main__":
    build()
