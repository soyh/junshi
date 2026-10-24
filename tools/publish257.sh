#!/usr/bin/env bash
# Publish Build 257 to the mirror and GitHub (slow link here: /tmp then sudo mv).
set -uo pipefail
cd "C:/Users/12274/Documents/deepseek-harness/default-workspace/junshi-repo"
KEY="C:/Users/12274/.ssh/id_ed25519"
HOST="ubuntu@101.34.253.116"
NAME="JunshiPC-257-Windows-x64.zip"

scp -i "$KEY" -o BatchMode=yes "builds/pc-v257/$NAME" "$HOST:/tmp/junshi257.zip"
ssh -i "$KEY" -o BatchMode=yes "$HOST" "sudo bash -lc 'mv /tmp/junshi257.zip /var/www/junshi-downloads/$NAME && chmod 644 /var/www/junshi-downloads/$NAME && ls -l /var/www/junshi-downloads/$NAME'"
curl -skI --ssl-no-revoke "https://101.34.253.116/downloads/$NAME" | head -3

for i in 1 2 3 4 5 6; do
  echo "release attempt $i"
  E:/anaconda_envs/bridge312/python.exe tools/gh_release_257.py && break
  sleep 15
done
