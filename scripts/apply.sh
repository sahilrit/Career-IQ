#!/usr/bin/env bash
# One-tap CareerOS auto-apply.
#
# Run it with:   bash scripts/apply.sh
#
# It asks you to paste your Render *External* Database URL once, then runs a
# single visible cycle against your live account — a browser window opens and
# works through jobs, applying to open forms and holding login/captcha ones.
set -euo pipefail

# Always run from the repo root, wherever this script is called from.
cd "$(dirname "$0")/.."

# Your workspace (baked in so you don't have to type it). Override by running
# CAREEROS_WORKSPACE_ID=... bash scripts/apply.sh
WORKSPACE_ID="${CAREEROS_WORKSPACE_ID:-72c51f62-10b3-4017-9884-99707ab6b8e9}"

echo "CareerOS auto-apply"
echo "-------------------"
echo "Paste your Render EXTERNAL Database URL below and press Enter."
echo "Find it: Render dashboard -> your Postgres database -> 'External Database URL'"
echo "(It starts with postgres:// and is a long line.)"
echo
printf "Database URL: "
read -r DB_URL

case "$DB_URL" in
  postgres://*|postgresql://*) ;;
  *)
    echo
    echo "That doesn't look like a postgres:// URL. Re-run and paste the"
    echo "'External Database URL' from Render (not the internal one)."
    exit 1
    ;;
esac

export CAREEROS_DATABASE_URL="$DB_URL"

echo
echo "Optional: paste an AI key to have the AI write cover letters + answer"
echo "screening questions — Groq (gsk_…, fast + free) or Google Gemini (AIza…)."
echo "Or just press Enter to use built-in templates."
printf "AI key (optional): "
read -r AI_KEY
if [ -n "$AI_KEY" ]; then
  export CAREEROS_AI_KEY="$AI_KEY"
fi

echo
echo "Choose a mode:"
echo "  [1] Assisted apply — fill every form (basics, résumé, cover letter,"
echo "      screening questions), then pause so YOU review and click submit"
echo "      (recommended — nothing is submitted without your click)"
echo "  [2] Prepare & review — same filling, but queued to your web Review page"
echo "      to finish later instead of pausing at the terminal"
printf "Mode [1/2, default 1]: "
read -r MODE

echo
echo "Making sure the browser is installed (one-time, safe to repeat)..."
uv run playwright install chromium >/dev/null 2>&1 || true

echo
echo "Running one cycle for workspace $WORKSPACE_ID. A Chrome window will open."
echo
if [ "$MODE" = "2" ]; then
  uv run python scripts/autopilot_daemon.py --workspace-id "$WORKSPACE_ID" --once --review
else
  uv run python scripts/autopilot_daemon.py --workspace-id "$WORKSPACE_ID" --once --assist
fi
