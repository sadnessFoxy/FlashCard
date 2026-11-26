#!/usr/bin/env bash
# Deploy the latest code from GitHub (docs/DEPLOY_ORACLE.md, "Cập nhật").
# Usage: sudo bash infra/deploy/update.sh
set -euo pipefail

DEPLOY_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DEPLOY_DIR/../.."

echo "==> Backup before updating"
bash "$DEPLOY_DIR/backup.sh"

echo "==> Pulling the latest code"
git pull --ff-only

echo "==> Rebuilding; migrations run before the API restarts"
cd "$DEPLOY_DIR"
docker compose up -d --build
docker image prune -f >/dev/null
docker compose ps
