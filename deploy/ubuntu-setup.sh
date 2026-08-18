#!/usr/bin/env bash
# ProofLab — Ubuntu server deployment helper
# Run on the server as a user with sudo access:
#   chmod +x deploy/ubuntu-setup.sh
#   sudo ./deploy/ubuntu-setup.sh

set -euo pipefail

APP_DIR="${APP_DIR:-/var/www/prooflab}"
APP_USER="${APP_USER:-www-data}"
DOMAIN="${DOMAIN:-_}"
REPO_URL="${REPO_URL:-}"

echo "==> ProofLab deploy to ${APP_DIR}"

if [[ $EUID -ne 0 ]]; then
  echo "Run with sudo."
  exit 1
fi

apt-get update
apt-get install -y python3 python3-venv python3-pip nginx git

mkdir -p "$APP_DIR"

if [[ -n "$REPO_URL" ]]; then
  if [[ ! -d "$APP_DIR/.git" ]]; then
    git clone "$REPO_URL" "$APP_DIR"
  else
    git -C "$APP_DIR" pull
  fi
elif [[ ! -f "$APP_DIR/app.py" ]]; then
  echo "Copy project files to ${APP_DIR} first, or set REPO_URL=git@..."
  exit 1
fi

cd "$APP_DIR"

python3 -m venv venv
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements.txt

if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "Created .env — edit ${APP_DIR}/.env (GROQ_API_KEY) before using AI explainer."
fi

chown -R "$APP_USER:$APP_USER" "$APP_DIR"

cp deploy/prooflab.service /etc/systemd/system/prooflab.service
systemctl daemon-reload
systemctl enable prooflab
systemctl restart prooflab

sed "s/YOUR_DOMAIN/${DOMAIN}/" deploy/nginx-prooflab.conf > /etc/nginx/sites-available/prooflab
ln -sf /etc/nginx/sites-available/prooflab /etc/nginx/sites-enabled/prooflab
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl reload nginx

echo ""
echo "Done. Open http://${DOMAIN} (or your server IP)."
echo "Service: sudo systemctl status prooflab"
echo "Logs:    sudo journalctl -u prooflab -f"
