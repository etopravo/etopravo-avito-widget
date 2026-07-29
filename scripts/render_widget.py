"""Рендерит web/widget.html и web/reviews.json из data/reviews.json."""
from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "reviews.json"
TEMPLATES_DIR = ROOT / "scripts" / "templates"
WEB_DIR = ROOT / "web"

# ссылка «Оставить отзыв» — ведёт на страницу продавца с открытой модалкой
LEAVE_REVIEW_URL = (
    "https://www.avito.ru/brands/etopravo/all"
    "?sellerId=82f01ddee3ca0ba1e640be54f3f4efa4#open-reviews"
)


def load() -> dict:
    return json.loads(DATA_PATH.read_text(encoding="utf-8"))


def enrich(reviews: list[dict]) -> list[dict]:
    """Оставляем только отзывы с оценкой, готовим поля для рендера."""
    out = []
    for r in reviews:
        if not r.get("score"):
            continue
        out.append({
            **r,
            "score_int": int(r["score"]),
            "stars_full": range(int(r["score"])),
            "stars_empty": range(5 - int(r["score"])),
            "text": (r.get("text") or "").strip(),
            "text_short": short_text(r.get("text") or "", 240),
            "needs_more": len((r.get("text") or "").strip()) > 240,
        })
    return out


def short_text(text: str, limit: int) -> str:
    text = text.strip()
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(" ", 1)[0]
    return cut + "…"


def render() -> None:
    payload = load()
    reviews = enrich(payload["reviews"])
    summary = payload.get("summary", {}) or {}

    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html"]),
    )
    tpl = env.get_template("widget.html.j2")
    updated_at = datetime.fromtimestamp(payload["updatedAt"], tz=timezone.utc)

    html = tpl.render(
        reviews=reviews,
        summary=summary,
        avg=summary.get("score") or 0,
        total=summary.get("reviewCount") or len(reviews),
        leave_url=LEAVE_REVIEW_URL,
        updated_at=updated_at.strftime("%Y-%m-%d %H:%M UTC"),
    )

    WEB_DIR.mkdir(parents=True, exist_ok=True)
    (WEB_DIR / "widget.html").write_text(html, encoding="utf-8")

    # ещё раздаём сам JSON — вдруг пригодится
    shutil.copyfile(DATA_PATH, WEB_DIR / "reviews.json")

    print(f"[render] {len(reviews)} reviews → {WEB_DIR / 'widget.html'}")


if __name__ == "__main__":
    render()
