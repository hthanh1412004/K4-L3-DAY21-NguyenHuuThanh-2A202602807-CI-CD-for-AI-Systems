#!/usr/bin/env bash
# Run on an Ubuntu VM as its deploy user, after copying the repo to ~/income-api.
set -euo pipefail
: "${ARTIFACT_BUCKET:?Set ARTIFACT_BUCKET to your real bucket}"
: "${CLOUD_PROVIDER:=gcp}"
sudo apt-get update
sudo apt-get install -y python3-venv curl
cd "$HOME/income-api"
python3 -m venv .venv
.venv/bin/python -m pip install --no-cache-dir -r requirements.txt
mkdir -p models
# Add GOOGLE_APPLICATION_CREDENTIALS or AWS credentials to this private file.
umask 077
if [ ! -f .env ]; then
  printf 'ARTIFACT_BUCKET=%s\nCLOUD_PROVIDER=%s\nAWS_DEFAULT_REGION=%s\n' \
    "$ARTIFACT_BUCKET" "$CLOUD_PROVIDER" "${AWS_DEFAULT_REGION:-ap-southeast-1}" > .env
fi
sudo tee /etc/systemd/system/income-api.service >/dev/null <<EOF
[Unit]
Description=Adult Income FastAPI
After=network-online.target
Wants=network-online.target

[Service]
User=$(id -un)
WorkingDirectory=$HOME/income-api
EnvironmentFile=$HOME/income-api/.env
ExecStart=$HOME/income-api/.venv/bin/python -m src.serve
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
sudo systemctl daemon-reload
sudo systemctl enable income-api
echo 'VM ready. Start service after the first model is uploaded by CI.'
