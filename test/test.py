import time

from helpers import get_dev, draw_progress_bar

# ---------- CONFIG ----------
# A = square, B = rectangle
WIDTH_A, HEIGHT_A = 128, 32
WIDTH_B, HEIGHT_B = 128, 64

BUS_A, ADDR_A = 1, 0x3C         # /dev/i2c-1
BUS_B, ADDR_B = 3, 0x3C         # /dev/i2c-3

FPS = 25                        # target frames per second (software I2C likes 15–25)
SCROLL_PX_PER_SEC = 40          # marquee speed
GAP_PX = 32                     # gap between repeated song titles
# ----------------------------

if __name__ == '__main__':
    s = time.monotonic()
    frame_time = 1.0 / FPS
    devA = get_dev('a')
    devB = get_dev('b')
    try:
        while True:
            now = time.monotonic()
            elapsed = now - s

            frameA = draw_progress_bar(WIDTH_A, WIDTH_A, elapsed, 30, title='Playing')
            frameB = draw_progress_bar(WIDTH_B, WIDTH_B, elapsed, 15, title='Fart')

            devA.display(frameA)
            devB.display(frameB)

            took = time.monotonic() - now
            delay = frame_time - took
            if delay > 0:
                time.sleep(delay)


    except KeyboardInterrupt:
        devA.clear()
        devB.clear()

