"""Static site exporter so KiboFlow Studio + Client Demos deploy to GitHub Pages for $0/month."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from kiboflow import COMPANY_PROFILE
from kiboflow.data_seed import DECISIONS_SEED, LEADS_SEED, PACKAGES_SEED
from kiboflow.server import WEB_DIR


def export_static_site(output_dir: Path) -> Path:
    """Export KiboFlow Studio public storefront, demos, and static JSON snapshots for GitHub Pages."""
    out = output_dir.resolve()
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)

    shutil.copytree(WEB_DIR, out, dirs_exist_ok=True)
    # Create clean directory index routes (/ops/index.html, /demos/hospitality/index.html, etc.)
    ops_dir = out / "ops"
    ops_dir.mkdir(exist_ok=True)
    shutil.copy2(out / "ops.html", ops_dir / "index.html")

    for demo_slug in ("hospitality", "clinic", "hardware"):
        demo_subdir = out / "demos" / demo_slug
        demo_subdir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(out / "demos" / f"{demo_slug}.html", demo_subdir / "index.html")

    # Pre-baked JSON fallback so static hosting works even without the Python backend
    static_api = out / "static_data"
    static_api.mkdir(exist_ok=True)
    (static_api / "bootstrap.json").write_text(
        json.dumps(
            {
                "company": COMPANY_PROFILE,
                "packages": PACKAGES_SEED,
                "leads": LEADS_SEED,
                "decisions": DECISIONS_SEED,
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (out / ".nojekyll").write_text("", encoding="utf-8")
    return out
