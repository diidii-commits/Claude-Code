# CGV 예매 오픈 감시기 — 극장판 치이카와: 인어 섬의 비밀 (2026-10-03)

**CGV 용산아이파크몰·성신여대입구·여의도·연남·대학로** 5곳만 감시합니다.
10/3(토) **오전 회차(12시 이전 시작)**가 아직 없는 극장을 1분마다 다시 확인하고, 새로 열리면
ntfy(`hyunji-cgv-chiikawa-7391`)로 극장명과 오전 회차 시간을 최고 우선순위로 푸시합니다.

## 왜 GitHub Actions가 아니라 폰(Termux)인가
GitHub Actions 러너(해외 데이터센터 IP)에서 cgv.co.kr에 접속하면 Cloudflare가
"비정상적으로 CGV에 접속한 것이 확인되어 이용이 제한되었어요"(403)로 차단합니다.
한국 모바일 IP(안드로이드 폰의 Termux)에서는 일반 HTTP 요청으로 접속됩니다(Playwright 불필요).

## 사용 API (로그인 불필요, `https://cgv.co.kr/api/v1/booking/*`)
사이트의 BFF 주소입니다. `api.cgv.co.kr/cnm/atkt/*`를 직접 부르면 401이 납니다.

| 용도 | 엔드포인트 | 주요 파라미터 |
|---|---|---|
| 영화 번호 | `searchAtktTopPostrList` | `coCd=A420` → 치이카와 `movNo=30001367` |
| 전체 극장 | `searchRegnList` | `coCd, lntd, lttd, regnGrpCd=, srchKwrd=` (175곳) |
| 극장별 상영일 | `searchSiteScnscYmdListByMov` | `coCd, siteNo, movNo` → `scnYmd` 목록 |
| 회차 시간 | `searchSchByMov` | `coCd, siteNo, scnYmd, movNo, rtctlScopCd=01` |

## 동작
- 시작: 전체 극장 목록에서 5곳을 이름으로 찾고(못 찾은 극장은 경고 알림), 10/3 오전 회차 현황을 알림으로 보냅니다. 오전 회차가 없는 곳은 `state.json`의 `pending`에 저장합니다.
- 1분마다 `pending` 극장만 재확인합니다. 극장당 요청 1~2회, 요청 사이 1초 간격입니다. 오전 회차가 생기면 알림을 보내고 목록에서 뺍니다. 오후 회차만 열린 극장은 계속 감시합니다.
- 10/3이 지나거나(KST 기준) 5곳 모두 오전 회차가 열리면 종료 알림을 보내고 끝납니다.
- 설정은 `FOCUS_KEYWORDS`, `MORNING_END`(기본 `1200`), `INTERVAL_SEC`(기본 60)에서 바꿀 수 있습니다. 대상이나 기준이 바뀌면 `state.json`을 자동으로 다시 만듭니다.

## Termux 실행
```
curl -sL -o cgv_monitor.py https://raw.githubusercontent.com/diidii-commits/Claude-Code/claude/cgv-ticket-monitor-tgnoas/cgv-monitor/cgv_monitor.py
python cgv_monitor.py test     # 알림 테스트
termux-wake-lock
python cgv_monitor.py loop     # 감시 시작 (Termux를 닫지 말고 홈 버튼으로 나가기)
```
