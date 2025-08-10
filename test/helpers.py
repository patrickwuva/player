from luma.core.interface.serial import i2c
from luma.oled.device import ssd1306
from PIL import Image, ImageDraw, ImageFont
import time
import math
from functools import lru_cache

# ---------- CONFIG ----------
WIDTH_A, HEIGHT_A = 128, 64
WIDTH_B, HEIGHT_B = 128, 32

BUS_A, ADDR_A = 1, 0x3C
BUS_B, ADDR_B = 3, 0x3C

FPS = 25
SCROLL_PX_PER_SEC = 40
GAP_PX = 32 
# ----------------------------

try:
    FONT = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
except Exception:
    FONT = ImageFont.load_default()

@lru_cache
def get_dev(name):
    if name == 'a':
        return ssd1306(i2c(port=BUS_A, address=ADDR_A), width=WIDTH_A, height=HEIGHT_A)
    else:
        return ssd1306(i2c(port=BUS_B, address=ADDR_B), width=WIDTH_B, height=HEIGHT_B)

def mmss(seconds):
    seconds = max(0, int(seconds))
    return f"{seconds//60:02d}:{seconds%60:02d}"

def text_w(text, font=FONT):
    try:
        return int(font.getlength(text))
    except Exception:
        img = Image.new("1", (1,1))
        d = ImageDraw.Draw(img)
        return d.textbbox((0,0), text, font=font)[2]

def draw_progress_bar(w, h, elapsed, duration, title=None):
    elapsed = max(0.0, min(duration, float(elapsed)))
    pct = 0.0 if duration <= 0 else elapsed / duration

    img = Image.new("1", (w, h))
    d = ImageDraw.Draw(img)

    top_text_h = 0
    if title:
        max_chars = max(6, int(w / 7))
        txt = title if len(title) <= max_chars else title[:max_chars-1] + "…"
        d.text((0, 0), txt, fill=1, font=FONT)
        top_text_h = 12

    bar_h = max(6, (h - top_text_h) // 3)
    top = top_text_h + (h - top_text_h - bar_h) // 2
    bottom = top + bar_h

    d.rectangle((0, top, w-1, bottom), outline=1, fill=0)
    fill_w = 1 + int((w-2) * pct)
    d.rectangle((1, top+1, fill_w, bottom-1), outline=1, fill=1)

    tleft = mmss(elapsed)
    tright = mmss(duration)
    d.text((0, bottom + 1 if bottom + 10 < h else top - 12), tleft, fill=1, font=FONT)
    right_x = w - text_w(tright)
    d.text((right_x, bottom + 1 if bottom + 10 < h else top - 12), tright, fill=1, font=FONT)

    return img


