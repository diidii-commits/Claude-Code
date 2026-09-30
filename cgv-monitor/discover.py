"""CGV 접속 확인 + 시간표 API 파라미터 탐색 (폰에서 1회 실행).
출력 전체를 복사해서 Claude에게 붙여넣어 주세요."""
import json, time, urllib.parse, urllib.request, urllib.error

API = "https://api.cgv.co.kr"
H = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 14; SM-S921N) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36",
    "Accept": "application/json", "Accept-Language": "ko-KR",
    "Origin": "https://cgv.co.kr", "Referer": "https://cgv.co.kr/cnm/movieBook",
}
LAT, LNG = "37.5665", "126.9780"


def get(path, **params):
    time.sleep(1.5)
    url = API + path + "?" + urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=H), timeout=20) as r:
            body = r.read().decode("utf-8", "replace")
            code = r.status
    except urllib.error.HTTPError as e:
        code, body = e.code, e.read().decode("utf-8", "replace")
    except Exception as e:
        code, body = None, repr(e)
    try:
        return code, json.loads(body)
    except Exception:
        return code, body


def lists(o, out=None):
    out = [] if out is None else out
    if isinstance(o, list):
        if o and isinstance(o[0], dict):
            out.append(o)
        for x in o:
            lists(x, out)
    elif isinstance(o, dict):
        for v in o.values():
            lists(v, out)
    return out


def show(tag, code, j):
    if not isinstance(j, dict):
        print(f"[{tag}] HTTP {code} NON-JSON: {str(j)[:150]!r}")
        return
    ls = lists(j.get("data"))
    print(f"[{tag}] HTTP {code} sc={j.get('statusCode')} msg={j.get('statusMessage')} "
          f"lists={[len(l) for l in ls][:6]}")
    if ls:
        first = {k: v for k, v in ls[0][0].items() if v not in (None, "", [])}
        print("   keys:", ",".join(list(ls[0][0].keys())[:40]))
        print("   ex:", json.dumps(first, ensure_ascii=False)[:400])
    elif j.get("data") not in (None, [], {}):
        print("   data:", json.dumps(j.get("data"), ensure_ascii=False)[:300])


print("== 1. 접속 확인")
code, j = get("/cnm/atkt/searchAtktTopPostrList", coCd="A420", movNm="", div="", attrCd="")
show("postr", code, j)
if code != 200:
    raise SystemExit("CGV 접속 차단됨 (위 결과를 알려주세요)")

movs = [m for l in lists(j) for m in l if "치이카와" in str(m.get("movNm", ""))]
code, j2 = get("/cnm/atkt/searchOnlyCgvMovList", coCd="A420")
movs += [m for l in lists(j2) for m in l if "치이카와" in str(m.get("movNm", ""))]
print("== 2. 치이카와 영화:", json.dumps([{k: m.get(k) for k in ("movNo", "movNm")} for m in movs],
                                   ensure_ascii=False))
mov = movs[0]["movNo"] if movs else ""

print("== 3. 극장 목록 후보")
code, j = get("/cnm/atkt/searchRegnList", coCd="A420", lntd=LNG, lttd=LAT, regnGrpCd="", srchKwrd="")
show("regn", code, j)
code, j = get("/cnm/atkt/searchRegnList", coCd="A420", lntd=LNG, lttd=LAT, regnGrpCd="01", srchKwrd="")
show("regn01", code, j)
code, j = get("/cnm/atkt/searchRcmSiteList", coCd="A420", custNo="", lntd=LNG, lttd=LAT,
              srchKwrd="", div=" ", attrCd=" ", movNo="")
show("rcm", code, j)
code, j = get("/cnm/atkt/searchRcmSiteList", coCd="A420", custNo="", lntd=LNG, lttd=LAT,
              srchKwrd="", div=" ", attrCd=" ", movNo=mov)
show("rcm+mov", code, j)
site = "0013"  # CGV 용산아이파크몰
for l in lists(j):
    if l and l[0].get("siteNo"):
        site = l[0]["siteNo"]
        break
print("   test site:", site)

print("== 4. 시간표 후보 (영화", mov, ")")
for ymd in ("20260930", "20261003"):
    show(f"schByMov {ymd}", *get("/cnm/atkt/searchSchByMov", coCd="A420", siteNo=site, scnYmd=ymd, movNo=mov))
    show(f"schByMov nosite {ymd}", *get("/cnm/atkt/searchSchByMov", coCd="A420", scnYmd=ymd, movNo=mov))
show("ymdByMov", *get("/cnm/atkt/searchSiteScnscYmdListByMov", coCd="A420", siteNo=site, movNo=mov))
show("ymdBySite", *get("/cnm/atkt/searchSiteScnscYmdListBySite", coCd="A420", siteNo=site))
show("movScnInfo", *get("/cnm/atkt/searchMovScnInfo", coCd="A420", siteNo=site, scnYmd="20260930"))
show("lastScnDay", *get("/cnm/atkt/searchLastScnDay", coCd="A420", siteNo=site, movNo=mov))
print("== 끝")
