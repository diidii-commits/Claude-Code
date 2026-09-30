"""2차 탐색: 극장목록 형태 + 시간표 rtctlScopCd 값 찾기 (출력은 한 화면용으로 짧게)."""
import json, time, urllib.parse, urllib.request, urllib.error

API = "https://cgv.co.kr/api/v1/booking"
H = {"User-Agent": "Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/130.0.0.0 Mobile Safari/537.36",
     "Accept": "application/json", "Accept-Language": "ko-KR",
     "Referer": "https://cgv.co.kr/cnm/movieBook"}


def get(path, **p):
    time.sleep(1.2)
    try:
        with urllib.request.urlopen(urllib.request.Request(
                API + path + "?" + urllib.parse.urlencode(p), headers=H), timeout=20) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read())
        except Exception:
            return {"statusCode": e.code}


def dicts(o):
    if isinstance(o, dict):
        yield o
        for v in o.values():
            yield from dicts(v)
    elif isinstance(o, list):
        for v in o:
            yield from dicts(v)


j = get("/searchAtktTopPostrList", coCd="A420", movNm="", div="", attrCd="")
movs = sorted({d["movNo"] for d in dicts(j) if "치이카와" in str(d.get("movNm"))})
print("MOV", movs)
mov = movs[0]
j = get("/searchRegnList", coCd="A420", lntd="126.978", lttd="37.5665", regnGrpCd="", srchKwrd="")
sites = {d["siteNo"]: d.get("siteNm") for d in dicts(j) if d.get("siteNo")}
grps = {d.get("regnGrpCd") for d in dicts(j) if d.get("regnGrpCd")}
print("REGN sc", j.get("statusCode"), "sites", len(sites), "grps", sorted(grps)[:12])
if not sites:
    j = get("/searchRegnList", coCd="A420", lntd="126.978", lttd="37.5665", regnGrpCd="01", srchKwrd="")
    sites = {d["siteNo"]: d.get("siteNm") for d in dicts(j) if d.get("siteNo")}
    print("REGN01 sc", j.get("statusCode"), "sites", len(sites))
site = next(iter(sites), "0013")
print("SITE", site, sites.get(site))
ymds = [d["scnYmd"] for d in dicts(get("/searchSiteScnscYmdListByMov", coCd="A420", siteNo=site, movNo=mov))
        if d.get("scnYmd")]
print("YMD", ymds[:6])
ymd = ymds[0] if ymds else "20260930"
for v in ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "00", "11", "12", "99"]:
    j = get("/searchSchByMov", coCd="A420", siteNo=site, scnYmd=ymd, movNo=mov, rtctlScopCd=v)
    rows = [d for d in dicts(j.get("data")) if d.get("scnsrtTm") or d.get("scnSseq")]
    print("R", v, j.get("statusCode"), len(rows), str(j.get("statusMessage"))[:22])
    if rows:
        r = rows[0]
        print("KEYS", ",".join(k for k in r if r[k] not in (None, ""))[:400])
        print("EX", {k: r[k] for k in ("siteNm", "scnYmd", "scnsrtTm", "scnsNm", "movNm", "movkndDsplNm",
                                      "frSeatCnt", "stcnt") if k in r})
        break
print("END")
