# -*- coding: utf-8 -*-
"""무턱/턱끝 전진 영상 → 카드뉴스 스튜디오 스키마(JSON) 생성·검증."""
import json, os, sys

ICON_KEYS = ["face","nose","eye","lip","jaw","lifting","syringe","shield","clock",
             "calendar","check","warning","question","doctor","chat","money","star",
             "heart","sparkle","list","bandage"]

data = {
  "title": "무턱, 턱끝 전진으로 입체감이 생길까? (필러·보형물 없이)",
  "slides": [
    {"type":"cover",
     "heading":"무턱, 뼈로 입체감이 생길까?",
     "body":"턱끝 전진으로 보는 무턱 이야기",
     "icon":"jaw","timestamp":-1},
    {"type":"content",
     "heading":"무턱은 인상까지 바꿔요",
     "body":"턱끝이 뒤로 물러나면 옆모습이 밋밋하고 인상이 옹졸해 보이기 쉬워요. 특히 남성분은 남성적인 느낌이 줄어 보이기도 합니다.",
     "icon":"face","timestamp":18},
    {"type":"content",
     "heading":"핵심은 턱끝 ‘전진’",
     "body":"턱끝은 앞으로 전진, 뒤로 후진 등 방법이 다양해요. 무턱은 앞쪽으로 살짝 전진시켜 개선하는 방향이 핵심입니다.",
     "icon":"jaw","timestamp":26},
    {"type":"content",
     "heading":"뼈를 전진시켜 고정해요",
     "body":"뼈에서 턱끝을 앞으로 전진시킨 뒤 고정하면, 부족했던 턱의 볼륨감과 입체감이 살아나게 됩니다.",
     "icon":"bandage","timestamp":58},
    {"type":"content",
     "heading":"에스테틱 라인에 맞춰요",
     "body":"턱끝이 이 라인에 못 미치는 경우가 많아요. 남성분은 보통 6~8mm 정도 전진을 고려할 수 있고, 비율에 따라 달라집니다.",
     "icon":"check","timestamp":75},
    {"type":"content",
     "heading":"필러 없이, 내 뼈로",
     "body":"여성분도 무턱이 심하면 이중턱처럼 보일 수 있어요. 턱끝 필러나 보형물 없이 뼈술로 입체감을 더하는 방법도 있습니다.",
     "icon":"sparkle","timestamp":103},
    {"type":"cta",
     "heading":"내 턱끝, 어떻게 달라질까요?",
     "body":"영상으로 확인하고 상담으로 방향을 잡아보세요.",
     "icon":"chat","timestamp":-1}
  ],
  "blog": {
    "title":"무턱 턱끝 전진, 필러 없이 입체감 살리는 방법｜강남 무이성형외과",
    "intro":"거울로 볼 땐 괜찮은데, 옆모습 사진만 보면 턱끝이 유독 아쉬우신가요? 무턱은 단순히 ‘턱이 짧은’ 문제가 아니라 옆선과 얼굴 아래쪽 인상 전체와 이어진 부분이라 접근 방법도 달라집니다. 오늘은 무이성형외과에서 턱끝 전진으로 무턱을 어떻게 바라보고 개선하는지, 영상 내용을 바탕으로 차근차근 풀어드릴게요.",
    "sections":[
      {"heading":"무턱, 왜 인상까지 달라 보일까요?",
       "body":"턱끝이 충분히 발달하지 못하면 옆모습이 밋밋해지고 인상이 다소 옹졸해 보이기 쉬워요. 특히 남성분들은 무턱일 때 남성적인 느낌이 줄어 보이는 경우가 많습니다. 그러다 보니 마스크를 자주 찾게 되고, 자신감이 떨어진다고 느끼시는 분들도 계세요. 그래서 무턱은 턱만의 문제가 아니라 얼굴 아래쪽 전체 인상과 연결해서 봐야 합니다.",
       "timestamp":18},
      {"heading":"무턱 개선의 핵심은 ‘턱끝 전진’이에요",
       "body":"턱끝은 앞으로 전진시키거나 뒤로 후진시키고, 길이감을 조절하는 등 방법이 다양합니다. 그중 무턱은 턱끝을 조금 앞쪽으로 전진시켜 개선하는 방향이 핵심이에요. 뼈에서 턱끝을 앞으로 전진시킨 뒤 단단히 고정하면, 부족했던 볼륨감과 입체감이 살아나게 됩니다. 없던 라인을 억지로 만드는 게 아니라, 뒤로 물러나 있던 내 뼈의 위치를 앞으로 옮겨 준다고 이해하시면 쉬워요.",
       "timestamp":58},
      {"heading":"얼마나 나와야 자연스러울까요? (에스테틱 라인)",
       "body":"턱끝이 어느 정도 나와야 조화로운지는 ‘에스테틱 라인’을 기준으로 봅니다. 무턱은 턱끝이 이 라인에 못 미치는 경우가 많아, 라인에 맞춰 전진 정도를 설계해요. 남성분의 경우 보통 짧게는 6mm, 길게는 8mm 정도까지 전진을 고려할 수 있습니다. 다만 이 수치는 얼굴 비율과 뼈 구조에 따라 달라지므로, 정해진 정답이 아니라 개인에 맞춰 조정되는 값이에요.",
       "timestamp":67},
      {"heading":"여성 무턱, 필러·보형물 없이 뼈로 볼 수 있어요",
       "body":"무턱은 남성분만의 고민이 아니에요. 여성분들도 무턱이 심하면 턱 아래가 접히듯 보여 이중턱처럼 느껴진다고 하시는 경우가 있습니다. 이때도 턱끝을 전진시켜 입체감을 만들면 밋밋하던 하관이 한결 정돈될 수 있어요. 턱끝 필러나 보형물을 넣는 대신, 내 뼈를 이동시키는 뼈술로 무턱을 보완하는 접근입니다.",
       "timestamp":96}
    ],
    "outro":"정리하면, 자연스러운 무턱 개선은 ‘무조건 채우는 것’보다 내 뼈를 에스테틱 라인에 맞춰 전진시키는 설계에서 시작됩니다. 다만 턱끝 전진은 뼈를 다루는 윤곽수술인 만큼, 전진할 수 있는 범위와 방법은 뼈 구조와 얼굴 비율에 따라 개인마다 달라질 수 있어요. 수술·시술의 효과는 개인에 따라 차이가 있고 부작용이 발생할 수 있으므로, 혼자 판단하기보다 전문의와 충분히 상담하신 뒤 나에게 맞는 방향을 정하시길 권해드립니다.",
    "tags":["무턱","무턱수술","턱끝전진","턱끝성형","남성무턱","이중턱","에스테틱라인","윤곽수술","강남성형외과","무이성형외과"]
  }
}

# ── 검증 ──────────────────────────────────────
errs = []
s = data["slides"]
if s[0]["type"] != "cover": errs.append("첫 슬라이드가 cover 아님")
if s[-1]["type"] != "cta": errs.append("마지막 슬라이드가 cta 아님")
content = [x for x in s if x["type"] == "content"]
if not (4 <= len(content) <= 6): errs.append(f"content 슬라이드 {len(content)}개 (4~6 벗어남)")
for i, x in enumerate(s):
    if x["icon"] not in ICON_KEYS: errs.append(f"slide{i} icon 잘못: {x['icon']}")
    if not isinstance(x["timestamp"], (int, float)): errs.append(f"slide{i} timestamp 숫자아님")
    if x["type"] == "content":
        if len(x["heading"]) > 20: errs.append(f"slide{i} heading {len(x['heading'])}자 > 20")
        if len(x["body"]) > 90: errs.append(f"slide{i} body {len(x['body'])}자 > 90")
b = data["blog"]
for k in ["title","intro","sections","outro","tags"]:
    if k not in b: errs.append(f"blog.{k} 누락")
if not (3 <= len(b["sections"]) <= 5): errs.append(f"blog sections {len(b['sections'])}개 (3~5 벗어남)")
if len(b["tags"]) != 10: errs.append(f"tags {len(b['tags'])}개 (10 권장)")

# 금지 표현 스캐너
BANNED = ["100%","최고","최초","유일","1등","부작용 없음","안전 보장","완벽","확실한 효과"]
blob = json.dumps(data, ensure_ascii=False)
hits = [w for w in BANNED if w in blob]
if hits: errs.append("금지표현 감지: " + ", ".join(hits))

print("=== 슬라이드 길이 체크 ===")
for i, x in enumerate(s):
    if x["type"] == "content":
        print(f"  slide{i}: heading {len(x['heading'])}자 / body {len(x['body'])}자")
print("=== 검증 결과 ===")
print("OK ✅ 문제 없음" if not errs else "\n".join("  ✗ " + e for e in errs))

out = os.path.abspath(os.path.join(os.path.dirname(__file__), "..",
        "무이성형외과_무턱_카드뉴스_블로그.json"))
with open(out, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print("saved:", out)
if errs: sys.exit(1)
