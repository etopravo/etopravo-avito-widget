#!/bin/bash
# Локальный cron: fetch → render → git push
# Запускается launchd раз в 6 часов на макбуке Руслана.
# IP: домашний → API Авито работает.
# После push → GitHub Actions деплоит на Pages.
set -euo pipefail

REPO="$HOME/etopravo-avito-widget"
cd "$REPO"

LOG="$REPO/data/last-run.log"
{
  echo "=== $(date -u '+%Y-%m-%d %H:%M:%S UTC') ==="

  # синхронизируемся с remote (мог быть коммит от manual правки)
  git fetch origin main --quiet
  git rebase origin/main || {
    echo "[cron] rebase conflict — auto-resolving in favor of local"
    git checkout --theirs data/reviews.json web/widget.html web/reviews.json 2>/dev/null || true
    git add data/reviews.json web/widget.html web/reviews.json
    git rebase --continue || git rebase --abort
  }

  "$REPO/.venv/bin/python" scripts/fetch_reviews.py
  "$REPO/.venv/bin/python" scripts/render_widget.py

  git add data/reviews.json web/widget.html web/reviews.json
  if git diff --cached --quiet; then
    echo "[cron] no changes"
    exit 0
  fi
  git commit -m "chore(reviews): auto-update $(date -u +'%Y-%m-%d %H:%M UTC')"
  git push
  echo "[cron] pushed"
} 2>&1 | tee -a "$LOG"
