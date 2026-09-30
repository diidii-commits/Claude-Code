#!/usr/bin/env bash
# Download CGV Next.js bundles from the static CDN and grep API endpoints.
set -u
OUT=cgv-monitor/probe/out3; mkdir -p $OUT/js
BASE=https://cdn.cgv.co.kr/cgvpomscontent/static/script/e3bf2d63/_next/
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/130 Safari/537.36"
get(){ curl -sS -m 20 -A "$UA" -o "$OUT/js/$(echo $1 | tr '/()' '___')" -w "%{http_code} $1\n" "$BASE$1"; sleep 0.3; }
for f in static/chunks/webpack-fc17d5ea6464a758.js "static/chunks/app/(home)/cnm/movieBook/page-4360e60f1d7597e2.js" \
  "static/chunks/app/(home)/layout-88bb368989f43b1c.js" static/chunks/app/layout-0f6bcf42250f47a3.js \
  static/chunks/8346-e8014a133d0e467a.js static/chunks/main-app-dc7ae2e06adc0f2d.js; do get "$f"; done | tee $OUT/status.txt
# all chunk ids referenced by webpack runtime / page chunk
python3 - "$OUT" <<'PY' > $OUT/chunklist.txt
import re,sys,glob
s="".join(open(f,errors="ignore").read() for f in glob.glob(sys.argv[1]+"/js/*"))
w=open(glob.glob(sys.argv[1]+"/js/*webpack*")[0],errors="ignore").read()
# webpack runtime: "static/chunks/"+(({..names..})[e]||e)+"."+({..hashes..})[e]+".js"
m=re.search(r'"static/chunks/"\+\(\(\{(.*?)\}\)\[e\]\|\|e\)\+"\."\+\(\{(.*?)\}\)\[e\]', w, re.S)
if m:
    names=dict(re.findall(r'(\d+):"([^"]+)"',m.group(1)))
    for k,h in re.findall(r'(\d+):"([0-9a-f]+)"',m.group(2)):
        print(f"static/chunks/{names.get(k,k)}.{h}.js")
PY
wc -l $OUT/chunklist.txt
while read -r f; do get "$f" >> $OUT/status.txt; done < $OUT/chunklist.txt
grep -c '^200' $OUT/status.txt
grep -ohE '"/?(api/v1|cnm|com|met|atkt|ssn|mbr)/[A-Za-z0-9/_]{4,}"|https://[a-z]+\.cgv\.co\.kr[A-Za-z0-9/_]*' $OUT/js/* | sort | uniq -c | sort -rn > $OUT/endpoints.txt
# context around schedule-ish identifiers
grep -ohE '.{300}(searchSchd|Schd|ScnSchd|scnYmd|searchMovScn|siteNo)[^;]{0,300}' $OUT/js/* | head -300 > $OUT/context.txt
ls -la $OUT/js
