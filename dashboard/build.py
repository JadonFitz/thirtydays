#!/usr/bin/env python3
"""Build script: reads research/*.md → dashboard/dist/data.json"""
import json, os, re, shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent
RESEARCH_DIR = ROOT / "research"
DIST_DIR = Path(__file__).parent / "dist"

CATEGORIES = {
    "crypto": {
        "name": "Crypto Trading",
        "color": "#00ff88",
        "description": "Sentiment, altcoin rotation, macro signals, on-chain narratives",
        "prompts": [
            "/last30days BTC market sentiment",
            "/last30days ETH DeFi narrative",
            "/last30days altcoin season signals",
            "/last30days crypto macro correlation",
            "/last30days crypto whale moves",
            "/last30days SOL ecosystem updates",
            "/last30days hyperliquid perpetuals",
            "/last30days SUI ecosystem momentum",
        ],
        "keywords": ["bitcoin", "ethereum", "solana", "chainlink", "sui", "tron",
                     "hyperliquid", "render", "fed-rate", "crypto", "btc", "eth",
                     "defi", "altcoin", "rndr", "hype"],
    },
    "video_clients": {
        "name": "Video Client Acquisition",
        "color": "#4488ff",
        "description": "Brands in LA seeking video partners, buyer signals, retainer intel",
        "prompts": [
            "/last30days brand video production Los Angeles",
            "/last30days video retainer agency 2026",
            "/last30days content marketing video ROI",
            "/last30days corporate video trends 2026",
            "/last30days brand storytelling video strategy",
            "/last30days startup brand video",
        ],
        "keywords": ["video-production", "brand-video", "commercial", "content-marketing",
                     "los-angeles", "retainer", "corporate-video"],
    },
    "ntc": {
        "name": "New Terrain Creative",
        "color": "#ff8844",
        "description": "Agency positioning, pricing, differentiation, founder moves",
        "prompts": [
            "/last30days video production agency pricing 2026",
            "/last30days creative agency differentiation",
            "/last30days video production studio growth",
            "/last30days content agency retainer model",
            "/last30days filmmaker entrepreneur",
        ],
        "keywords": ["agency", "creative-agency", "terrain", "studio-growth", "retainer-model"],
    },
    "personal_brand": {
        "name": "Personal Brand",
        "color": "#cc44ff",
        "description": "Platform trends, filmmaker content strategy, what's resonating",
        "prompts": [
            "/last30days filmmaker personal brand",
            "/last30days content creator monetization 2026",
            "/last30days LinkedIn video creator",
            "/last30days filmmaker YouTube strategy",
            "/last30days creative director personal brand",
        ],
        "keywords": ["filmmaker", "personal-brand", "creator", "linkedin", "youtube-strategy",
                     "content-creator"],
    },
}

KEYWORD_FLAT = {kw: cat_key for cat_key, cat in CATEGORIES.items() for kw in cat["keywords"]}


def categorize(filename: str) -> str:
    fn = filename.lower().replace("_", "-")
    for kw, cat in KEYWORD_FLAT.items():
        if kw.replace("-", "") in fn.replace("-", ""):
            return cat
    return "crypto"


def extract_date(filename: str):
    m = re.search(r"(\d{4}-\d{2}-\d{2})", filename)
    return m.group(1) if m else None


def display_name(stem: str) -> str:
    name = re.sub(r"-raw-v\d+", "", stem)
    name = re.sub(r"-\d{4}-\d{2}-\d{2}$", "", name)
    return name.replace("-", " ").title()


def main():
    DIST_DIR.mkdir(parents=True, exist_ok=True)

    files = []
    if RESEARCH_DIR.exists():
        for path in sorted(RESEARCH_DIR.glob("*.md"), reverse=True):
            content = path.read_text(encoding="utf-8", errors="replace")
            preview_lines = [
                l for l in content.splitlines()
                if l.strip() and not l.startswith("#") and not l.startswith("---")
                and not l.startswith(">") and not l.startswith("-  Date")
                and not l.startswith("- Date") and not l.startswith("- Source")
            ]
            files.append({
                "filename": path.name,
                "display_name": display_name(path.stem),
                "category": categorize(path.name),
                "date": extract_date(path.name),
                "preview": " ".join(preview_lines[:2])[:200],
                "content": content,
            })

    data = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "categories": CATEGORIES,
        "files": files,
    }

    out = DIST_DIR / "data.json"
    out.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    print(f"Wrote {out} ({len(files)} files)")

    src_html = Path(__file__).parent / "index.html"
    shutil.copy(src_html, DIST_DIR / "index.html")
    print(f"Copied index.html → dist/")


if __name__ == "__main__":
    main()
