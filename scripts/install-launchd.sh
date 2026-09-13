#!/usr/bin/env bash
# Install the launchd agent that runs the preprint intern every Thursday (sends biweekly).
# Idempotent: re-run after changes to update. No hardcoded paths: substitutes yours into the template.
set -euo pipefail

REPO_PATH="$(cd "$(dirname "$0")/.." && pwd)"
LABEL="com.preprintjudge.intern"
TEMPLATE="${REPO_PATH}/launchd/preprint-intern.plist.template"
INSTALL_PATH="${HOME}/Library/LaunchAgents/${LABEL}.plist"

UV_PATH="$(command -v uv || true)"
[[ -n "$UV_PATH" ]] || { echo "error: 'uv' not found in PATH" >&2; exit 1; }
CREDS="${HOME}/.preprint-judge/credentials.json"
[[ -f "$CREDS" ]] || { echo "error: $CREDS missing (see credentials.json.example)" >&2; exit 1; }
# launchd starts no shell, so nothing sources .env: the key has to be in the credentials file.
grep -q '"openrouter_api_key"' "$CREDS" || { echo "error: add \"openrouter_api_key\" to $CREDS" >&2; exit 1; }

if launchctl list "$LABEL" >/dev/null 2>&1; then
    launchctl unload "$INSTALL_PATH" 2>/dev/null || true
fi
mkdir -p "${HOME}/.preprint-judge" "${HOME}/Library/LaunchAgents"
sed -e "s|__UV_PATH__|${UV_PATH}|g" -e "s|__REPO_PATH__|${REPO_PATH}|g" -e "s|__HOME__|${HOME}|g" \
    "$TEMPLATE" > "$INSTALL_PATH"
launchctl load "$INSTALL_PATH"

echo "Installed: $INSTALL_PATH"
echo "Force a run:  launchctl start $LABEL"
echo "Logs:         ~/.preprint-judge/intern.log and launchd.*.log"
echo "Uninstall:    launchctl unload $INSTALL_PATH && rm $INSTALL_PATH"
