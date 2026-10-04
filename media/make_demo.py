# -*- coding: utf-8 -*-
#
# AutoNote for Notepad++ — © 2026 Himanshu Dadhich.
# Developed by Himanshu Dadhich. Released under the MIT License; see LICENSE.
#
"""
Renders the AutoNote demo animation (an illustration, not a screen recording).

Usage:  python make_demo.py            -> autonote-demo.mp4 and autonote-demo.gif
        python make_demo.py --stills   -> a few PNG frames for checking the layout
Needs Pillow and ffmpeg on PATH.
"""
import os
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

W = H = 1080
S = 2            # supersampling factor; frames are drawn at 2x and scaled down
FPS = 30
DURATION = 17.0  # the end card holds for about 5 seconds
OUT_DIR = os.path.dirname(os.path.abspath(__file__))
FONTS = r"C:\Windows\Fonts"

BG = (13, 17, 23)
CARD = (22, 27, 34)
CARD_LINE = (48, 54, 61)
WHITE = (240, 246, 252)
MUTED = (139, 148, 158)
GREEN = (63, 185, 80)
ORANGE = (240, 136, 62)
RED = (218, 54, 51)
WIN_BG = (255, 255, 255)
WIN_BAR = (233, 236, 239)
WIN_TABS = (222, 226, 230)
WIN_LINE = (206, 212, 218)
INK = (33, 37, 41)
INK_MUTED = (134, 142, 150)
GUTTER = (241, 243, 245)

FILE_NAME = "2026-10-04 client call points.txt"
LINES = [
    ("client call points", 1.2, 2.0),
    ("- send proposal by Friday", 3.7, 1.9),
    ("- follow up Monday", 6.0, 1.4),
]
T_NAMED = 4.1
# moments the status chip briefly shows "Saving…" while typing continues
SAVE_PULSES = (5.2, 6.6, 7.5)
T_CLOSE = 9.0
T_SYNC = 10.4
T_END = 11.8

CAPTIONS = [
    (0.0, "Never save a note in Notepad++ again."),
    (1.2, "Just type."),
    (T_NAMED, "AutoNote names the file from your first line."),
    (6.0, "Every edit saves itself in about 2 seconds."),
    (8.4, "Close the tab. No \u201cSave file?\u201d prompt."),
    (T_SYNC - 0.2, "Keep the folder in Drive. Your notes sync."),
]


def font(name, size):
    return ImageFont.truetype(os.path.join(FONTS, name), int(size * S))


F_CAPTION = font("seguisb.ttf", 46)
F_UI = font("segoeui.ttf", 22)
F_UI_BOLD = font("seguisb.ttf", 22)
F_TAB = font("segoeui.ttf", 21)
F_CODE = font("consola.ttf", 30)
F_FILE = font("consola.ttf", 23)
F_SMALL = font("segoeui.ttf", 20)
F_END_TITLE = font("segoeuib.ttf", 64)
F_END_SUB = font("segoeui.ttf", 32)
F_END_URL = font("consola.ttf", 28)
F_END_NAME = font("segoeuib.ttf", 52)
F_END_LABEL = font("segoeui.ttf", 28)


def clamp(value, low=0.0, high=1.0):
    return max(low, min(high, value))


def ease(value):
    value = clamp(value)
    return value * value * (3 - 2 * value)


def ramp(t, start, length):
    """0 before start, 1 after start+length, eased in between."""
    return ease((t - start) / length)


def mix(a, b, amount):
    amount = clamp(amount)
    return tuple(int(round(a[i] + (b[i] - a[i]) * amount)) for i in range(3))


def box(values):
    return [int(round(v * S)) for v in values]


def rounded(draw, rect, radius, fill, outline=None, width=1):
    draw.rounded_rectangle(box(rect), radius=int(radius * S), fill=fill,
                           outline=outline, width=int(width * S))


def text(draw, xy, value, fnt, fill, anchor="la"):
    draw.text((int(xy[0] * S), int(xy[1] * S)), value, font=fnt, fill=fill, anchor=anchor)


def text_width(draw, value, fnt):
    return draw.textlength(value, font=fnt) / S


def wrap(draw, value, fnt, max_width):
    lines, current = [], ""
    for word in value.split(" "):
        trial = (current + " " + word).strip()
        if text_width(draw, trial, fnt) <= max_width or not current:
            current = trial
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def check(draw, cx, cy, size, color, width=3):
    points = [(cx - size * 0.5, cy), (cx - size * 0.12, cy + size * 0.38), (cx + size * 0.55, cy - size * 0.4)]
    draw.line([(int(x * S), int(y * S)) for x, y in points], fill=color, width=int(width * S), joint="curve")


def cloud(draw, cx, cy, size, color):
    for dx, dy, r in ((-0.45, 0.12, 0.34), (0.0, -0.12, 0.46), (0.48, 0.14, 0.32)):
        x, y, rad = cx + dx * size, cy + dy * size, r * size
        draw.ellipse(box((x - rad, y - rad, x + rad, y + rad)), fill=color)
    draw.rectangle(box((cx - 0.45 * size, cy + 0.1 * size, cx + 0.48 * size, cy + 0.46 * size)), fill=color)


def typed(t):
    """Text of each line visible at time t."""
    visible = []
    for value, start, length in LINES:
        if t < start:
            break
        count = int(len(value) * clamp((t - start) / length))
        visible.append(value[:count])
    return visible


def typing_now(t):
    return any(start <= t <= start + length for _value, start, length in LINES)


def caption_at(t):
    current, since = CAPTIONS[0][1], CAPTIONS[0][0]
    for start, value in CAPTIONS:
        if t >= start:
            current, since = value, start
    return current, since


def draw_caption(draw, t):
    value, since = caption_at(t)
    color = mix(BG, WHITE, ramp(t, since, 0.3))
    lines = wrap(draw, value, F_CAPTION, 940)
    top = 128 - (len(lines) - 1) * 30
    for index, line in enumerate(lines):
        text(draw, (W / 2, top + index * 60), line, F_CAPTION, color, anchor="mm")


def draw_editor(draw, t):
    left, top, right, bottom = 70, 240, 1010, 790
    closing = ramp(t, T_CLOSE, 0.4)
    rounded(draw, (left, top, right, bottom), 14, WIN_BG, outline=WIN_LINE, width=1)
    # title bar
    rounded(draw, (left, top, right, top + 46), 14, WIN_BAR)
    draw.rectangle(box((left, top + 26, right, top + 46)), fill=WIN_BAR)
    text(draw, (left + 22, top + 23), "Notepad++", F_UI, INK_MUTED, anchor="lm")
    # window buttons: minimise, maximise, close
    mid = top + 23
    draw.line(box((right - 112, mid, right - 98, mid)), fill=INK_MUTED, width=int(1.5 * S))
    draw.rectangle(box((right - 73, mid - 7, right - 59, mid + 7)), outline=INK_MUTED, width=int(1.5 * S))
    for dx in (-1, 1):
        draw.line(box((right - 34, mid - 7 * dx, right - 20, mid + 7 * dx)), fill=INK_MUTED, width=int(1.5 * S))
    # tab strip
    strip_top = top + 46
    draw.rectangle(box((left + 1, strip_top, right - 1, strip_top + 46)), fill=WIN_TABS)
    named = ramp(t, T_NAMED, 0.35)
    label = FILE_NAME if t >= T_NAMED else "new 1"
    width_before = text_width(draw, "new 1", F_TAB) + 100
    width_after = text_width(draw, FILE_NAME, F_TAB) + 100
    tab_width = width_before + (width_after - width_before) * named
    tab_left = left + 12
    tab_fill = mix(WIN_BG, WIN_TABS, closing)
    rounded(draw, (tab_left, strip_top + 6, tab_left + tab_width, strip_top + 60), 8, tab_fill)
    glow = clamp(1 - (t - T_NAMED) / 1.4) if t >= T_NAMED else 0.0
    if glow > 0:
        rounded(draw, (tab_left, strip_top + 6, tab_left + tab_width, strip_top + 60), 8, None,
                outline=mix(WIN_BG, GREEN, glow), width=3)
    draw.rectangle(box((left + 1, strip_top + 46, right - 1, strip_top + 62)), fill=WIN_BG)
    has_text = t >= LINES[0][1] + 0.1
    saved = t >= T_NAMED and not any(start <= t < start + 0.4 for start in SAVE_PULSES)
    dot = GREEN if saved else (ORANGE if has_text else INK_MUTED)
    draw.ellipse(box((tab_left + 16, strip_top + 21, tab_left + 30, strip_top + 35)),
                 fill=mix(dot, WIN_TABS, closing))
    text(draw, (tab_left + 42, strip_top + 28), label, F_TAB, mix(INK, WIN_TABS, closing), anchor="lm")
    close_hot = ramp(t, T_CLOSE - 0.45, 0.2) * (1 - closing)
    cx, cy = tab_left + tab_width - 24, strip_top + 28
    if close_hot > 0:
        draw.ellipse(box((cx - 13, cy - 13, cx + 13, cy + 13)), fill=mix(WIN_BG, RED, close_hot))
    cross = mix(mix(INK_MUTED, WHITE, close_hot), WIN_TABS, closing)
    for dx in (-1, 1):
        draw.line(box((cx - 6, cy - 6 * dx, cx + 6, cy + 6 * dx)), fill=cross, width=int(2 * S))
    # text area
    area_top = strip_top + 62
    draw.rectangle(box((left + 1, area_top, left + 64, bottom - 44)), fill=GUTTER)
    lines = typed(t)
    row = 46
    for index in range(max(1, len(lines))):
        y = area_top + 18 + index * row
        text(draw, (left + 50, y), str(index + 1), F_CODE, mix(INK_MUTED, GUTTER, closing), anchor="ra")
    for index, value in enumerate(lines):
        y = area_top + 18 + index * row
        text(draw, (left + 84, y), value, F_CODE, mix(INK, WIN_BG, closing))
    if closing < 0.05 and (typing_now(t) or int(t * 2) % 2 == 0):
        last = lines[-1] if lines else ""
        cursor_x = left + 84 + text_width(draw, last, F_CODE) + 2
        cursor_y = area_top + 16 + (max(1, len(lines)) - 1) * row
        draw.rectangle(box((cursor_x, cursor_y, cursor_x + 3, cursor_y + 36)), fill=INK)
    if closing > 0:
        text(draw, ((left + right) / 2 + 30, (area_top + bottom - 44) / 2), "Tab closed. Nothing to save.",
             F_UI, mix(WIN_BG, INK_MUTED, closing), anchor="mm")
    # status bar
    draw.line(box((left + 1, bottom - 44, right - 1, bottom - 44)), fill=WIN_LINE, width=S)
    line_no = max(1, len(lines))
    col = len(lines[-1]) + 1 if lines else 1
    text(draw, (left + 20, bottom - 22), "Ln %d, Col %d" % (line_no, col), F_SMALL,
         mix(INK_MUTED, WIN_BG, closing), anchor="lm")
    if has_text and closing < 1:
        if saved:
            chip, color = "Saved", GREEN
        elif t >= T_NAMED:
            chip, color = "Saving\u2026", ORANGE
        else:
            chip, color = "Not saved yet", ORANGE
        chip_width = text_width(draw, chip, F_UI_BOLD) + (56 if saved else 30)
        rounded(draw, (right - 20 - chip_width, bottom - 38, right - 20, bottom - 8), 15,
                mix(mix(WIN_BG, color, 0.16), WIN_BG, closing))
        x = right - 20 - chip_width + 15
        if saved:
            check(draw, x + 9, bottom - 23, 14, mix(color, WIN_BG, closing))
            x += 26
        text(draw, (x, bottom - 23), chip, F_UI_BOLD, mix(mix(color, INK, 0.25), WIN_BG, closing), anchor="lm")


def draw_folder(draw, t):
    left, top, right, bottom = 70, 826, 1010, 986
    rounded(draw, (left, top, right, bottom), 14, CARD, outline=CARD_LINE, width=1)
    text(draw, (left + 26, top + 34), "Notes folder", F_UI_BOLD, WHITE, anchor="lm")
    text(draw, (left + 26 + text_width(draw, "Notes folder", F_UI_BOLD) + 14, top + 34), "D:\\Notes",
         F_UI, MUTED, anchor="lm")
    appear = ramp(t, T_NAMED + 0.1, 0.45)
    if appear <= 0:
        text(draw, (left + 26, top + 100), "empty", F_UI, mix(CARD, MUTED, 0.6), anchor="lm")
        return
    offset = (1 - appear) * 18
    row_top = top + 68 + offset
    rounded(draw, (left + 18, row_top, right - 18, row_top + 64), 10, mix(CARD, (33, 40, 50), appear))
    icon_x, icon_y = left + 40, row_top + 16
    rounded(draw, (icon_x, icon_y, icon_x + 26, icon_y + 32), 4, mix(CARD, WHITE, appear * 0.9))
    for index in range(3):
        y = icon_y + 9 + index * 7
        draw.line(box((icon_x + 6, y, icon_x + 20, y)), fill=mix(CARD, MUTED, appear), width=S)
    text(draw, (icon_x + 44, row_top + 32), FILE_NAME, F_FILE, mix(CARD, WHITE, appear), anchor="lm")
    sync = ramp(t, T_SYNC, 0.4)
    if sync > 0:
        label = "Synced"
        badge_width = text_width(draw, label, F_UI_BOLD) + 70
        badge_left = right - 34 - badge_width
        rounded(draw, (badge_left, row_top + 14, right - 34, row_top + 50), 18,
                mix((33, 40, 50), mix((33, 40, 50), GREEN, 0.22), sync))
        cloud(draw, badge_left + 30, row_top + 30, 22, mix((33, 40, 50), GREEN, sync))
        text(draw, (badge_left + 54, row_top + 32), label, F_UI_BOLD, mix((33, 40, 50), GREEN, sync), anchor="lm")


def end_card():
    image = Image.new("RGB", (W * S, H * S), BG)
    draw = ImageDraw.Draw(image)
    text(draw, (W / 2, 250), "AutoNote", F_END_TITLE, WHITE, anchor="mm")
    text(draw, (W / 2, 328), "for Notepad++", F_END_SUB, MUTED, anchor="mm")
    draw.line(box((W / 2 - 60, 388, W / 2 + 60, 388)), fill=GREEN, width=int(4 * S))
    text(draw, (W / 2, 450), "Free and open source. MIT license.", F_END_SUB, WHITE, anchor="mm")
    url = "github.com/kushaai/autonote-for-notepadpp"
    width = text_width(draw, url, F_END_URL) + 56
    rounded(draw, (W / 2 - width / 2, 510, W / 2 + width / 2, 570), 12, CARD, outline=CARD_LINE, width=1)
    text(draw, (W / 2, 540), url, F_END_URL, GREEN, anchor="mm")
    # credits
    text(draw, (W / 2, 676), "Built by", F_END_LABEL, MUTED, anchor="mm")
    text(draw, (W / 2, 738), "Himanshu Dadhich", F_END_NAME, WHITE, anchor="mm")
    text(draw, (W / 2, 822), "Kusha AI", F_END_NAME, GREEN, anchor="mm")
    text(draw, (W / 2, 878), "kushaai.com", F_END_LABEL, MUTED, anchor="mm")
    return image


END_CARD = None


def frame(t):
    global END_CARD
    image = Image.new("RGB", (W * S, H * S), BG)
    draw = ImageDraw.Draw(image)
    draw_caption(draw, t)
    draw_editor(draw, t)
    draw_folder(draw, t)
    text(draw, (W / 2, 1034), "github.com/kushaai/autonote-for-notepadpp", F_SMALL, MUTED, anchor="mm")
    fade = ramp(t, T_END, 0.5)
    if fade > 0:
        if END_CARD is None:
            END_CARD = end_card()
        image = Image.blend(image, END_CARD, fade)
    return image.resize((W, H), Image.LANCZOS)


def render_video():
    mp4 = os.path.join(OUT_DIR, "autonote-demo.mp4")
    gif = os.path.join(OUT_DIR, "autonote-demo.gif")
    encoder = subprocess.Popen(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
         "-s", "%dx%d" % (W, H), "-r", str(FPS), "-i", "-",
         "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-movflags", "+faststart", mp4],
        stdin=subprocess.PIPE)
    total = int(DURATION * FPS)
    for index in range(total):
        encoder.stdin.write(frame(index / FPS).tobytes())
    encoder.stdin.close()
    if encoder.wait() != 0:
        raise SystemExit("ffmpeg failed while writing the mp4")
    subprocess.check_call(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", mp4, "-vf",
         "fps=15,scale=720:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=128[p];[b][p]paletteuse=dither=bayer:bayer_scale=4",
         gif])
    for path in (mp4, gif):
        print("%s  %.1f MB" % (path, os.path.getsize(path) / 1e6))


def render_stills():
    for t in (0.6, 2.4, 4.4, 7.0, 8.9, 9.6, 11.0, 13.0):
        path = os.path.join(OUT_DIR, "still-%04.1f.png" % t)
        frame(t).save(path)
        print(path)


if __name__ == "__main__":
    if "--stills" in sys.argv:
        render_stills()
    else:
        render_video()
