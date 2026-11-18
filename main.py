#!/usr/bin/env python3
"""Draw one front-page image that sums up the world news of
Tuesday 17 November 2026, and write it to /output/entry.png.

Pure Python 3 standard library: the picture is painted pixel by pixel
into a frame buffer and encoded as a PNG with zlib + struct.
No network, no input files, deterministic output.
"""

import os
import struct
import zlib

WIDTH = 1024
HEIGHT = 1024

# ---------------------------------------------------------------- palette
PAPER = (247, 242, 231)
PANEL = (255, 253, 246)
INK = (20, 33, 61)
RED = (193, 39, 45)
GOLD = (224, 165, 38)
TEAL = (29, 120, 116)
SKY = (174, 205, 224)
SEA = (64, 110, 150)
GREY = (105, 110, 118)
WHITE = (255, 255, 255)
BLACK = (12, 14, 18)


# ---------------------------------------------------------------- png out
def encode_png(width, height, rgb):
    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data +
                struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

    rows = []
    stride = width * 3
    for y in range(height):
        rows.append(b"\x00" + bytes(rgb[y * stride:(y + 1) * stride]))
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) +
            chunk(b"IDAT", zlib.compress(b"".join(rows), 9)) +
            chunk(b"IEND", b""))


# ---------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, width, height, colour):
        self.w = width
        self.h = height
        self.buf = bytearray(bytes(colour) * (width * height))

    def px(self, x, y, colour):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.buf[i:i + 3] = bytes(colour)

    def rect(self, x, y, w, h, colour):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.px(xx, yy, colour)

    def frame(self, x, y, w, h, colour, thick=3):
        self.rect(x, y, w, thick, colour)
        self.rect(x, y + h - thick, w, thick, colour)
        self.rect(x, y, thick, h, colour)
        self.rect(x + w - thick, y, thick, h, colour)

    def disc(self, cx, cy, r, colour):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                if (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r:
                    self.px(xx, yy, colour)

    def ring(self, cx, cy, r, colour, thick=3):
        for yy in range(cy - r - thick, cy + r + thick + 1):
            for xx in range(cx - r - thick, cx + r + thick + 1):
                d = ((xx - cx) ** 2 + (yy - cy) ** 2) ** 0.5
                if r - thick <= d <= r:
                    self.px(xx, yy, colour)

    def line(self, x0, y0, x1, y1, colour, thick=3):
        steps = max(abs(x1 - x0), abs(y1 - y0), 1)
        r = max(thick // 2, 1)
        for i in range(steps + 1):
            x = x0 + (x1 - x0) * i // steps
            y = y0 + (y1 - y0) * i // steps
            self.disc(x, y, r, colour)

    def tri(self, ax, ay, bx, by, cx, cy, colour):
        minx, maxx = min(ax, bx, cx), max(ax, bx, cx)
        miny, maxy = min(ay, by, cy), max(ay, by, cy)
        d = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
        if d == 0:
            return
        for yy in range(miny, maxy + 1):
            for xx in range(minx, maxx + 1):
                w0 = ((by - cy) * (xx - cx) + (cx - bx) * (yy - cy)) / d
                w1 = ((cy - ay) * (xx - cx) + (ax - cx) * (yy - cy)) / d
                w2 = 1 - w0 - w1
                if w0 >= 0 and w1 >= 0 and w2 >= 0:
                    self.px(xx, yy, colour)


# ---------------------------------------------------------------- font 5x7
FONT = {
    "A": (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    "D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    "H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"),
    "J": ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    "K": ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "M": ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "N": ("#...#", "#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#"),
    "O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "P": ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "Q": (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    "R": ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "S": (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    "T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "U": ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "V": ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "W": ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    "X": ("#...#", ".#.#.", "..#..", "..#..", "..#..", ".#.#.", "#...#"),
    "Y": ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "Z": ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    "0": (".###.", "#..##", "#.#.#", "##..#", "#...#", "#...#", ".###."),
    "1": ("..#..", ".##..", "#.#..", "..#..", "..#..", "..#..", "#####"),
    "2": (".###.", "#...#", "....#", "..##.", ".#...", "#....", "#####"),
    "3": ("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
    "4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    "5": ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    "6": (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    "7": ("#####", "....#", "...#.", "..#..", "..#..", "..#..", "..#.."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    ".": (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ",": (".....", ".....", ".....", ".....", ".##..", ".##..", ".#..."),
    ":": (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    ";": (".....", ".##..", ".##..", ".....", ".##..", ".##..", ".#..."),
    "!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    "?": (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
    "'": ("..#..", "..#..", ".#...", ".....", ".....", ".....", "....."),
    "-": (".....", ".....", ".....", "#####", ".....", ".....", "....."),
    "+": (".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."),
    "/": ("....#", "....#", "...#.", "..#..", ".#...", "#....", "#...."),
    "(": ("...##", "..#..", ".#...", ".#...", ".#...", "..#..", "...##"),
    ")": ("##...", "..#..", "...#.", "...#.", "...#.", "..#..", "##..."),
    "&": (".##..", "#..#.", "#.#..", ".#...", "#.#.#", "#..#.", ".##.#"),
    "%": ("##..#", "##.#.", "....#", "...#.", "..#..", ".#...", "#..##"),
    "$": ("..#..", ".####", "#.#..", ".###.", "..#.#", "####.", "..#.."),
}


def text_width(text, scale):
    return len(text) * 6 * scale - scale


def draw_text(cv, x, y, text, colour, scale=3):
    cx = x
    for ch in text.upper():
        glyph = FONT.get(ch, FONT[" "])
        for row_i, row in enumerate(glyph):
            for col_i, cell in enumerate(row):
                if cell == "#":
                    cv.rect(cx + col_i * scale, y + row_i * scale,
                            scale, scale, colour)
        cx += 6 * scale
    return cx


def draw_text_centred(cv, cx, y, text, colour, scale=3):
    return draw_text(cv, cx - text_width(text, scale) // 2, y,
                     text, colour, scale)


def wrap(text, scale, max_width):
    words = text.split()
    lines = []
    cur = ""
    for word in words:
        trial = word if not cur else cur + " " + word
        if text_width(trial, scale) <= max_width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


# ---------------------------------------------------------------- icons
def icon_bridge(cv, x, y):
    # two pylons, a deck with a broken middle, water below
    cv.rect(x + 8, y + 26, 10, 74, INK)
    cv.rect(x + 100, y + 26, 10, 74, INK)
    cv.rect(x, y + 20, 118, 7, INK)
    cv.line(x + 13, y + 22, x + 52, y + 58, INK, 2)
    cv.line(x + 105, y + 22, x + 66, y + 58, INK, 2)
    cv.rect(x, y + 58, 46, 8, RED)
    cv.line(x + 46, y + 62, x + 62, y + 84, RED, 5)
    cv.rect(x + 72, y + 58, 46, 8, RED)
    # the fallen span in the water, with splash marks
    cv.line(x + 50, y + 104, x + 72, y + 96, RED, 5)
    cv.line(x + 52, y + 92, x + 48, y + 84, SEA, 3)
    cv.line(x + 62, y + 90, x + 62, y + 82, SEA, 3)
    cv.line(x + 72, y + 92, x + 76, y + 84, SEA, 3)
    for i in range(4):
        wx = x + 4 + i * 30
        cv.line(wx, y + 112, wx + 8, y + 106, SEA, 3)
        cv.line(wx + 8, y + 106, wx + 16, y + 112, SEA, 3)


def icon_plane_down(cv, x, y):
    for i, (sx, sy, r) in enumerate(((18, 16, 9), (34, 30, 12), (52, 44, 14))):
        cv.disc(x + sx, y + sy, r, GREY)
    cv.line(x + 58, y + 52, x + 96, y + 90, INK, 9)
    cv.tri(x + 70, y + 62, x + 92, y + 56, x + 84, y + 82, RED)
    cv.tri(x + 92, y + 84, x + 108, y + 76, x + 104, y + 96, INK)
    cv.line(x + 60, y + 50, x + 48, y + 34, INK, 6)
    cv.line(x + 8, y + 116, x + 110, y + 116, INK, 3)
    cv.line(x + 78, y + 108, x + 100, y + 96, RED, 4)


def icon_globe(cv, x, y):
    cx, cy, r = x + 56, y + 62, 44
    cv.ring(cx, cy, r, TEAL, 4)
    for dx in (-22, 0, 22):
        for t in range(-40, 41, 4):
            yy = cy + t
            half = int((r * r - t * t) ** 0.5)
            xx = cx + int(dx * half / r)
            cv.px(xx, yy, TEAL)
            cv.px(xx + 1, yy, TEAL)
    cv.line(cx - r, cy, cx + r, cy, TEAL, 2)
    cv.line(cx - r, cy - 20, cx + r, cy - 20, TEAL, 2)
    cv.line(cx - r, cy + 20, cx + r, cy + 20, TEAL, 2)
    cv.line(x + 88, y + 8, x + 108, y + 20, RED, 5)
    cv.tri(x + 100, y + 10, x + 114, y + 22, x + 98, y + 24, RED)


def icon_syringe(cv, x, y):
    cv.line(x + 22, y + 88, x + 62, y + 48, INK, 13)
    cv.line(x + 62, y + 48, x + 84, y + 26, INK, 7)
    cv.line(x + 84, y + 26, x + 102, y + 8, GREY, 3)
    cv.line(x + 14, y + 80, x + 30, y + 96, INK, 6)
    cv.line(x + 70, y + 40, x + 82, y + 52, RED, 4)
    vx, vy = x + 92, y + 88
    cv.disc(vx, vy, 15, RED)
    for ang in range(0, 360, 45):
        import math
        dx = int(21 * math.cos(math.radians(ang)))
        dy = int(21 * math.sin(math.radians(ang)))
        cv.line(vx, vy, vx + dx, vy + dy, RED, 3)
        cv.disc(vx + dx, vy + dy, 3, RED)


def icon_crowd(cv, x, y):
    cv.rect(x + 18, y + 6, 82, 30, GOLD)
    cv.frame(x + 18, y + 6, 82, 30, INK, 3)
    draw_text(cv, x + 28, y + 16, "PAY!", INK, 2)
    cv.line(x + 24, y + 36, x + 24, y + 62, INK, 4)
    cv.line(x + 94, y + 36, x + 94, y + 62, INK, 4)
    for i, hx in enumerate((28, 56, 84)):
        cv.disc(x + hx, y + 76, 10, INK)
        cv.rect(x + hx - 11, y + 88, 22, 30, TEAL if i == 1 else RED)


def icon_chip(cv, x, y):
    cv.frame(x + 28, y + 22, 62, 62, INK, 5)
    cv.frame(x + 44, y + 38, 30, 30, TEAL, 3)
    draw_text(cv, x + 47, y + 49, "AI", TEAL, 2)
    for i in range(3):
        p = 34 + i * 18
        cv.rect(x + p, y + 8, 6, 14, INK)
        cv.rect(x + p, y + 84, 6, 14, INK)
        cv.rect(x + 14, y + p, 14, 6, INK)
        cv.rect(x + 90, y + p, 14, 6, INK)


# ---------------------------------------------------------------- layout
def panel(cv, x, y, w, h, kicker, headline, body, icon):
    cv.rect(x, y, w, h, PANEL)
    cv.frame(x, y, w, h, INK, 3)
    icon(cv, x + 14, y + 52)
    tx = x + 146
    tw = w - 162
    draw_text(cv, tx, y + 14, kicker, RED, 2)
    cv.rect(tx, y + 32, 54, 3, GOLD)
    ly = y + 44
    for ln in wrap(headline, 3, tw):
        draw_text(cv, tx, ly, ln, INK, 3)
        ly += 27
    ly += 6
    for ln in wrap(body, 2, tw):
        draw_text(cv, tx, ly, ln, INK, 2)
        ly += 20


def build_image():
    cv = Canvas(WIDTH, HEIGHT, PAPER)
    # masthead
    cv.rect(0, 0, WIDTH, 10, RED)
    draw_text_centred(cv, WIDTH // 2, 30, "THE WORLD IN ONE DAY", INK, 6)
    cv.rect(88, 88, WIDTH - 176, 3, INK)
    draw_text_centred(cv, WIDTH // 2, 102, "TUESDAY 17 NOVEMBER 2026",
                      RED, 4)
    cv.rect(88, 140, WIDTH - 176, 3, INK)

    stories = [
        ("EUROPE - WAR", "UKRAINE STRIKES CRIMEA BRIDGE",
         "The Kerch Bridge partly collapses in an unprecedented "
         "attack; a second day of strikes as Russia hits Kyiv bridges.",
         icon_bridge),
        ("RUSSIA", "MILITARY PLANE CRASH KILLS 19",
         "An An-12 transport comes down in the Kemerovo region; "
         "officials blame a technical fault.", icon_plane_down),
        ("DIPLOMACY", "TRUMP IN ASIA FOR SUMMIT TALKS",
         "The US president stops in Manila ahead of meetings with "
         "Xi Jinping and Vladimir Putin in Shenzhen.", icon_globe),
        ("HEALTH", "US LOSES MEASLES-FREE STATUS",
         "After 26 years: 5,400+ cases and 10 deaths, a 40-year "
         "high as vaccination rates fall.", icon_syringe),
        ("FRANCE", "146,000 MARCH IN NATIONWIDE STRIKE",
         "Unions shut schools and transport in a second day of "
         "protest over pay and living costs.", icon_crowd),
        ("BUSINESS - TECH", "NVIDIA POSTS BUMPER RESULTS",
         "The AI chip giant beats forecasts as a leadership shock "
         "and the China chip row swirl around it.", icon_chip),
    ]
    pw, ph, gap, mx, top = 474, 238, 20, 28, 168
    for i, (kicker, head, body, icon) in enumerate(stories):
        px = mx + (i % 2) * (pw + gap)
        py = top + (i // 2) * (ph + gap)
        panel(cv, px, py, pw, ph, kicker, head, body, icon)

    fy = top + 3 * ph + 2 * gap + 14
    cv.rect(88, fy, WIDTH - 176, 3, INK)
    draw_text_centred(cv, WIDTH // 2, fy + 12,
                      "ALSO: WESTERN POWERS URGE GAZA AID CROSSINGS OPEN",
                      INK, 2)
    draw_text_centred(cv, WIDTH // 2, fy + 36,
                      "JAPAN JETS SCRAMBLE - MOLDOVA SHUTS AIRSPACE",
                      INK, 2)
    return encode_png(WIDTH, HEIGHT, cv.buf)


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    data = build_image()
    with open(os.path.join(out_dir, "entry.png"), "wb") as fh:
        fh.write(data)
    print("wrote entry.png:", len(data), "bytes")


if __name__ == "__main__":
    main()
