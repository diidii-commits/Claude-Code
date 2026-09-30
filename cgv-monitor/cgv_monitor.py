"""CGV 예매 오픈 감시기 — '극장판 치이카와: 인어 섬의 비밀' 2026-10-03 회차.

사용법 (Termux):
  python cgv_monitor.py loop    # 첫 실행 시 전체 스캔 → 5분마다 미오픈 극장만 재확인 (10/3 지나면 종료)
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
INTERVAL_SEC = 5 * 60
# 중점 감시 극장: 1분마다 확인, 오픈 시 최고 우선순위 알림
FOCUS_KEYWORDS = ["용산아이파크", "성신여대", "여의도", "연남", "대학로"]
FOCUS_INTERVAL_SEC = 60
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


def all_sites():
    j = get("/searchRegnList", coCd=CO_CD, lntd="126.978", lttd="37.5665", regnGrpCd="", srchKwrd="")
    sites = {}
    for d in dicts(j.get("data")):
        if d.get("siteNo") and d.get("siteNm"):
            sites[d["siteNo"]] = d["siteNm"]
    if len(sites) < 50:
        raise ApiError(f"극장 목록이 비정상적으로 적음 ({len(sites)})")
    return sites


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
        out.append(f"{t[:2]}:{t[2:4]} {r.get('scnsNm', '')} {kind}{seats}".replace("  ", " ").strip())
    return out


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
    title = (f"{'[테스트] ' if test else ''}{'★중점★ ' if focus else ''}"
             f"{site_nm} {fmt_ymd(ymd)} 치이카와 예매 오픈!")
    msg = "\n".join(times) if times else "(회차 시간 조회 실패 — 앱에서 확인)"
    return notify(title, msg, tags="rotating_light" if focus else "movie_camera", priority=5 if focus else 4)


def focus_report(st):
    """중점 극장 5곳의 현재 상태를 한 번에 알림."""
    every = {**st["opened_at_init"], **{k: v["name"] for k, v in st["opened_later"].items()}, **st["pending"]}
    lines = []
    for kw in FOCUS_KEYWORDS:
        hits = [(no, nm) for no, nm in every.items() if kw in nm]
        if not hits:
            lines.append(f"{kw}: 극장 목록에서 못 찾음")
            log(f"중점 극장 '{kw}'을 극장 목록에서 찾지 못함")
        for no, nm in hits:
            if no in st["pending"]:
                lines.append(f"{nm}: 미오픈 → 1분마다 감시")
            else:
                try:
                    times = showtimes(no, st["movNo"], st["target"])
                except ApiError:
                    times = []
                lines.append(f"{nm}: 이미 오픈 {' / '.join(t.split(' ')[0] for t in times)}")
    log("중점 극장:\n  " + "\n  ".join(lines))
    notify(f"중점 극장 {fmt_ymd(st['target'])} 현황", "\n".join(lines), tags="star", priority=4)


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
            has = ymd in schedule_dates(no, mov_no)
        except ApiError as e:
            log("  오류", nm, e)
            errors += 1
            has = False  # 확인 실패한 극장은 미오픈으로 두고 계속 감시
        (opened if has else pending)[no] = nm
        if i % 25 == 0:
            log(f"  {i}/{len(sites)} (오픈 {len(opened)}, 미오픈 {len(pending)})")
    st = {"movNo": mov_no, "movNm": mov_nm, "target": ymd, "created": now().isoformat(),
          "pending": pending, "opened_at_init": opened, "opened_later": {}}
    save_state(st)
    log(f"스캔 완료: 이미 오픈 {len(opened)}곳, 미오픈 {len(pending)}곳 (오류 {errors}) → state.json 저장")
    notify(f"치이카와 {fmt_ymd(ymd)} 감시 시작",
           f"이미 오픈 {len(opened)}곳 / 미오픈 {len(pending)}곳 감시 중 (중점 5곳 1분 / 나머지 5분 간격)", tags="eyes", priority=3)
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
            if ymd not in schedule_dates(no, mov_no):
                continue
            try:
                times = showtimes(no, mov_no, ymd)
            except ApiError as e:
                log("  회차 조회 실패", nm, e)
                times = []
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
    if st is None or st.get("target") != TARGET_YMD:
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
            notify("치이카와 감시 종료", "감시하던 극장이 모두 오픈됐습니다.", tags="tada", priority=3)
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
    """알림 경로 테스트: 해당 날짜에 치이카와 회차가 있는 극장 2곳의 실제 시간표로 [테스트] 알림 전송."""
    mov_no, mov_nm = find_movie()
    sites = all_sites()
    order = ["0056", "0013", "0074"] + [s for s in sites if s not in ("0056", "0013", "0074")]
    probe_dates = sorted(schedule_dates(order[0], mov_no))
    use = ymd
    if ymd not in probe_dates:
        later = [d for d in probe_dates if d >= ymd]
        use = later[0] if later else ymd
        log(f"{fmt_ymd(ymd)}에는 치이카와 회차가 없음 (개봉 전) → {fmt_ymd(use)} 회차로 테스트")
    sent = 0
    for no in order[:40]:
        if no not in sites:
            continue
        if use not in schedule_dates(no, mov_no):
            continue
        times = showtimes(no, mov_no, use)
        log(f"테스트 알림: {sites[no]} {times}")
        notify_open(sites[no], use, times, test=True)
        sent += 1
        if sent == 2:
            break
    log(f"테스트 완료: 알림 {sent}건 전송 (ntfy 앱에서 확인)")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "loop"
    if cmd == "init":
        init_scan()
    elif cmd == "check":
        s = load_state() or init_scan()
        check_round(s)
    elif cmd == "test":
        test(sys.argv[2] if len(sys.argv) > 2 else "20260930")
    else:
        loop()
