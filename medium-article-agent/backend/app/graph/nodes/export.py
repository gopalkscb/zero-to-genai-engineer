"""Export node — markdown, HTML, clipboard payload."""

from __future__ import annotations

from pathlib import Path
import re

import markdown

from app.editorial.skills import apply_deterministic_fixes
from app.config import get_settings
from app.graph.images import inject_images
from app.graph.state import AgentState, ExportArtifacts, LogEntry, LogLevel, PipelineStatus
from app.utils.dash_check import assert_no_em_en_dash

_IMG_BLOCK = re.compile(
    r"<p>\s*<img([^>]+)>\s*</p>(?:\s*<p><em>(.*?)</em></p>)?",
    re.IGNORECASE | re.DOTALL,
)


def _attr(attrs: str, name: str) -> str:
    match = re.search(rf'{name}="([^"]*)"', attrs, re.IGNORECASE)
    return match.group(1) if match else ""


def html_with_figures(html: str) -> str:
    def repl(match: re.Match[str]) -> str:
        attrs = match.group(1)
        echoed = (match.group(2) or "").strip()
        alt = _attr(attrs, "alt") or echoed
        src = _attr(attrs, "src")
        caption = f"<figcaption>{alt}</figcaption>" if alt else ""
        return f'<figure class="medium-figure"><img src="{src}" alt="{alt}">{caption}</figure>'

    return _IMG_BLOCK.sub(repl, html)


def export_node(state: AgentState) -> dict:
    settings = get_settings()
    run_id = state.get("run_id", "unknown")
    md_text = state.get("final_markdown", state.get("draft_markdown", ""))
    md_text = apply_deterministic_fixes(md_text)
    md_text = inject_images(md_text, state.get("images") or [])

    violations = assert_no_em_en_dash(md_text)
    if violations:
        from app.utils.dash_check import strip_em_en_dashes
        md_text = strip_em_en_dashes(md_text)

    html = html_with_figures(markdown.markdown(md_text, extensions=["fenced_code", "tables"]))
    medium_html = f"""<article class="medium-article">
{html}
</article>"""

    export_dir = Path(settings.data_dir) / "runs" / run_id / "export"
    export_dir.mkdir(parents=True, exist_ok=True)
    md_path = export_dir / "article.md"
    html_path = export_dir / "article.html"
    md_path.write_text(md_text, encoding="utf-8")
    html_path.write_text(medium_html, encoding="utf-8")

    artifacts = ExportArtifacts(
        markdown=md_text,
        html=medium_html,
        clipboard_text=md_text,
        export_path=str(export_dir),
    )

    return {
        "export": artifacts,
        "status": PipelineStatus.COMPLETED,
        "logs": [
            LogEntry(
                node="export",
                level=LogLevel.INFO,
                message=f"Exported to {export_dir}",
            )
        ],
    }
