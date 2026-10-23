#!/usr/bin/env bash
set -euo pipefail
cd "C:/Users/12274/Documents/deepseek-harness/default-workspace/junshi-repo"
ZIP="builds/pc-v251/JunshiPC-251-Windows-x64.zip"
KEY="C:/Users/12274/.ssh/junshi_ed25519"
scp -o BatchMode=yes -i "$KEY" "$ZIP" ubuntu@101.34.253.116:/tmp/JunshiPC-251-Windows-x64.zip
ssh -o BatchMode=yes -i "$KEY" ubuntu@101.34.253.116 'sudo mv /tmp/JunshiPC-251-Windows-x64.zip /var/www/junshi-downloads/ && sudo chmod 644 /var/www/junshi-downloads/JunshiPC-251-Windows-x64.zip'
echo "mirror uploaded"
curl -s -o /dev/null -w 'mirror=%{http_code} size=%{size_download}\n' -I https://101.34.253.116/downloads/JunshiPC-251-Windows-x64.zip || true
