#!/usr/bin/env bash
set -uo pipefail
cd "C:/Users/12274/Documents/deepseek-harness/default-workspace/junshi-repo"
TOKEN=$(cat /c/Users/12274/AppData/Local/Temp/tok251.txt)
URL="https://uploads.github.com/repos/soyh/junshi/releases/421870235/assets?name=JunshiPC-251-Windows-x64.zip"
for attempt in 1 2 3 4 5 6; do
  echo "attempt $attempt"
  if curl -sS --ssl-no-revoke --http1.1 --max-time 3000 \
      -X POST \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/zip" \
      --data-binary @builds/pc-v251/JunshiPC-251-Windows-x64.zip \
      "$URL" -o /tmp/asset251.json; then
    if grep -q '"id"' /tmp/asset251.json; then
      echo "uploaded"
      head -c 300 /tmp/asset251.json
      exit 0
    fi
    echo "bad response:"; head -c 300 /tmp/asset251.json
  fi
  sleep 8
done
exit 1
