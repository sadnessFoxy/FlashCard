#!/usr/bin/env bash
# Make an already registered account an admin.
# Usage: sudo bash infra/deploy/admin.sh you@example.com
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Usage: sudo bash infra/deploy/admin.sh you@example.com" >&2
  exit 1
fi
cd "$(dirname "$0")"
docker compose exec -T api python -m app.scripts.create_admin "$1"
