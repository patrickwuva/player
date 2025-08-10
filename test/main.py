# two_oled_anim.py
from luma.core.interface.serial import i2c
from luma.oled.device import ssd1306
from PIL import Image, ImageDraw, ImageFont
import time

# ---------- CONFIG ----------
# A = square, B = rectangle
WIDTH_A, HEIGHT_A = 128, 64     # adjust if needed
WIDTH_B, HEIGHT_B = 128, 32     # adjust if needed

BUS_A, ADDR_A = 1, 0x3C         # /dev/i2c-1
BUS_B, ADDR_B = 3, 0x3C         # /dev/i2c-3

SCROLL_SPEED = 0.02             # seconds between frames
PROGRESS_DURATION = 5.0         # seconds for full bar (example)
# ----------------------------

# Load font
try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
except Exception:
    font = ImageFont.load_default()

def text_width_px(text, font):
    # robust width calc for Pillow default/TTF
    try:
        return int(font.getlength(text))
    except Exception:
        # fallback via bounding box
        img = Image.new("1", (1,1))
        d = ImageDraw.Draw(img)
        return d.textbbox((0,0), text, font=font)[2]

# Devices
devA = ssd1306(i2c(port=BUS_A, address=ADDR_A), width=WIDTH_A, height=HEIGHT_A)
devB = ssd1306(i2c(port=BUS_B, address=ADDR_B), width=WIDTH_B, height=HEIGHT_B)

def scroll_text(device, w, h, text, speed=SCROLL_SPEED, y=None, pad=24, repeat=1):
    """
    Horizontal marquee:
      - pad: blank spacing between repeats
      - repeat: how many times to scroll across
      - y: baseline y; if None, vertically centered
    """
    tw = text_width_px(text, font)
    gap = pad
    canvas_w = tw + w + gap
    img = Image.new("1", (canvas_w, h))
    d = ImageDraw.Draw(img)
    if y is None:
        # try to vertically center 8–12 px text nicely
        y = max(0, (h - 12) // 2)
    d.text((w, y), text, fill=1, font=font)  # start off-screen to the right

    for _ in range(repeat):
        for x in range(0, tw + gap + w):
            frame = img.crop((x, 0, x + w, h))
            device.display(frame)
            time.sleep(speed)

def progress_bar(device, w, h, pct):
    """
    pct: 0.0..1.0
    Draws an outlined bar with fill proportional to pct.
    """
    pct = max(0.0, min(1.0, float(pct)))
    img = Image.new("1", (w, h))
    d = ImageDraw.Draw(img)

    bar_h = max(6, h // 6)               # thickness ~1/6 screen height
    top = (h - bar_h) // 2
    bottom = top + bar_h
    d.rectangle((0, top, w-1, bottom), outline=1, fill=0)

    fill_w = int((w-2) * pct)
    if fill_w > 0:
        d.rectangle((1, top+1, 1 + fill_w, bottom-1), outline=1, fill=1)

    device.display(img)

def demo():
    # Show titles first
    scroll_text(devA, WIDTH_A, HEIGHT_A, "Square A: Hello from bus 1", repeat=1)
    scroll_text(devB, WIDTH_B, HEIGHT_B, "Rectangle B: Hello from bus 3", repeat=1)

    # Demo: A shows scrolling song title while B shows progress
    song = "Artist - Fancy Long Song Title (Live at The Tiny Desk 2025)"
    t0 = time.time()
    duration = PROGRESS_DURATION  # pretend the song is short for demo

    # Prebuild the title scroller image once by calling scroll in short chunks
    # We'll interleave: one step of scroll on A, then update progress on B.
    tw = text_width_px(song, font)
    pad = 32
    canvas_w = tw + WIDTH_A + pad
    imgA = Image.new("1", (canvas_w, HEIGHT_A))
    dA = ImageDraw.Draw(imgA)
    yA = max(0, (HEIGHT_A - 12) // 2)
    dA.text((WIDTH_A, yA), song, fill=1, font=font)

    x = 0
    while True:
        # frame for A (scroll one pixel)
        frameA = imgA.crop((x, 0, x + WIDTH_A, HEIGHT_A))
        devA.display(frameA)
        x += 1
        if x >= (tw + pad + WIDTH_A):
            x = 0  # loop marquee

        # update B progress
        elapsed = time.time() - t0
        pct = (elapsed % duration) / duration  # loop 0..1
        progress_bar(devB, WIDTH_B, HEIGHT_B, pct)

        time.sleep(SCROLL_SPEED)

if __name__ == "__main__":
    try:
        demo()
    except KeyboardInterrupt:
        devA.clear()
        devB.clear()

