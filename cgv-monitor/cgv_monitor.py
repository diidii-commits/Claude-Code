"""CGV 예매 오픈 감시기 — '극장판 치이카와: 인어 섬의 비밀' 2026-10-03 회차.

사용법 (Termux):
  python cgv_monitor.py loop    # 첫 실행 시 감시 극장 스캔 → 1분마다 오전 회차 미오픈 극장만 재확인 (10/3 지나면 종료)
  python cgv_monitor.py init    # 전체 극장 스캔해서 state.json 새로 만들기
  python cgv_monitor.py check   # 1회만 재확인
  python cgv_monitor.py test    # 알림 테스트 (9/30 → 회차 없으면 가장 가까운 상영일로 실제 시간표 알림)

API: 사이트 BFF https://cgv.co.kr/api/v1/booking/* (api.cgv.co.kr/cnm/atkt/* 를 중계, 로그인 불필요)
  searchAtktTopPostrList       영화 목록 → movNo
  searchRegnList               전체 극장 (siteNo, siteNm)
  searchSiteScnscYmdListByMov  극장+영화 → 상영일 목록 (극장당 1회 호출로 오픈 여부 판단)
  searchSchByMov               극장+영화+날짜 → 회차 (rtctlScopCd=01 필수)
"""
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

MOVIE_KEYWORD = "치이카와"
TARGET_YMD = "20261003"
NTFY_TOPIC = "hyunji-cgv-chiikawa-7391"
INTERVAL_SEC = 60
# 감시 대상: 이 5곳만 (극장명 부분 일치), 1분마다 확인, 오픈 시 최고 우선순위 알림
FOCUS_KEYWORDS = ["용산아이파크", "성신여대", "여의도", "연남", "대학로"]
ONLY_FOCUS = True
FOCUS_INTERVAL_SEC = 60
# 오전(12시 이전 시작) 회차만 '오픈'으로 판단
SEOUL_ONLY = False  # ONLY_FOCUS가 켜져 있으면 무시
MORNING_END = "1200"  # HHMM, 이 시각 이전에 시작하는 회차만
FILTER_KEY = (f"focus={','.join(FOCUS_KEYWORDS)}" if ONLY_FOCUS else f"seoul={SEOUL_ONLY}") + f"|morning<{MORNING_END}"
DELAY_SEC = 1.0  # CGV 서버 부담을 줄이기 위한 요청 간 간격

API = "https://cgv.co.kr/api/v1/booking"
CO_CD = "A420"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/130.0.0.0 Mobile Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "ko-KR",
    "Referer": "https://cgv.co.kr/cnm/movieBook",
}
KST = timezone(timedelta(hours=9))
STATE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "state.json")


class ApiError(Exception):
    pass


def now():
    return datetime.now(KST)


def log(*a):
    print(now().strftime("%m-%d %H:%M:%S"), *a, flush=True)


def get(path, **params):
    time.sleep(DELAY_SEC)
    url = f"{API}{path}?{urllib.parse.urlencode(params)}"
    last = None
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=20) as r:
                j = json.loads(r.read())
            if j.get("statusCode") not in (0, None):
                raise ApiError(f"{path}: {j.get('statusCode')} {j.get('statusMessage')}")
            return j
        except urllib.error.HTTPError as e:
            last = ApiError(f"{path}: HTTP {e.code}")
            if e.code in (401, 403):  # 차단/인증 문제는 재시도해도 소용없음
                raise last
        except (urllib.error.URLError, TimeoutError, ValueError) as e:
            last = ApiError(f"{path}: {e!r}")
        time.sleep(3 * (attempt + 1))
    raise last


def dicts(o):
    if isinstance(o, dict):
        yield o
        for v in o.values():
            yield from dicts(v)
    elif isinstance(o, list):
        for v in o:
            yield from dicts(v)


def find_movie():
    j = get("/searchAtktTopPostrList", coCd=CO_CD, movNm="", div="", attrCd="")
    for d in dicts(j.get("data")):
        if MOVIE_KEYWORD in str(d.get("movNm", "")) and d.get("movNo"):
            return d["movNo"], d["movNm"]
    raise ApiError(f"영화 '{MOVIE_KEYWORD}'를 찾지 못함")


def walk_sites(o, grp=("", "")):
    """(siteNo, siteNm, regnGrpCd, regnGrpNm) — 상위 객체의 지역 정보를 물려받음."""
    if isinstance(o, dict):
        grp = (o.get("regnGrpCd") or grp[0], o.get("regnGrpNm") or grp[1])
        if o.get("siteNo") and o.get("siteNm"):
            yield o["siteNo"], o["siteNm"], grp[0], grp[1]
        for v in o.values():
            if isinstance(v, (dict, list)):
                yield from walk_sites(v, grp)
    elif isinstance(o, list):
        for v in o:
            yield from walk_sites(v, grp)


def all_sites(seoul_only=SEOUL_ONLY):
    j = get("/searchRegnList", coCd=CO_CD, lntd="126.978", lttd="37.5665", regnGrpCd="", srchKwrd="")
    rows = list(walk_sites(j.get("data")))
    sites = {no: nm for no, nm, _, _ in rows}
    if len(sites) < 50:
        raise ApiError(f"극장 목록이 비정상적으로 적음 ({len(sites)})")
    if ONLY_FOCUS:
        focus = {no: nm for no, nm in sites.items() if is_focus(nm)}
        missing = [k for k in FOCUS_KEYWORDS if not any(k in nm for nm in focus.values())]
        if missing:
            log("극장 목록에서 못 찾은 극장:", ", ".join(missing))
            notify("치이카와 감시 경고", f"극장 목록에서 못 찾음: {', '.join(missing)}", tags="warning", priority=4)
        if not focus:
            raise ApiError("감시할 극장을 하나도 찾지 못함")
        return focus
    if not seoul_only:
        return sites
    seoul = {no: nm for no, nm, cd, gnm in rows if "서울" in gnm}
    if not seoul:  # 지역명이 없으면 서울 코드(01)로 직접 조회
        j = get("/searchRegnList", coCd=CO_CD, lntd="126.978", lttd="37.5665", regnGrpCd="01", srchKwrd="")
        seoul = {no: nm for no, nm, cd, _ in walk_sites(j.get("data")) if cd in ("01", "")}
    if not 10 <= len(seoul) < len(sites):
        raise ApiError(f"서울 극장 목록을 구분하지 못함 ({len(seoul)}/{len(sites)})")
    return seoul


def schedule_dates(site_no, mov_no):
    j = get("/searchSiteScnscYmdListByMov", coCd=CO_CD, siteNo=site_no, movNo=mov_no)
    return {d["scnYmd"] for d in dicts(j.get("data")) if d.get("scnYmd")}


def showtimes(site_no, mov_no, ymd):
    j = get("/searchSchByMov", coCd=CO_CD, siteNo=site_no, scnYmd=ymd, movNo=mov_no, rtctlScopCd="01")
    rows = [d for d in dicts(j.get("data")) if d.get("scnsrtTm")]
    rows.sort(key=lambda r: r["scnsrtTm"])
    out = []
    for r in rows:
        t = r["scnsrtTm"]
        kind = r.get("movkndDsplNm") or ""
        seats = f" 잔여{r['frSeatCnt']}" if r.get("frSeatCnt") not in (None, "") else ""
        out.append((t, f"{t[:2]}:{t[2:4]} {r.get('scnsNm', '')} {kind}{seats}".replace("  ", " ").strip()))
    return out


def morning_times(site_no, mov_no, ymd):
    """오전 회차 목록(문자열). 해당 날짜 시간표가 아예 없으면 None, 오후만 있으면 []."""
    if ymd not in schedule_dates(site_no, mov_no):
        return None
    return [txt for hhmm, txt in showtimes(site_no, mov_no, ymd) if hhmm < MORNING_END]


def notify(title, message, tags="movie_camera", priority=4):
    body = json.dumps({"topic": NTFY_TOPIC, "title": title, "message": message,
                       "tags": [tags], "priority": priority,
                       "click": "https://cgv.co.kr/cnm/movieBook"}).encode()
    req = urllib.request.Request("https://ntfy.sh/", data=body,
                                 headers={"Content-Type": "application/json"})
    for attempt in range(3):
        try:
            urllib.request.urlopen(req, timeout=20).read()
            return True
        except Exception as e:
            log("ntfy 전송 실패", e)
            time.sleep(3)
    return False


def fmt_ymd(ymd):
    d = datetime.strptime(ymd, "%Y%m%d")
    return f"{d.month}/{d.day}({'월화수목금토일'[d.weekday()]})"


def is_focus(site_nm):
    return any(k in site_nm for k in FOCUS_KEYWORDS)


def notify_open(site_nm, ymd, times, test=False):
    focus = is_focus(site_nm)
    title = (f"{'[테스트] ' if test else ''}{'★중점★ ' if focus and not ONLY_FOCUS else ''}"
             f"{site_nm} {fmt_ymd(ymd)} 치이카와 오전 회차 오픈!")
    msg = "\n".join(times)
    return notify(title, msg, tags="rotating_light" if focus else "movie_camera", priority=5 if focus else 4)


def focus_report(st):
    """감시 극장 5곳의 현재 상태를 한 번에 알림."""
    every = {**st["opened_at_init"], **{k: v["name"] for k, v in st["opened_later"].items()}, **st["pending"]}
    lines = []
    for kw in FOCUS_KEYWORDS:
        hits = [(no, nm) for no, nm in every.items() if kw in nm]
        if not hits:
            lines.append(f"{kw}: 극장 목록에서 못 찾음")
            log(f"중점 극장 '{kw}'을 극장 목록에서 찾지 못함")
        for no, nm in hits:
            try:
                times = morning_times(no, st["movNo"], st["target"])
            except ApiError:
                lines.append(f"{nm}: 조회 실패")
                continue
            if times:
                lines.append(f"{nm}: 오전 이미 오픈 {' / '.join(t.split(' ')[0] for t in times)}")
            elif times == []:
                lines.append(f"{nm}: 오후 회차만 있음 → 1분마다 감시")
            else:
                lines.append(f"{nm}: 미오픈 → 1분마다 감시")
    log("감시 극장:\n  " + "\n  ".join(lines))
    notify(f"감시 극장 {fmt_ymd(st['target'])} 오전 회차 현황", "\n".join(lines), tags="star", priority=4)


def load_state():
    try:
        with open(STATE_PATH, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return None


def save_state(st):
    tmp = STATE_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(st, f, ensure_ascii=False, indent=1)
    os.replace(tmp, STATE_PATH)


def init_scan(ymd=TARGET_YMD):
    mov_no, mov_nm = find_movie()
    sites = all_sites()
    log(f"영화 {mov_nm} ({mov_no}), 극장 {len(sites)}곳 스캔 시작 — 약 {len(sites) * (DELAY_SEC + 0.3) / 60:.0f}분")
    pending, opened, errors = {}, {}, 0
    for i, (no, nm) in enumerate(sites.items(), 1):
        try:
            has = bool(morning_times(no, mov_no, ymd))
        except ApiError as e:
            log("  오류", nm, e)
            errors += 1
            has = False  # 확인 실패한 극장은 미오픈으로 두고 계속 감시
        (opened if has else pending)[no] = nm
        if i % 25 == 0:
            log(f"  {i}/{len(sites)} (오픈 {len(opened)}, 미오픈 {len(pending)})")
    st = {"movNo": mov_no, "movNm": mov_nm, "target": ymd, "filter": FILTER_KEY, "created": now().isoformat(),
          "pending": pending, "opened_at_init": opened, "opened_later": {}}
    save_state(st)
    log(f"스캔 완료 (오전 {MORNING_END[:2]}시 이전 회차 기준): 이미 오픈 {len(opened)}곳, 미오픈 {len(pending)}곳 (오류 {errors}) → state.json 저장")
    notify(f"치이카와 {fmt_ymd(ymd)} 오전 회차 감시 시작",
           f"{len(sites)}곳 중 오전 회차 이미 오픈 {len(opened)}곳 / 미오픈 {len(pending)}곳 감시 중 (1분 간격)", tags="eyes", priority=3)
    return st


def check_round(st, focus_only=False):
    mov_no, ymd = st["movNo"], st["target"]
    pending = st["pending"]
    newly, errors = [], 0
    targets = sorted(pending.items(), key=lambda kv: not is_focus(kv[1]))  # 중점 극장 먼저
    if focus_only:
        targets = [kv for kv in targets if is_focus(kv[1])]
    for no, nm in targets:
        try:
            times = morning_times(no, mov_no, ymd)
            if not times:
                continue
        except ApiError as e:
            errors += 1
            log("  오류", nm, e)
            if "HTTP 403" in str(e) or "HTTP 401" in str(e):
                raise
            continue
        log(f"  ★ 오픈: {nm} {times}")
        if notify_open(nm, ymd, times):
            st["opened_later"][no] = {"name": nm, "times": times, "at": now().isoformat()}
            del pending[no]
            save_state(st)
            newly.append(nm)
    if not focus_only or newly or errors:
        log(f"{'중점 ' if focus_only else ''}확인 완료: 새로 오픈 {len(newly)}곳, "
            f"남은 미오픈 {len(pending)}곳, 오류 {errors}")
    return newly


def expired(ymd=TARGET_YMD):
    return now().strftime("%Y%m%d") > ymd


def loop():
    st = load_state()
    if st is None or st.get("target") != TARGET_YMD or st.get("filter") != FILTER_KEY:
        st = init_scan()
    focus_report(st)
    blocked = 0
    last_full = 0.0
    while True:
        if expired(st["target"]):
            log("대상 날짜가 지나서 종료합니다.")
            notify("치이카와 감시 종료", f"{fmt_ymd(st['target'])} 지남 — 감시를 종료했습니다.", tags="stop_sign", priority=2)
            return
        if not st["pending"]:
            log("모든 극장이 오픈되어 종료합니다.")
            notify("치이카와 감시 종료", "감시하던 극장의 오전 회차가 모두 오픈됐습니다.", tags="tada", priority=3)
            return
        started = time.time()
        full = started - last_full >= INTERVAL_SEC - 5
        try:
            check_round(st, focus_only=not full)
            if full:
                last_full = started
            blocked = 0
        except ApiError as e:
            blocked += 1
            log("CGV 접속 차단/오류:", e)
            if blocked == 3:
                notify("치이카와 감시 오류", f"CGV 접속이 연속 실패 중입니다: {e}", tags="warning", priority=4)
        time.sleep(max(10, FOCUS_INTERVAL_SEC - (time.time() - started)))


def test(ymd="20260930"):
    """알림 경로 테스트: 감시 극장마다 ymd 이후 가장 빠른 오전 회차가 있는 날짜를 찾아 [테스트] 알림.
    오전 회차가 하나도 없어도 극장별 상영일 요약을 알림으로 보내므로 항상 1건 이상 도착한다."""
    mov_no, _ = find_movie()
    sites = all_sites()
    log(f"감시 극장 {len(sites)}곳: {', '.join(sites.values())}")
    sent, summary = 0, []
    for no, nm in sites.items():
        dates = sorted(d for d in schedule_dates(no, mov_no) if d >= ymd)
        found = None
        for d in dates[:4]:
            times = morning_times(no, mov_no, d)
            if times:
                found = (d, times)
                break
        log(f"  {nm}: 상영일 {[fmt_ymd(d) for d in dates]} / 오전회차 {found}")
        summary.append(f"{nm}: " + (f"{fmt_ymd(found[0])} 오전 {len(found[1])}회" if found
                                     else f"상영일 {len(dates)}일, 오전회차 없음"))
        if found and sent < 2:
            notify_open(nm, found[0], found[1], test=True)
            sent += 1
    notify("[테스트] 치이카와 감시 알림 확인", "\n".join(summary), tags="white_check_mark", priority=4)
    log(f"테스트 완료: 오픈 알림 {sent}건 + 요약 알림 1건 전송 (ntfy 앱에서 확인)")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "loop"
    if cmd == "init":
        init_scan()
    elif cmd == "check":
        s = load_state()
        if not s or s.get("filter") != FILTER_KEY:
            s = init_scan()
        check_round(s)
    elif cmd == "test":
        test(sys.argv[2] if len(sys.argv) > 2 else "20260930")
    else:
        loop()
