#!/usr/bin/env python3
"""Front-page composer for The World Today — Wednesday 25 November 2026.

Builds a deterministic 1024x1024 PNG front page (`entry.png`) from editorial
photography in `assets/` using Pillow, with balanced text wrapping, vertical
gradient scrims, layout collision/clipping checks, and < 1 MiB PNG output.
"""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Sequence

from PIL import Image, ImageDraw, ImageFont

BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"
OUTPUT_PATH = BASE_DIR / "entry.png"

CANVAS_W = 1024
CANVAS_H = 1024
MAX_BYTES = 1_048_576

NOTO_DIR = Path("/usr/share/fonts/truetype/noto")
FONT_FILES = {
    "black": NOTO_DIR / "NotoSans-Black.ttf",
    "extrabold": NOTO_DIR / "NotoSans-ExtraBold.ttf",
    "bold": NOTO_DIR / "NotoSans-Bold.ttf",
    "semibold": NOTO_DIR / "NotoSans-SemiBold.ttf",
    "medium": NOTO_DIR / "NotoSans-Medium.ttf",
    "regular": NOTO_DIR / "NotoSans-Regular.ttf",
}

COLORS = {
    "bg": (11, 15, 22),
    "panel_bg": (18, 24, 34),
    "border": (40, 50, 66),
    "gold": (222, 182, 62),
    "masthead": (246, 248, 252),
    "headline": (255, 255, 255),
    "date": (234, 240, 248),
    "body": (224, 231, 240),
    "brief": (242, 246, 252),
    "rule": (74, 86, 104),
    "footer": (176, 188, 204),
    "scrim": (7, 10, 16),
}

# Verified news content — Wednesday 25 November 2026
DATE_LINE = "WEDNESDAY 25 NOVEMBER 2026"
MASTHEAD_TITLE = "THE WORLD TODAY"
MASTHEAD_TAGLINE = "THE DAY IN ONE PICTURE"

HERO = {
    "asset": "hero-samara.jpg",
    "kicker": "SAMARA · OIL WAR",
    "headline": "UKRAINE STRIKES SAMARA REFINERIES",
    "subline": (
        "Ukrainian drones hit two Rosneft refineries in the Samara region, about "
        "800 km from the border; fires reported, one person killed and power cuts "
        "— a day after President Putin vowed retaliation for refinery strikes."
    ),
}

LEFT_PANEL = {
    "asset": "panel-chess.jpg",
    "kicker": "GENEVA · WORLD CHESS CHAMPIONSHIP",
    "headline": "GAME 2: 20-MOVE DRAW — MATCH TIED 1–1",
    "body": (
        "Champion Gukesh (White) and challenger Sindarov drew Game 2 in just 20 "
        "moves by threefold repetition; Gukesh surprised with the London System "
        "(3.Bf4). Score 1–1; Game 3 is Thursday with Sindarov White."
    ),
}

RIGHT_PANEL = {
    "asset": "panel-space.jpg",
    "kicker": "SPACE · TIANGONG",
    "headline": "CHINA LAUNCHES SHENZHOU-24 — FIRST FOREIGN ASTRONAUT ABOARD TIANGONG",
    "body": (
        "China launched Shenzhou-24 to the Tiangong space station with three "
        "astronauts, including the first Pakistani astronaut — the first foreign "
        "astronaut in China's space programme."
    ),
}

BRIEFS = [
    ("INDONESIA · DISASTER", "BOGOR GOLD MINE FLOOD: 9 DEAD, 17 STILL TRAPPED"),
    ("UKRAINE · FOREIGN AID", "ZELENSKY: UKRAINE NEEDS €115BN FOREIGN AID FOR 2027"),
]

FOOTER_TEXT = "NORTH KOREA EXPELS SWISS DIPLOMATS, ORDERS EMBASSY SHUT IN 48 HOURS"


@dataclass(frozen=True)
class Box:
    x0: int
    y0: int
    x1: int
    y1: int

    @property
    def w(self) -> int:
        return self.x1 - self.x0

    @property
    def h(self) -> int:
        return self.y1 - self.y0

    def coords(self) -> tuple[int, int, int, int]:
        return (self.x0, self.y0, self.x1, self.y1)


class PlacementChecker:
    """Draws text while asserting no clipping beyond bounds and no overlap."""

    def __init__(self) -> None:
        self.placed: list[tuple[str, tuple[int, int, int, int]]] = []
        self.errors: list[str] = []

    def text(
        self,
        draw: ImageDraw.ImageDraw,
        label: str,
        x: int,
        y: int,
        content: str,
        font: ImageFont.FreeTypeFont,
        fill: tuple[int, int, int],
        bounds: Box,
        right_align: bool = False,
    ) -> tuple[int, int, int, int]:
        if right_align:
            measured = draw.textbbox((0, y), content, font=font)
            x = bounds.x1 - measured[2]

        bbox = draw.textbbox((x, y), content, font=font)
        if bbox[0] < bounds.x0:
            x += bounds.x0 - bbox[0]
            bbox = draw.textbbox((x, y), content, font=font)

        clips = []
        if bbox[0] < bounds.x0:
            clips.append(f"left {bbox[0]} < {bounds.x0}")
        if bbox[1] < bounds.y0:
            clips.append(f"top {bbox[1]} < {bounds.y0}")
        if bbox[2] > bounds.x1:
            clips.append(f"right {bbox[2]} > {bounds.x1}")
        if bbox[3] > bounds.y1:
            clips.append(f"bottom {bbox[3]} > {bounds.y1}")
        if clips:
            self.errors.append(f"CLIP [{label}]: {', '.join(clips)} bbox={bbox}")

        for other_label, ob in self.placed:
            if bbox[0] < ob[2] and bbox[2] > ob[0] and bbox[1] < ob[3] and bbox[3] > ob[1]:
                self.errors.append(f"OVERLAP [{label}] vs [{other_label}]: {bbox} vs {ob}")

        self.placed.append((label, bbox))
        draw.text((x, y), content, font=font, fill=fill)
        return bbox


def font_of(weight: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_FILES[weight]), size)


def cover_crop(
    img: Image.Image,
    target_w: int,
    target_h: int,
    fx: float = 0.5,
    fy: float = 0.5,
    zoom: float = 1.0,
) -> Image.Image:
    """Scale and crop an image to cover target dimensions without distortion."""
    sw, sh = img.size
    scale = max(target_w / sw, target_h / sh) * zoom
    nw = max(target_w, round(sw * scale))
    nh = max(target_h, round(sh * scale))
    resized = img.resize((nw, nh), Image.Resampling.LANCZOS)
    ox = max(0, min(round((nw - target_w) * fx), nw - target_w))
    oy = max(0, min(round((nh - target_h) * fy), nh - target_h))
    return resized.crop((ox, oy, ox + target_w, oy + target_h))


def make_scrim(
    width: int,
    height: int,
    fade_start: float,
    solid_start: float,
    max_alpha: int,
    rgb: tuple[int, int, int],
) -> Image.Image:
    """Smoothstep bottom gradient scrim for strong text contrast over photos."""
    col = Image.new("RGBA", (1, height), (*rgb, 0))
    y_fade = round(height * fade_start)
    y_solid = round(height * solid_start)
    span = max(1, y_solid - y_fade)
    for y in range(height):
        if y < y_fade:
            a = 0
        elif y < y_solid:
            t = (y - y_fade) / span
            a = round(max_alpha * (t * t * (3.0 - 2.0 * t)))
        else:
            a = max_alpha
        col.putpixel((0, y), (*rgb, a))
    return col.resize((width, height), Image.Resampling.NEAREST)


def greedy_wrap(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont,
    max_w: int,
) -> list[str]:
    words = text.split()
    lines: list[str] = []
    cur: list[str] = []
    for w in words:
        candidate = " ".join(cur + [w])
        if cur and draw.textbbox((0, 0), candidate, font=font)[2] > max_w:
            lines.append(" ".join(cur))
            cur = [w]
        else:
            cur.append(w)
    if cur:
        lines.append(" ".join(cur))
    return lines


def balanced_wrap(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont,
    max_w: int,
) -> list[str]:
    """Wrap into minimum lines while evening line lengths and avoiding orphans."""
    base = greedy_wrap(draw, text, font, max_w)
    k = len(base)
    if k <= 1:
        return base

    words = text.split()
    n = len(words)

    def width_of(i: int, j: int) -> int:
        return draw.textbbox((0, 0), " ".join(words[i:j]), font=font)[2]

    inf = 10**18
    dp = [[inf] * (n + 1) for _ in range(k + 1)]
    prev = [[-1] * (n + 1) for _ in range(k + 1)]
    dp[0][0] = 0

    for line_no in range(1, k + 1):
        for end in range(line_no, n + 1):
            for start in range(line_no - 1, end):
                if dp[line_no - 1][start] == inf:
                    continue
                w = width_of(start, end)
                if w > max_w:
                    continue
                slack = max_w - w
                orphan = 600_000 if (line_no == k and end - start == 1) else 0
                cost = dp[line_no - 1][start] + slack * slack + orphan
                if cost < dp[line_no][end]:
                    dp[line_no][end] = cost
                    prev[line_no][end] = start

    if dp[k][n] >= inf:
        return base

    out: list[str] = []
    pos = n
    for line_no in range(k, 0, -1):
        s = prev[line_no][pos]
        out.append(" ".join(words[s:pos]))
        pos = s
    out.reverse()
    return out


def paste_photo_panel(
    canvas: Image.Image,
    asset: str,
    box: Box,
    fy: float,
    fade_start: float,
    solid_start: float,
    max_alpha: int,
    zoom: float = 1.0,
    jpeg_quality: int | None = None,
) -> None:
    photo = Image.open(ASSETS_DIR / asset).convert("RGB")
    if jpeg_quality is not None:
        buf = BytesIO()
        photo.save(buf, format="JPEG", quality=jpeg_quality, optimize=True)
        buf.seek(0)
        photo = Image.open(buf).convert("RGB")
    cropped = cover_crop(photo.convert("RGBA"), box.w, box.h, fx=0.5, fy=fy, zoom=zoom)
    scrim = make_scrim(box.w, box.h, fade_start, solid_start, max_alpha, COLORS["scrim"])
    canvas.paste(Image.alpha_composite(cropped, scrim), (box.x0, box.y0))


def draw_lines(
    draw: ImageDraw.ImageDraw,
    checker: PlacementChecker,
    prefix: str,
    x: int,
    y: int,
    step: int,
    lines: Sequence[str],
    font: ImageFont.FreeTypeFont,
    fill: tuple[int, int, int],
    bounds: Box,
) -> int:
    cur_y = y
    for idx, line in enumerate(lines, start=1):
        checker.text(draw, f"{prefix}.{idx}", x, cur_y, line, font, fill, bounds)
        cur_y += step
    return cur_y


def render_page(jpeg_quality: int | None = None) -> tuple[Image.Image, list[str]]:
    canvas = Image.new("RGBA", (CANVAS_W, CANVAS_H), (*COLORS["bg"], 255))
    checker = PlacementChecker()

    margin = 32
    gutter = 16
    full_w = CANVAS_W - 2 * margin  # 960
    half_w = (full_w - gutter) // 2  # 472

    hero_box = Box(margin, 122, margin + full_w, 534)  # 960x412
    left_box = Box(margin, 548, margin + half_w, 840)  # 472x292
    right_box = Box(margin + half_w + gutter, 548, margin + full_w, 840)  # 472x292

    paste_photo_panel(
        canvas,
        HERO["asset"],
        hero_box,
        fy=0.22,
        fade_start=0.52,
        solid_start=0.71,
        max_alpha=240,
        zoom=1.0,
        jpeg_quality=jpeg_quality,
    )
    paste_photo_panel(
        canvas,
        LEFT_PANEL["asset"],
        left_box,
        fy=0.62,
        fade_start=0.45,
        solid_start=0.64,
        max_alpha=242,
        zoom=1.08,
        jpeg_quality=jpeg_quality,
    )
    paste_photo_panel(
        canvas,
        RIGHT_PANEL["asset"],
        right_box,
        fy=0.60,
        fade_start=0.40,
        solid_start=0.60,
        max_alpha=244,
        zoom=1.02,
        jpeg_quality=jpeg_quality,
    )

    draw = ImageDraw.Draw(canvas)

    # Panel borders
    for box in (hero_box, left_box, right_box):
        draw.rectangle(
            [box.x0, box.y0, box.x1 - 1, box.y1 - 1],
            outline=COLORS["border"],
            width=1,
        )

    # Masthead
    mast_box = Box(margin, 14, margin + full_w, 112)
    checker.text(
        draw,
        "masthead.title",
        margin,
        17,
        MASTHEAD_TITLE,
        font_of("black", 52),
        COLORS["masthead"],
        mast_box,
    )
    checker.text(
        draw,
        "masthead.tagline",
        margin,
        82,
        MASTHEAD_TAGLINE,
        font_of("bold", 17),
        COLORS["gold"],
        mast_box,
    )
    checker.text(
        draw,
        "masthead.date",
        margin,
        79,
        DATE_LINE,
        font_of("extrabold", 20),
        COLORS["date"],
        mast_box,
        right_align=True,
    )
    draw.rectangle([margin, 110, margin + full_w, 113], fill=COLORS["gold"])

    # Hero text block (bottom-anchored inside hero_box)
    hero_inner = Box(hero_box.x0 + 22, hero_box.y0 + 220, hero_box.x1 - 22, hero_box.y1 - 14)
    hero_kicker_f = font_of("bold", 16)
    hero_head_f = font_of("extrabold", 41)
    hero_sub_f = font_of("regular", 17)

    hero_head_lines = balanced_wrap(draw, HERO["headline"], hero_head_f, hero_inner.w)
    hero_sub_lines = balanced_wrap(draw, HERO["subline"], hero_sub_f, hero_inner.w)

    head_step = 48
    sub_step = 24
    block_h = 24 + len(hero_head_lines) * head_step + 6 + len(hero_sub_lines) * sub_step
    hero_y = hero_inner.y1 - block_h

    checker.text(
        draw,
        "hero.kicker",
        hero_inner.x0,
        hero_y,
        HERO["kicker"],
        hero_kicker_f,
        COLORS["gold"],
        hero_inner,
    )
    y_after_head = draw_lines(
        draw,
        checker,
        "hero.headline",
        hero_inner.x0,
        hero_y + 24,
        head_step,
        hero_head_lines,
        hero_head_f,
        COLORS["headline"],
        hero_inner,
    )
    draw_lines(
        draw,
        checker,
        "hero.sub",
        hero_inner.x0,
        y_after_head + 6,
        sub_step,
        hero_sub_lines,
        hero_sub_f,
        COLORS["body"],
        hero_inner,
    )

    # Side panels (bottom-anchored to handle 1- or 2-line headlines cleanly)
    panel_kicker_f = font_of("bold", 12)
    panel_head_f = font_of("extrabold", 18)
    panel_body_f = font_of("regular", 13)

    for tag, box, data in (
        ("left", left_box, LEFT_PANEL),
        ("right", right_box, RIGHT_PANEL),
    ):
        inner = Box(box.x0 + 16, box.y0 + 112, box.x1 - 16, box.y1 - 12)
        h_lines = balanced_wrap(draw, data["headline"], panel_head_f, inner.w)
        b_lines = balanced_wrap(draw, data["body"], panel_body_f, inner.w)
        h_step = 23
        b_step = 18
        total_h = 18 + len(h_lines) * h_step + 7 + len(b_lines) * b_step
        start_y = inner.y1 - total_h

        checker.text(
            draw,
            f"{tag}.kicker",
            inner.x0,
            start_y,
            data["kicker"],
            panel_kicker_f,
            COLORS["gold"],
            inner,
        )
        y_body = draw_lines(
            draw,
            checker,
            f"{tag}.headline",
            inner.x0,
            start_y + 18,
            h_step,
            h_lines,
            panel_head_f,
            COLORS["headline"],
            inner,
        )
        draw_lines(
            draw,
            checker,
            f"{tag}.body",
            inner.x0,
            y_body + 7,
            b_step,
            b_lines,
            panel_body_f,
            COLORS["body"],
            inner,
        )

    # Briefs strip
    brief_top = 854
    brief_bottom = 954
    brief_kicker_f = font_of("bold", 13)
    brief_text_f = font_of("bold", 18)

    for idx, (kicker, headline) in enumerate(BRIEFS):
        bx0 = margin + idx * (half_w + gutter)
        bx1 = bx0 + half_w
        card = Box(bx0, brief_top, bx1, brief_bottom)
        draw.rectangle(card.coords(), fill=COLORS["panel_bg"], outline=COLORS["border"], width=1)
        draw.rectangle([bx0, brief_top, bx1, brief_top + 3], fill=COLORS["gold"])

        inner = Box(bx0 + 16, brief_top + 10, bx1 - 16, brief_bottom - 10)
        checker.text(
            draw,
            f"brief{idx + 1}.kicker",
            inner.x0,
            brief_top + 13,
            kicker,
            brief_kicker_f,
            COLORS["gold"],
            inner,
        )
        wrapped = balanced_wrap(draw, headline, brief_text_f, inner.w)
        draw_lines(
            draw,
            checker,
            f"brief{idx + 1}.text",
            inner.x0,
            brief_top + 38,
            24,
            wrapped,
            brief_text_f,
            COLORS["brief"],
            inner,
        )

    # Footer line
    draw.rectangle([margin, 968, margin + full_w, 969], fill=COLORS["rule"])
    footer_box = Box(margin, 972, margin + full_w, 1012)
    checker.text(
        draw,
        "footer.line",
        margin,
        981,
        FOOTER_TEXT,
        font_of("medium", 13),
        COLORS["footer"],
        footer_box,
    )

    return canvas.convert("RGB"), checker.errors


def compose() -> list[str]:
    rgb, errors = render_page(jpeg_quality=None)
    rgb.save(OUTPUT_PATH, format="PNG", optimize=True)
    size = OUTPUT_PATH.stat().st_size
    print(f"Initial RGB PNG size: {size} bytes")

    if size > MAX_BYTES:
        for q in (82, 72, 62, 52):
            rgb, errors = render_page(jpeg_quality=q)
            rgb.save(OUTPUT_PATH, format="PNG", optimize=True)
            size = OUTPUT_PATH.stat().st_size
            print(f"Recompressed assets (JPEG q={q}) -> RGB PNG size: {size} bytes")
            if size <= MAX_BYTES:
                break

    if size > MAX_BYTES:
        quantized = rgb.quantize(
            colors=256,
            method=Image.Quantize.MEDIANCUT,
            dither=Image.Dither.FLOYDSTEINBERG,
        )
        quantized.save(OUTPUT_PATH, format="PNG", optimize=True)
        size = OUTPUT_PATH.stat().st_size
        print(f"Quantized 256-color PNG size: {size} bytes")

    return errors


def main() -> int:
    errors = compose()
    if errors:
        for err in errors:
            print(f"LAYOUT ERROR: {err}")
        return 1
    print("Layout check passed: 0 errors.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
