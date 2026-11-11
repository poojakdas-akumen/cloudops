#!/usr/bin/env bash
set -euo pipefail
ARCHIVE="${1:?Usage: deploy.sh /tmp/cloudops-task-manager.tar.gz}"
APP_DIR="/opt/cloudops-task-manager/app"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

tar -xzf "$ARCHIVE" -C "$TMP_DIR"
rm -rf "$APP_DIR"
mkdir -p "$APP_DIR"
cp -a "$TMP_DIR"/. "$APP_DIR"/
chown -R cloudops:www-data /opt/cloudops-task-manager
python3 -m venv /opt/cloudops-task-manager/venv
/opt/cloudops-task-manager/venv/bin/pip install --upgrade pip
/opt/cloudops-task-manager/venv/bin/pip install -r "$APP_DIR/requirements.txt"
systemctl restart cloudops-task-manager
sleep 2
systemctl is-active --quiet cloudops-task-manager
curl --fail --silent http://127.0.0.1:8000/health
echo
