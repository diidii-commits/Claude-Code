#!/usr/bin/env bash
# 쇼츠 배경 렌더링 스크립트
# 사용법: ./render.sh
#   - output/background.png     : 최종 배경 (1080×1920)
#   - output/background@2x.png  : 고해상도 배경 (2160×3840)
#   - output/preview.png        : 영상 영역 가이드가 표시된 미리보기
set -euo pipefail
cd "$(dirname "$0")"

CHROME="${CHROME:-/opt/pw-browsers/chromium}"
command -v "$CHROME" >/dev/null || CHROME="$(command -v chromium || command -v google-chrome)"

FLAGS=(--headless=new --no-sandbox --disable-gpu --hide-scrollbars --window-size=1080,1920)
mkdir -p output

"$CHROME" "${FLAGS[@]}" --force-device-scale-factor=1 \
  --screenshot="output/background.png" "file://$PWD/template.html"

"$CHROME" "${FLAGS[@]}" --force-device-scale-factor=2 \
  --screenshot="output/background@2x.png" "file://$PWD/template.html"

"$CHROME" "${FLAGS[@]}" --force-device-scale-factor=1 \
  --screenshot="output/preview.png" "file://$PWD/template.html?mode=preview"

echo "완료: output/background.png, output/background@2x.png, output/preview.png"
