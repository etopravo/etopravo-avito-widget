"""Тянет отзывы Авито через публичный JSON-API и сохраняет в data/reviews.json."""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

from curl_cffi import requests as curl_requests

SELLER_ID = "82f01ddee3ca0ba1e640be54f3f4efa4"
IMPERSONATE = "chrome131"
API_URL = "https://www.avito.ru/web/7/user/{seller_id}/ratings"
PAGE_SIZE = 25
MAX_PAGES = 20
REQUEST_DELAY_SEC = 1.5
TIMEOUT_SEC = 20
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "reviews.json"


def fetch_page(session: curl_requests.Session, offset: int) -> dict:
    params = {
        "limit": PAGE_SIZE,
        "offset": offset,
        "photoOnly": "false",
        "sortRating": "date_desc",
    }
    resp = session.get(
        API_URL.format(seller_id=SELLER_ID),
        params=params,
        timeout=TIMEOUT_SEC,
    )
    resp.raise_for_status()
    return resp.json()


def extract_summary(entries: list[dict]) -> dict:
    for e in entries:
        if e.get("type") == "score":
            v = e["value"]
            return {
                "score": v.get("score"),
                "reviewCount": v.get("reviewCount"),
                "ratingStat": v.get("ratingStat", []),
            }
    return {}


def extract_reviews(entries: list[dict]) -> list[dict]:
    out = []
    for e in entries:
        if e.get("type") != "rating":
            continue
        v = e["value"]
        text_parts = [t.get("text", "") for t in v.get("textSections", [])]
        out.append({
            "id": v.get("id"),
            "author": v.get("title"),
            "role": v.get("titleCaption"),
            "date": v.get("rated"),
            "score": v.get("score"),
            "stage": v.get("stageTitle"),
            "service": v.get("itemTitle"),
            "text": "\n".join(text_parts).strip(),
            "avatar": v.get("avatar", {}).get("100x100"),
        })
    return out


def main() -> int:
    headers = {
        "Accept": "application/json",
        "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
        "Referer": "https://www.avito.ru/",
    }

    reviews: list[dict] = []
    summary: dict = {}

    session = curl_requests.Session(impersonate=IMPERSONATE, headers=headers)

    # прогреваем сессию: первый заход на главную даёт куки от anti-bot
    session.get("https://www.avito.ru/", timeout=TIMEOUT_SEC)

    try:
        for page in range(MAX_PAGES):
            offset = page * PAGE_SIZE
            print(f"[fetch] page={page + 1} offset={offset}", flush=True)
            try:
                data = fetch_page(session, offset)
            except curl_requests.HTTPError as exc:
                status = getattr(exc.response, "status_code", "?")
                print(f"[error] HTTP {status} at offset={offset}", flush=True)
                if status in (429, 403):
                    print("[error] rate-limit / blocked — abort", flush=True)
                    return 2
                raise
            entries = data.get("entries", [])
            if page == 0:
                summary = extract_summary(entries)
                print(f"[summary] {summary}", flush=True)
            page_reviews = extract_reviews(entries)
            reviews.extend(page_reviews)
            print(f"[fetch] got {len(page_reviews)} reviews (total {len(reviews)})", flush=True)
            if len(page_reviews) < PAGE_SIZE:
                break
            if summary.get("reviewCount") and len(reviews) >= summary["reviewCount"]:
                break
            time.sleep(REQUEST_DELAY_SEC)
    finally:
        session.close()

    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "updatedAt": int(time.time()),
        "sellerId": SELLER_ID,
        "summary": summary,
        "reviews": reviews,
    }
    DATA_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[done] saved {len(reviews)} reviews → {DATA_PATH}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
