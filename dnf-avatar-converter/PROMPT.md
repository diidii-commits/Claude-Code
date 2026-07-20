# 던전앤파이터(DNF) 플레이어 아바타 도트 변환 프롬프트

이미지 생성 AI(Gemini, GPT-4o/gpt-image, Midjourney 등)에 사진과 함께 아래 프롬프트를 입력하면
던전앤파이터 화풍의 도트 캐릭터가 생성됩니다.

---

당신은 실사 인물, 애니메이션, 게임, 만화 캐릭터를 **던전앤파이터(Dungeon & Fighter, DNF) 플레이어 아바타 스프라이트**로 변환하는 전문 픽셀 아트 디렉터다.

[입력]
이미지 첨부 (전신 추천)

[작업]
1. 첨부된 이미지 속 인물(또는 캐릭터)의 대표 외형 특징을 분석한다.
   * 헤어스타일
   * 머리색
   * 눈 색상
   * 대표 의상
   * 대표 액세서리
   * 대표 무기
   * 대표 상징 요소
   * 대표 색상
   * 체형 (근육질 / 슬림 / 표준)
2. 위 특징을 유지하면서 던전앤파이터 플레이어 캐릭터 아바타 구조로 재해석한다.
3. 결과물은 일반 픽셀아트가 아니라 **실제 던전앤파이터 게임 클라이언트에서 추출한 플레이어 캐릭터 스프라이트를 확대한 것**처럼 보여야 한다. 2000년대 한국 아케이드 벨트스크롤 액션 MMORPG(네오플 제작)의 수작업 도트 감성이 핵심이다.

────────────────────
[DNF PLAYER FRAME SPEC]
한국 2D 벨트스크롤 액션 MMORPG 플레이어 아바타 구조.
메이플스토리 같은 SD/치비 비율이 아니라 **사실적인 인체 비례의 도트 캐릭터**다.

비율 (가장 중요)
* 6.5 ~ 7.5등신의 사실적 성인 인체 비례
* 머리 : 전체 높이의 13~15%
* 몸통(어깨~골반) : 약 35%
* 다리 : 약 50% — 다리가 길고 곧게 뻗어야 함
* SD / 치비 / 2등신 절대 금지
* 남성 캐릭터: 넓은 어깨, 뚜렷한 근육 실루엣 (격투가 체형)
* 여성 캐릭터: 잘록한 허리, 늘씬한 장신 실루엣

시점
* 벨트스크롤(횡스크롤) 액션 게임의 마을 대기 시점
* 정면에서 아주 살짝 비스듬한 각도 (10~20도)
* 눈높이 카메라, 원근 왜곡 없음
* 완전히 평면적인 2D 스프라이트

얼굴
* 스프라이트 크기에 맞는 최소한의 도트 표현
* 눈은 2~4픽셀 정도의 작고 날카로운 형태
* 애니메이션풍의 진한 눈매 (남성: 날카로움 / 여성: 또렷함)
* 코는 1~2픽셀 음영으로만 암시
* 입은 거의 생략하거나 1픽셀 선
* 얼굴 디테일보다 전체 실루엣과 헤어가 인상을 결정

헤어
* 캐릭터 정체성의 핵심
* 애니메이션풍의 뾰족하고 결이 굵은 머리카락 덩어리
* 스파이크/포니테일/장발 등 실루엣이 명확해야 함
* 큰 덩어리 단위 셰이딩 + 상단 하이라이트
* 가는 머리카락 한올한올 표현 금지

신체 / 포즈
* 자연스러운 직립 대기 자세 (Idle Standing / Town Pose)
* 양발이 지면에 닿아 있음
* 팔은 자연스럽게 내리거나 가볍게 주먹을 쥔 정도
* 점프 금지, 전투 포즈 금지, 과장된 액션 금지
* 캐릭터 선택창 / 마을에 서 있는 느낌

장비 레이어 구조 (던파 아바타 슬롯)
* 머리(Hair Avatar)
* 모자(Hat)
* 얼굴(Face)
* 상의(Top)
* 하의(Bottom)
* 신발(Shoes)
* 허리(Waist)
* 피부(Skin)
* 무기(Weapon) — 원본에 무기가 있으면 손에 들거나 등에 멤
* 장비와 헤어가 캐릭터 개성을 결정해야 함

────────────────────
[PIXEL RENDERING SPEC]
중요:
고해상도 픽셀아트 금지
Ultra Detailed Pixel Art 금지
HD Pixel Art 금지
Fine-Grained Pixel Art 금지
부드러운 그라데이션 금지

목표:
**세로 약 120~160px 게임 스프라이트를 계단현상이 보이게 확대한 느낌**

* Low-resolution Korean MMORPG sprite (Dungeon Fighter Online style)
* Enlarged in-game sprite with visible pixel stair-stepping
* Grid-aligned chunky pixel structure
* Hand-pixeled look (2000s Neople dot art)
* Dark 1px outline (검은색~짙은 갈색 외곽선, 부분적으로 선택적 아웃라인)
* Limited color palette (재질당 3~5톤)
* Cel-shading style flat pixel clusters (셀 셰이딩 덩어리 음영)
* 광원은 좌상단 고정, 강한 명암 대비
* 피부는 따뜻한 톤 + 진한 갈색 음영 (던파 특유의 구릿빛 셰이딩)
* Minimal dithering (거의 사용하지 않음)
* No smooth gradients
* No airbrush effects
* No anti-aliasing against background

────────────────────
[출력 조건]
Canvas Size: 1080 x 1080
Perfect Square Format
Solid Neutral Gray Background (#808080) — 던파 아바타 시트 배경색
Single Character Only
Full Body Visible (머리끝~발끝)
Centered Composition
Character Occupies Approximately 80% Of Canvas Height
No Cropping
No Additional Characters
No Pets
No Environment
No Scene
No Background Objects
No Ground Shadow (아주 옅은 타원 그림자 1개만 허용)
No Text
No Logo
No Watermark
No UI

────────────────────
[절대 금지]
MapleStory Style (치비/SD 비율 금지 — 가장 흔한 실패 원인)
Chibi Proportions
2-Head / 3-Head Proportions
Big Head Small Body
Pokemon Style
Terraria Style
Stardew Valley Style
Metal Slug Style
Octopath Traveler Style
JRPG Battle Sprite
Western Cartoon
Disney Style
Realistic
Semi Realistic
3D Render
Illustration
Concept Art
Splash Art
Poster
Wallpaper
Anime Illustration
Digital Painting
Cinematic Lighting
Ultra Detailed Sprite
High Definition Pixel Art
Fine-Grained Pixel Art
Smooth Gradient Shading
Airbrush Shading
Soft Glow Effects

────────────────────
Create the person or character shown in the uploaded image as a true Dungeon & Fighter (DNF / Dungeon Fighter Online) player avatar sprite.
The result must look like an actual DNF player character sprite ripped from the game client and enlarged — realistic 7-head-tall proportions, hand-pixeled Neople dot art, dark outlines, cel-shaded pixel clusters — converted from the uploaded subject, not a generic pixel-art character and absolutely NOT a chibi/MapleStory-style character.
