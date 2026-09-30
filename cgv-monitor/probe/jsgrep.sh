#!/usr/bin/env bash
# Download CGV Next.js bundles from the static CDN for offline endpoint analysis.
set -u
OUT=cgv-monitor/probe/out4; mkdir -p $OUT/js
BASE=https://cdn.cgv.co.kr/cgvpomscontent/static/script/e3bf2d63/_next/
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/130 Safari/537.36"
while read -r f; do
  curl -sS -m 20 -A "$UA" -o "$OUT/js/$(echo $f | tr '/()' '___')" -w "%{http_code} $f\n" "$BASE$f"; sleep 0.3
done < cgv-monitor/probe/chunks.txt | tee $OUT/status.txt
