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
echo "Optional: paste your Google Gemini key (AIza…) to have the AI write each"
echo "cover letter, or just press Enter to use built-in templates."
printf "Gemini key (optional): "
read -r AI_KEY
if [ -n "$AI_KEY" ]; then
  export CAREEROS_AI_KEY="$AI_KEY"
fi

echo
echo "Making sure the browser is installed (one-time, safe to repeat)..."
uv run playwright install chromium >/dev/null 2>&1 || true

echo
echo "Running one cycle for workspace $WORKSPACE_ID."
echo "A Chrome window will open — you can watch it work. Applied jobs print as"
echo "APPLIED, and login/captcha jobs print as 'held' with a reason."
echo
uv run python scripts/autopilot_daemon.py --workspace-id "$WORKSPACE_ID" --once --show-browser
