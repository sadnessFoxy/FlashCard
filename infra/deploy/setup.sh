#!/usr/bin/env bash
# First install on a fresh Ubuntu server (docs/DEPLOY_ORACLE.md, step 4).
# Usage, from the repo folder:  sudo bash infra/deploy/setup.sh
# Safe to run again: existing secrets in infra/deploy/.env are kept.
set -euo pipefail

DEPLOY_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(cd "$DEPLOY_DIR/../.." && pwd)"
ENV_FILE="$DEPLOY_DIR/.env"
BACKUP_DIR=/opt/flashcard-backups

say() { printf '\n\033[1;32m==> %s\033[0m\n' "$1"; }

if [[ $EUID -ne 0 ]]; then
  echo "Run with sudo: sudo bash infra/deploy/setup.sh" >&2
  exit 1
fi

say "1/6 Installing Docker"
if ! command -v docker >/dev/null 2>&1; then
  curl -fsSL https://get.docker.com | sh
fi
systemctl enable --now docker
if [[ -n "${SUDO_USER:-}" ]]; then usermod -aG docker "$SUDO_USER" || true; fi

say "2/6 Opening ports 80 and 443 in the server firewall"
# Oracle's Ubuntu images reject everything except SSH in iptables.
for port in 80 443; do
  iptables -C INPUT -p tcp --dport "$port" -j ACCEPT 2>/dev/null \
    || iptables -I INPUT 1 -p tcp --dport "$port" -j ACCEPT
done
iptables -C INPUT -p udp --dport 443 -j ACCEPT 2>/dev/null \
  || iptables -I INPUT 1 -p udp --dport 443 -j ACCEPT
if command -v netfilter-persistent >/dev/null 2>&1; then
  netfilter-persistent save
else
  DEBIAN_FRONTEND=noninteractive apt-get install -y iptables-persistent >/dev/null
  netfilter-persistent save
fi

say "3/6 Writing settings and secrets (infra/deploy/.env)"
if [[ ! -f "$ENV_FILE" ]]; then
  ip="$(curl -fsS https://api.ipify.org || true)"
  default_site="${ip//./-}.sslip.io"
  read -r -p "Web address [${default_site}]: " site < /dev/tty
  site="${site:-$default_site}"
  read -r -p "Your email (certificate notices, Resend account email): " email < /dev/tty
  read -r -s -p "Gemini API key (hidden): " gemini < /dev/tty; echo
  read -r -s -p "Resend API key (hidden, Enter to skip for now): " resend < /dev/tty; echo
  rand() { openssl rand -hex "$1"; }
  umask 077
  cat > "$ENV_FILE" <<EOF
# Written by setup.sh. NEVER commit this file.
SITE_ADDRESS=${site}
ACME_EMAIL=${email}

SECRET_KEY=$(rand 32)
POSTGRES_PASSWORD=$(rand 24)
GEMINI_API_KEY=${gemini}

S3_BUCKET_NAME=flashcard
S3_ACCESS_KEY=$(rand 12)
S3_SECRET_KEY=$(rand 24)

# Email through Resend (https://resend.com). Without your own domain Resend only
# delivers to your own account email (docs/DEPLOY_ORACLE.md).
SMTP_HOST=smtp.resend.com
SMTP_PORT=587
SMTP_USE_TLS=true
SMTP_USERNAME=resend
SMTP_PASSWORD=${resend}
SMTP_FROM_EMAIL=onboarding@resend.dev
# Others cannot receive the code until you have a domain, so uploads do not wait for it.
REQUIRE_VERIFIED_EMAIL_FOR_UPLOAD=false

# Google sign-in (optional, docs/SETUP_GOOGLE.md)
GOOGLE_CLIENT_IDS=
GOOGLE_WEB_CLIENT_ID=
EOF
  echo "Saved. Edit later with: nano $ENV_FILE"
else
  echo "Keeping the existing $ENV_FILE"
fi

# Storage keys for SeaweedFS, derived from .env so both always match.
set -a; . "$ENV_FILE"; set +a
umask 077
cat > "$DEPLOY_DIR/s3.json" <<EOF
{"identities":[{"name":"app","credentials":[{"accessKey":"${S3_ACCESS_KEY}","secretKey":"${S3_SECRET_KEY}"}],"actions":["Admin","Read","Write","List","Tagging"]}]}
EOF
chmod 644 "$DEPLOY_DIR/s3.json"  # read by the storage container's own user

say "4/6 Building and starting the app (first time: 10 to 20 minutes)"
cd "$DEPLOY_DIR"
docker compose up -d --build

say "5/6 Daily backup at 03:00 (kept 7 days in $BACKUP_DIR)"
mkdir -p "$BACKUP_DIR"
echo "0 3 * * * root bash $DEPLOY_DIR/backup.sh >> /var/log/flashcard-backup.log 2>&1" \
  > /etc/cron.d/flashcard-backup

say "6/6 Done"
echo "Open https://${SITE_ADDRESS} (the certificate can take a minute the first time)."
echo "Status: cd $DEPLOY_DIR && sudo docker compose ps"
echo "Make yourself admin after signing up: sudo bash $DEPLOY_DIR/admin.sh you@example.com"
