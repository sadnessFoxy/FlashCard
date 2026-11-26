#!/usr/bin/env bash
# Back up the database and the uploaded files; keep the last 7 days.
# Runs daily from cron (setup.sh). Restore steps: docs/DEPLOY_ORACLE.md.
set -euo pipefail

DEPLOY_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKUP_DIR=/opt/flashcard-backups
STAMP="$(date +%Y%m%d-%H%M)"
mkdir -p "$BACKUP_DIR"
cd "$DEPLOY_DIR"

docker compose exec -T postgres pg_dump -U flashcard -d flashcard --format=custom \
  > "$BACKUP_DIR/db-$STAMP.dump"
docker run --rm -v flashcard_s3_data:/data:ro -v "$BACKUP_DIR":/backup alpine \
  tar czf "/backup/files-$STAMP.tar.gz" -C /data .

find "$BACKUP_DIR" -type f -mtime +7 -delete
echo "$(date -Is) backup ok: db-$STAMP.dump files-$STAMP.tar.gz"
