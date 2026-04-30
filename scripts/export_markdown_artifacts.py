from __future__ import annotations

import subprocess
from os.path import relpath
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STYLE_PATH = ROOT / "docs" / "markdown-export.css"
EXCLUDED_PARTS = {
    ".codex",
    ".git",
    ".pytest_cache",
    "node_modules",
    "dist",
    "build",
    "__pycache__",
}


def run_pandoc(source: Path, target: Path, extra_args: list[str]) -> None:
    command = [
        "pandoc",
        str(source),
        "--from",
        "gfm",
        "--standalone",
        "--output",
        str(target),
        *extra_args,
    ]
    subprocess.run(command, check=True, cwd=ROOT)


def export_markdown(source: Path) -> None:
    relative_source = source.relative_to(ROOT)
    html_target = source.with_suffix(".html")
    docx_target = source.with_suffix(".docx")
    title = source.stem.replace("-", " ").replace("_", " ").title()

    print(f"Exporting {relative_source}")
    run_pandoc(
        source,
        html_target,
        [
            "--metadata",
            f"title={title}",
            "--css",
            relpath(STYLE_PATH, start=source.parent),
        ],
    )
    run_pandoc(
        source,
        docx_target,
        [
            "--metadata",
            f"title={title}",
            "--toc",
        ],
    )


def main() -> None:
    markdown_files = sorted(ROOT.rglob("*.md"))
    for source in markdown_files:
        if EXCLUDED_PARTS.intersection(source.parts):
            continue
        export_markdown(source)


if __name__ == "__main__":
    main()
