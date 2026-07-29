"""Рендерит web/widget.html и web/reviews.json из data/reviews.json."""
from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone

CURRENT_YEAR = datetime.now(tz=timezone.utc).year
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


AVATAR_PALETTE = [
    "#e57373",  # red
    "#f06292",  # pink
    "#ba68c8",  # purple
    "#9575cd",  # deep purple
    "#7986cb",  # indigo
    "#64b5f6",  # blue
    "#4fc3f7",  # light blue
    "#4dd0e1",  # cyan
    "#4db6ac",  # teal
    "#81c784",  # green
    "#aed581",  # light green
    "#ffb74d",  # orange
    "#ff8a65",  # deep orange
    "#a1887f",  # brown
    "#90a4ae",  # blue grey
]


def enrich(reviews: list[dict]) -> list[dict]:
    """Оставляем только отзывы с оценкой, готовим поля для рендера."""
    out = []
    for r in reviews:
        if not r.get("score"):
            continue
        date_full = normalize_date(r.get("date") or "")
        author = (r.get("author") or "?").strip()
        # детерминированный цвет: по id (стабильно при перегенерации)
        seed = int(r.get("id") or abs(hash(author)))
        avatar_color = AVATAR_PALETTE[seed % len(AVATAR_PALETTE)]
        out.append({
            **r,
            "score_int": int(r["score"]),
            "stars_full": range(int(r["score"])),
            "stars_empty": range(5 - int(r["score"])),
            "text": (r.get("text") or "").strip(),
            "date_full": date_full,
            "verified": (r.get("stage") or "") == "Сделка состоялась",
            "initial": author[:1].upper(),
            "avatar_color": avatar_color,
        })
    return out


def compute_avg(rating_stat: list[dict]) -> float:
    """Считаем средний рейтинг из распределения оценок (API отдаёт только округлённое до целого)."""
    total_score = sum((r.get("score") or 0) * (r.get("count") or 0) for r in rating_stat)
    total_count = sum((r.get("count") or 0) for r in rating_stat)
    if not total_count:
        return 0.0
    return round(total_score / total_count, 1)


def normalize_date(date: str) -> str:
    """Свежие отзывы Avito отдаёт без года — досыпаем текущий."""
    date = date.strip()
    if not date:
        return ""
    # уже с годом — оставляем как есть
    parts = date.split()
    if len(parts) >= 3 and parts[-1].isdigit():
        return date
    return f"{date} {CURRENT_YEAR}"


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

    avg = compute_avg(summary.get("ratingStat") or [])
    total = summary.get("reviewCount") or len(reviews)

    html = tpl.render(
        reviews=reviews,
        summary=summary,
        avg=avg,                                    # дробное число, напр. 4.8
        avg_str=f"{avg:.1f}".replace(".", ","),     # для отображения: "4,8"
        avg_stars_full=int(round(avg)),             # для звёзд-иконок
        total=total,
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
