# two_oled_media.py
from luma.core.interface.serial import i2c
from luma.oled.device import ssd1306
from PIL import Image, ImageDraw, ImageFont
import time
import math

# ---------- CONFIG ----------
# A = square, B = rectangle
WIDTH_A, HEIGHT_A = 128, 64
WIDTH_B, HEIGHT_B = 128, 32

BUS_A, ADDR_A = 1, 0x3C         # /dev/i2c-1
BUS_B, ADDR_B = 3, 0x3C         # /dev/i2c-3

FPS = 25                        # target frames per second (software I2C likes 15–25)
SCROLL_PX_PER_SEC = 40          # marquee speed
GAP_PX = 32                     # gap between repeated song titles
# ----------------------------

# Load font
try:
    FONT = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
except Exception:
    FONT = ImageFont.load_default()

def text_w(text, font=FONT):
    try:
        return int(font.getlength(text))
    except Exception:
        img = Image.new("1", (1,1))
        d = ImageDraw.Draw(img)
        return d.textbbox((0,0), text, font=font)[2]

# Devices
devA = ssd1306(i2c(port=BUS_A, address=ADDR_A), width=WIDTH_A, height=HEIGHT_A)
devB = ssd1306(i2c(port=BUS_B, address=ADDR_B), width=WIDTH_B, height=HEIGHT_B)

# ------- DRAW HELPERS -------

def draw_marquee_frame(w, h, text, t, px_per_sec=SCROLL_PX_PER_SEC, gap=GAP_PX):
    """
    Return an Image (w x h) containing a horizontally scrolling 'text' at time t.
    We draw text twice to create a seamless loop.
    """
    tw = text_w(text)
    period = (tw + gap) / px_per_sec  # seconds per full loop
    # position where left edge of the first text starts
    x = - (px_per_sec * (t % period)) % (tw + gap)

    img = Image.new("1", (w, h))
    d = ImageDraw.Draw(img)

    y = max(0, (h - 12) // 2)
    # draw two copies for wrap
    d.text((x, y), text, fill=1, font=FONT)
    d.text((x + tw + gap, y), text, fill=1, font=FONT)
    # optional top/bottom separators / border
    # d.rectangle((0,0,w-1,h-1), outline=1)
    return img

def mmss(seconds):
    seconds = max(0, int(seconds))
    return f"{seconds//60:02d}:{seconds%60:02d}"

def draw_progress_frame(w, h, elapsed, duration, title=None):
    """
    Draw a centered progress bar with timestamps; optional small title on top.
    """
    elapsed = max(0.0, min(duration, float(elapsed)))
    pct = 0.0 if duration <= 0 else elapsed / duration

    img = Image.new("1", (w, h))
    d = ImageDraw.Draw(img)

    top_text_h = 0
    if title:
        # one-line title across the top (truncate if too long)
        max_chars = max(6, int(w / 7))  # rough fit for default font
        txt = title if len(title) <= max_chars else title[:max_chars-1] + "…"
        d.text((0, 0), txt, fill=1, font=FONT)
        top_text_h = 12

    bar_h = max(6, (h - top_text_h) // 3)
    top = top_text_h + (h - top_text_h - bar_h) // 2
    bottom = top + bar_h

    # outline and fill
    d.rectangle((0, top, w-1, bottom), outline=1, fill=0)
    fill_w = 1 + int((w-2) * pct)
    d.rectangle((1, top+1, fill_w, bottom-1), outline=1, fill=1)

    # timestamps
    tleft = mmss(elapsed)
    tright = mmss(duration)
    d.text((0, bottom + 1 if bottom + 10 < h else top - 12), tleft, fill=1, font=FONT)
    # right-align duration
    right_x = w - text_w(tright)
    d.text((right_x, bottom + 1 if bottom + 10 < h else top - 12), tright, fill=1, font=FONT)

    return img

# ------- MAIN LOOP (LOCKSTEP) -------

def run_media_ui(song_title, duration_secs):
    start = time.monotonic()
    frame_time = 1.0 / FPS

    try:
        while True:
            now = time.monotonic()
            elapsed = now - start

            # A: marquee title (always loops)
            frameA = draw_marquee_frame(WIDTH_A, HEIGHT_A, song_title, t=elapsed)

            # B: progress bar synced to same clock
            frameB = draw_progress_frame(WIDTH_B, HEIGHT_B, elapsed, duration_secs, title="Playing")

            # Push both frames this tick (A then B)
            devA.display(frameA)
            devB.display(frameB)

            # sleep to cap FPS
            took = time.monotonic() - now
            delay = frame_time - took
            if delay > 0:
                time.sleep(delay)
    except KeyboardInterrupt:
        devA.clear()
        devB.clear()

if __name__ == "__main__":
    # Example “now playing”
    run_media_ui(
        song_title="Artist – Fancy Long Song Title (Live 2025)",
        duration_secs=245,  # e.g., 4:05
    )

