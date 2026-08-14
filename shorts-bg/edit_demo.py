#!/usr/bin/env python3
"""쇼츠 편집 파이프라인 데모.

배경 PNG + 컷(이미지/영상 프레임) + 자막을 프레임 단위로 합성해
ffmpeg(libx264)로 인코딩한다. 컷 리스트만 바꾸면 실제 편집에 그대로 확장 가능.

효과: Ken Burns 줌, 자막 팝인(스케일+알파), 라벨 칩 팝, 엔딩 카드 스케일 팝.
실행: python3 edit_demo.py  (shorts-bg 디렉터리에서)
"""
from PIL import Image, ImageDraw, ImageFont
import subprocess

S = '/tmp/claude-0/-home-user-Claude-Code/879911d1-3b04-5166-aa89-bdb3a7912bf4/scratchpad'
FF = '/usr/local/lib/python3.11/dist-packages/imageio_ffmpeg/binaries/ffmpeg-linux-x86_64-v7.0.2'
FPS = 24
W, H = 1080, 1920
FRAME_BOX = (105, 571, 975, 1441)   # 콘텐츠 프레임 내부 870×870
SUB_Y = 1520                        # 자막 기준선

bg = Image.open('output/background.png').convert('RGB')
bold = ImageFont.truetype('fonts/GmarketSansBold.ttf', 46)
chipf = ImageFont.truetype('fonts/GmarketSansBold.ttf', 30)


def media_square(path):
    """편집자 A 프록시(480×854)에서 콘텐츠 정사각을 잘라 확대 여유분 포함 리사이즈."""
    src = Image.open(path)
    return src.crop((47, 191, 433, 573)).resize((1100, 1100), Image.LANCZOS)


def sub_layer(lines, hl_word=None):
    im = Image.new('RGBA', (W, 220), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    y = 10
    for line in lines:
        w = d.textlength(line, font=bold)
        x = (W - w) / 2
        if hl_word and hl_word in line:
            pre = line.split(hl_word)[0]
            x0 = x + d.textlength(pre, font=bold)
            x1 = x0 + d.textlength(hl_word, font=bold)
            d.rounded_rectangle([x0 - 8, y - 2, x1 + 8, y + 58], 8, fill=(255, 211, 56, 255))
        d.text((x, y), line, font=bold, fill=(23, 24, 26, 255))
        y += 66
    return im


def label_chip(text):
    d0 = ImageDraw.Draw(Image.new('RGB', (10, 10)))
    tw = d0.textlength(text, font=chipf)
    im = Image.new('RGBA', (int(tw) + 56, 62), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([3, 3, im.width - 6, 56], 14, fill=(255, 211, 56, 255),
                        outline=(23, 24, 26, 255), width=4)
    d.text((28, 14), text, font=chipf, fill=(23, 24, 26, 255))
    return im


def ease_out_back(t):
    c1, c3 = 1.70158, 2.70158
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2


frames = []


def content_cut(media, sub_lines, hl, dur, chip=None, zoom=(1.0, 1.08)):
    n = int(dur * FPS)
    sub = sub_layer(sub_lines, hl)
    chip_im = label_chip(chip) if chip else None
    for i in range(n):
        t = i / max(n - 1, 1)
        f = bg.copy()
        z = zoom[0] + (zoom[1] - zoom[0]) * t
        side = int(1100 / z)
        m = media.crop((550 - side // 2, 550 - side // 2,
                        550 + side // 2, 550 + side // 2)).resize((870, 870), Image.BILINEAR)
        f.paste(m, (FRAME_BOX[0], FRAME_BOX[1]))
        f = f.convert('RGBA')
        if chip_im is not None:
            k = min(1.0, i / 5)
            s = ease_out_back(k)
            ci = chip_im.resize((max(1, int(chip_im.width * s)), max(1, int(chip_im.height * s))))
            f.alpha_composite(ci, (135, 610))
        k = min(1.0, i / 5)
        s = 0.85 + 0.15 * ease_out_back(k)
        sl = sub.resize((int(W * s), int(220 * s)))
        a = sl.split()[3].point(lambda p: int(p * k))
        sl.putalpha(a)
        f.alpha_composite(sl, ((W - sl.width) // 2, SUB_Y - (sl.height - 220) // 2))
        frames.append(f.convert('RGB'))


# ── 컷 리스트 ──────────────────────────────────────────────
content_cut(media_square(f'{S}/frames/f10.png'),
            ['근데 요즘 승모근이랑', '팔꿈치를 다쳐서'], '승모근', 2.5)
content_cut(media_square(f'{S}/frames/f15.png'),
            ['운동 1년 못하고 수술까지...'], '수술', 2.5, chip='쓰리스타킬러 셰프 인터뷰')
content_cut(media_square(f'{S}/frames/f5.png'),
            ['쓰리스타킬러 셰프도 그래서'], None, 2.0)

# 엔딩: 카드 스케일 팝 + 화살표 지연 등장
end = Image.open('output/endcard.png').convert('RGBA')
arrow = Image.open('output/endcard-arrow.png')
for i in range(int(3 * FPS)):
    f = bg.copy().convert('RGBA')
    k = min(1.0, i / 7)
    s = 0.92 + 0.08 * ease_out_back(k)
    ei = end.resize((int(870 * s), int(870 * s)))
    cx, cy = FRAME_BOX[0] + 435, FRAME_BOX[1] + 435
    f.alpha_composite(ei, (cx - ei.width // 2, cy - ei.height // 2))
    if i > 12:
        k2 = min(1.0, (i - 12) / 5)
        a2 = arrow.split()[3].point(lambda p: int(p * k2))
        ar = arrow.copy()
        ar.putalpha(a2)
        f.alpha_composite(ar, (90, 1476))
    frames.append(f.convert('RGB'))

# ── 인코딩 ────────────────────────────────────────────────
p = subprocess.Popen([FF, '-y', '-hide_banner', '-loglevel', 'error',
                      '-f', 'image2pipe', '-framerate', str(FPS), '-vcodec', 'png', '-i', '-',
                      '-c:v', 'libx264', '-preset', 'medium', '-crf', '19', '-pix_fmt', 'yuv420p',
                      'output/demo_edit.mp4'], stdin=subprocess.PIPE)
for fr in frames:
    fr.save(p.stdin, 'PNG')
p.stdin.close()
p.wait()
print('frames:', len(frames), 'rc:', p.returncode)
