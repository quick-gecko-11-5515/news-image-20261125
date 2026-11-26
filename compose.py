#!/usr/bin/env python3
"""Deterministic front-page composer for The World Today — Wednesday 25 November 2026.

Builds a 1024x1024 editorial broadsheet front page (`entry.png`) combining
generated editorial photography with Noto Sans typography, smooth vertical
gradient scrims, automated overlap/clipping validation, and deterministic
PNG output under 1 MiB.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from PIL import Image, ImageDraw, ImageFont

BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"
OUTPUT_PATH = BASE_DIR / "entry.png"

CANVAS_DIM = 1024
MAX_BYTES = 1_048_576

NOTO_DIR = Path("/usr/share/fonts/truetype/noto")
FONT_FILES = {
    "black": NOTO_DIR / "NotoSans-Black.ttf",
    "extrabold": NOTO_DIR / "NotoSans-ExtraBold.ttf",
    "bold": NOTO_DIR / "NotoSans-Bold.ttf",
    "semibold": NOTO_DIR / "NotoSans-SemiBold.ttf",
    "medium": NOTO_DIR / "NotoSans-Medium.ttf",
    "regular": NOTO_DIR / "NotoSans-Regular.ttf",
    "cond_extrabold": NOTO_DIR / "NotoSans-CondensedExtraBold.ttf",
    "cond_bold": NOTO_DIR / "NotoSans-CondensedBold.ttf",
}

COLORS = {
    "bg": (11, 15, 22),
    "card": (18, 24, 34),
    "border": (42, 52, 68),
    "gold": (224, 184, 64),
    "masthead": (246, 248, 252),
    "white": (255, 255, 255),
    "date": (234, 240, 248),
    "body": (222, 230, 240),
    "brief": (242, 246, 252),
    "rule": (74, 86, 104),
    "footer": (176, 188, 204),
    "scrim": (7, 10, 16),
}

# Verified 25 November 2026 world news content
DATE_LINE = "WEDNESDAY 25 NOVEMBER 2026"

HERO_ASSET = "hero-space.jpg"
HERO_KICKER = "SPACE · TIANGONG"
HERO_HEADLINE = "CHINA LAUNCHES SHENZHOU-24"
HERO_SUBLINE = (
    "China launched Shenzhou-24 to the Tiangong space station with three "
    "astronauts, including the first Pakistani astronaut — the first foreign "
    "astronaut in China's space programme."
)

LEFT_PANEL = {
    "asset": "panel-chess.jpg",
    "kicker": "GENEVA · WORLD CHESS CHAMPIONSHIP",
    "headline": "GAME 2: 20-MOVE DRAW — MATCH TIED 1–1",
    "text": (
        "Champion Gukesh (White) and challenger Sindarov drew Game 2 in just "
        "20 moves by threefold repetition; Gukesh surprised with the London "
        "System (3.Bf4). Score 1–1; Game 3 is Thursday with Sindarov White."
    ),
    "focus_x": 0.50,
    "focus_y": 0.96,
    "zoom": 1.00,
}

RIGHT_PANEL = {
    "asset": "panel-samara.jpg",
    "kicker": "SAMARA · OIL WAR",
    "headline": "UKRAINE STRIKES SAMARA REFINERIES",
    "text": (
        "Ukrainian drones hit two Rosneft refineries in the Samara region, "
        "about 800 km from the border; fires reported, one person killed and "
        "power cuts — a day after President Putin vowed retaliation for "
        "refinery strikes."
    ),
    "focus_x": 0.50,
    "focus_y": 0.54,
    "zoom": 1.00,
}

BRIEFS = [
    ("INDONESIA · DISASTER", "BOGOR GOLD MINE FLOOD: 9 DEAD, 17 STILL TRAPPED"),
    ("KYIV · WAR FUNDING", "ZELENSKY: UKRAINE NEEDS €115BN FOREIGN AID FOR 2027"),
]

FOOTER_TEXT = "NORTH KOREA EXPELS SWISS DIPLOMATS, ORDERS EMBASSY SHUT IN 48 HOURS"


@dataclass(frozen=True)
class Box:
    left: int
    top: int
    right: int
    bottom: int

    @property
    def width(self) -> int:
        return self.right - self.left

    @property
    def height(self) -> int:
        return self.bottom - self.top

    @property
    def coords(self) -> tuple[int, int, int, int]:
        return (self.left, self.top, self.right, self.bottom)


class LayoutChecker:
    """Renders text while validating bounds containment and zero overlaps."""

    def __init__(self) -> None:
        self.placed: list[tuple[str, tuple[int, int, int, int]]] = []
        self.errors: list[str] = []

    def draw_line(
        self,
        draw: ImageDraw.ImageDraw,
        label: str,
        x: int,
        y: int,
        text: str,
        font: ImageFont.FreeTypeFont,
        fill: tuple[int, int, int],
        bounds: Box,
        right_align: bool = False,
    ) -> tuple[int, int, int, int]:
        if right_align:
            probe = draw.textbbox((0, y), text, font=font)
            x = bounds.right - probe[2]
        bbox = draw.textbbox((x, y), text, font=font)
        if bbox[0] < bounds.left:
            x += bounds.left - bbox[0]
            bbox = draw.textbbox((x, y), text, font=font)

        clips = []
        if bbox[0] < bounds.left:
            clips.append(f"left({bbox[0]}<{bounds.left})")
        if bbox[1] < bounds.top:
            clips.append(f"top({bbox[1]}<{bounds.top})")
        if bbox[2] > bounds.right:
            clips.append(f"right({bbox[2]}>{bounds.right})")
        if bbox[3] > bounds.bottom:
            clips.append(f"bottom({bbox[3]}>{bounds.bottom})")
        if clips:
            self.errors.append(f"CLIP {label}: {', '.join(clips)} bbox={bbox}")

        for other_label, ob in self.placed:
            if bbox[0] < ob[2] and bbox[2] > ob[0] and bbox[1] < ob[3] and bbox[3] > ob[1]:
                self.errors.append(f"OVERLAP {label} with {other_label}: {bbox} vs {ob}")

        self.placed.append((label, bbox))
        draw.text((x, y), text, font=font, fill=fill)
        return bbox


def get_font(style: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_FILES[style]), size)


def crop_cover(
    photo: Image.Image,
    target_w: int,
    target_h: int,
    focus_x: float = 0.5,
    focus_y: float = 0.5,
    zoom: float = 1.0,
) -> Image.Image:
    src_w, src_h = photo.size
    scale = max(target_w / src_w, target_h / src_h) * zoom
    new_w = max(target_w, round(src_w * scale))
    new_h = max(target_h, round(src_h * scale))
    resized = photo.resize((new_w, new_h), Image.Resampling.LANCZOS)
    x0 = max(0, min(round((new_w - target_w) * focus_x), new_w - target_w))
    y0 = max(0, min(round((new_h - target_h) * focus_y), new_h - target_h))
    return resized.crop((x0, y0, x0 + target_w, y0 + target_h))


def make_vertical_scrim(
    width: int,
    height: int,
    fade_start: float,
    solid_start: float,
    max_alpha: int,
    rgb: tuple[int, int, int],
) -> Image.Image:
    col = Image.new("RGBA", (1, height), (rgb[0], rgb[1], rgb[2], 0))
    y_fade = round(height * fade_start)
    y_solid = round(height * solid_start)
    span = max(1, y_solid - y_fade)
    for y in range(height):
        if y < y_fade:
            alpha = 0
        elif y < y_solid:
            t = (y - y_fade) / span
            smooth = t * t * (3.0 - 2.0 * t)
            alpha = round(max_alpha * smooth)
        else:
            alpha = max_alpha
        col.putpixel((0, y), (rgb[0], rgb[1], rgb[2], alpha))
    return col.resize((width, height), Image.Resampling.NEAREST)


def greedy_wrap(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont,
    max_width: int,
) -> list[str]:
    words = text.split()
    lines: list[str] = []
    buf: list[str] = []
    for word in words:
        candidate = " ".join(buf + [word])
        if buf and draw.textbbox((0, 0), candidate, font=font)[2] > max_width:
            lines.append(" ".join(buf))
            buf = [word]
        else:
            buf.append(word)
    if buf:
        lines.append(" ".join(buf))
    return lines


def balanced_wrap(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont,
    max_width: int,
) -> list[str]:
    base = greedy_wrap(draw, text, font, max_width)
    line_count = len(base)
    if line_count <= 1:
        return base

    words = text.split()
    n = len(words)
    inf = 10**18
    dp = [[inf] * (n + 1) for _ in range(line_count + 1)]
    back = [[-1] * (n + 1) for _ in range(line_count + 1)]
    dp[0][0] = 0

    for k in range(1, line_count + 1):
        for end in range(k, n + 1):
            for start in range(k - 1, end):
                if dp[k - 1][start] == inf:
                    continue
                width = draw.textbbox((0, 0), " ".join(words[start:end]), font=font)[2]
                if width > max_width:
                    continue
                slack = max_width - width
                orphan = 450_000 if (k == line_count and end - start == 1) else 0
                cost = dp[k - 1][start] + slack * slack + orphan
                if cost < dp[k][end]:
                    dp[k][end] = cost
                    back[k][end] = start

    if dp[line_count][n] >= inf:
        return base

    out: list[str] = []
    pos = n
    for k in range(line_count, 0, -1):
        prev = back[k][pos]
        out.append(" ".join(words[prev:pos]))
        pos = prev
    out.reverse()
    return out


def paste_photo_panel(
    canvas: Image.Image,
    asset_name: str,
    box: Box,
    focus_x: float,
    focus_y: float,
    zoom: float,
    fade_start: float,
    solid_start: float,
    max_alpha: int,
) -> None:
    photo = Image.open(ASSETS_DIR / asset_name).convert("RGBA")
    fitted = crop_cover(photo, box.width, box.height, focus_x=focus_x, focus_y=focus_y, zoom=zoom)
    scrim = make_vertical_scrim(
        box.width,
        box.height,
        fade_start=fade_start,
        solid_start=solid_start,
        max_alpha=max_alpha,
        rgb=COLORS["scrim"],
    )
    composited = Image.alpha_composite(fitted, scrim)
    canvas.paste(composited, (box.left, box.top))


def draw_lines(
    draw: ImageDraw.ImageDraw,
    checker: LayoutChecker,
    prefix: str,
    x: int,
    y_start: int,
    step: int,
    lines: Sequence[str],
    font: ImageFont.FreeTypeFont,
    fill: tuple[int, int, int],
    bounds: Box,
) -> int:
    y = y_start
    for idx, line in enumerate(lines, start=1):
        checker.draw_line(draw, f"{prefix}.{idx}", x, y, line, font, fill, bounds)
        y += step
    return y


def render_front_page() -> list[str]:
    canvas = Image.new("RGBA", (CANVAS_DIM, CANVAS_DIM), COLORS["bg"] + (255,))
    checker = LayoutChecker()

    margin = 32
    gutter = 16
    full_w = CANVAS_DIM - 2 * margin  # 960
    col_w = (full_w - gutter) // 2  # 472

    hero_box = Box(margin, 122, margin + full_w, 532)  # 960x410
    left_box = Box(margin, 546, margin + col_w, 846)  # 472x300
    right_box = Box(margin + col_w + gutter, 546, margin + full_w, 846)  # 472x300

    paste_photo_panel(
        canvas,
        HERO_ASSET,
        hero_box,
        focus_x=0.50,
        focus_y=0.28,
        zoom=1.00,
        fade_start=0.61,
        solid_start=0.80,
        max_alpha=240,
    )
    paste_photo_panel(
        canvas,
        LEFT_PANEL["asset"],
        left_box,
        focus_x=LEFT_PANEL["focus_x"],
        focus_y=LEFT_PANEL["focus_y"],
        zoom=LEFT_PANEL["zoom"],
        fade_start=0.40,
        solid_start=0.55,
        max_alpha=248,
    )
    paste_photo_panel(
        canvas,
        RIGHT_PANEL["asset"],
        right_box,
        focus_x=RIGHT_PANEL["focus_x"],
        focus_y=RIGHT_PANEL["focus_y"],
        zoom=RIGHT_PANEL["zoom"],
        fade_start=0.40,
        solid_start=0.55,
        max_alpha=248,
    )

    draw = ImageDraw.Draw(canvas)

    # Panel framing borders
    for panel_box in (hero_box, left_box, right_box):
        draw.rectangle(
            [panel_box.left, panel_box.top, panel_box.right - 1, panel_box.bottom - 1],
            outline=COLORS["border"],
            width=1,
        )

    # Masthead
    masthead_box = Box(margin, 14, margin + full_w, 112)
    checker.draw_line(
        draw,
        "masthead.title",
        margin,
        16,
        "THE WORLD TODAY",
        get_font("black", 52),
        COLORS["masthead"],
        masthead_box,
    )
    checker.draw_line(
        draw,
        "masthead.tagline",
        margin,
        82,
        "THE DAY IN ONE PICTURE",
        get_font("bold", 17),
        COLORS["gold"],
        masthead_box,
    )
    checker.draw_line(
        draw,
        "masthead.date",
        margin,
        79,
        DATE_LINE,
        get_font("extrabold", 20),
        COLORS["date"],
        masthead_box,
        right_align=True,
    )
    draw.rectangle([margin, 110, margin + full_w, 113], fill=COLORS["gold"])

    # Hero text overlay (positioned low to reveal the rocket exhaust plume above)
    hero_text_box = Box(hero_box.left + 22, hero_box.top + 266, hero_box.right - 22, hero_box.bottom - 10)
    hero_kicker_font = get_font("bold", 16)
    hero_head_font = get_font("extrabold", 42)
    # Subtle drop shadow behind kicker & headline for crisp readability over rocket glow
    draw.text((hero_text_box.left + 1, hero_box.top + 273), HERO_KICKER, font=hero_kicker_font, fill=(6, 9, 14))
    checker.draw_line(
        draw,
        "hero.kicker",
        hero_text_box.left,
        hero_box.top + 272,
        HERO_KICKER,
        hero_kicker_font,
        COLORS["gold"],
        hero_text_box,
    )
    draw.text((hero_text_box.left + 2, hero_box.top + 297), HERO_HEADLINE, font=hero_head_font, fill=(6, 9, 14))
    checker.draw_line(
        draw,
        "hero.headline",
        hero_text_box.left,
        hero_box.top + 295,
        HERO_HEADLINE,
        hero_head_font,
        COLORS["white"],
        hero_text_box,
    )
    hero_sub_font = get_font("regular", 18)
    hero_sub_lines = balanced_wrap(draw, HERO_SUBLINE, hero_sub_font, hero_text_box.width)
    draw_lines(
        draw,
        checker,
        "hero.sub",
        hero_text_box.left,
        hero_box.top + 350,
        24,
        hero_sub_lines,
        hero_sub_font,
        COLORS["body"],
        hero_text_box,
    )

    # Secondary side panels
    panel_kicker_font = get_font("bold", 12)
    panel_head_font = get_font("cond_extrabold", 22)
    panel_body_font = get_font("regular", 14)

    for tag, box, spec in (("left", left_box, LEFT_PANEL), ("right", right_box, RIGHT_PANEL)):
        inner = Box(box.left + 16, box.top + 148, box.right - 16, box.bottom - 10)
        draw.text((inner.left + 1, box.top + 155), spec["kicker"], font=panel_kicker_font, fill=(6, 9, 14))
        checker.draw_line(
            draw,
            f"{tag}.kicker",
            inner.left,
            box.top + 154,
            spec["kicker"],
            panel_kicker_font,
            COLORS["gold"],
            inner,
        )
        head_lines = balanced_wrap(draw, spec["headline"], panel_head_font, inner.width)
        next_y = draw_lines(
            draw,
            checker,
            f"{tag}.headline",
            inner.left,
            box.top + 173,
            26,
            head_lines,
            panel_head_font,
            COLORS["white"],
            inner,
        )
        body_lines = balanced_wrap(draw, spec["text"], panel_body_font, inner.width)
        draw_lines(
            draw,
            checker,
            f"{tag}.body",
            inner.left,
            next_y + 5,
            20,
            body_lines,
            panel_body_font,
            COLORS["body"],
            inner,
        )

    # Briefs strip
    brief_top = 860
    brief_bottom = 958
    brief_kicker_font = get_font("bold", 12)
    brief_text_font = get_font("bold", 18)

    for idx, (kicker, line_text) in enumerate(BRIEFS):
        bx0 = margin + idx * (col_w + gutter)
        bx1 = bx0 + col_w
        card = Box(bx0, brief_top, bx1, brief_bottom)
        draw.rectangle(card.coords, fill=COLORS["card"], outline=COLORS["border"], width=1)
        draw.rectangle([bx0, brief_top, bx1, brief_top + 3], fill=COLORS["gold"])

        inner = Box(bx0 + 16, brief_top + 10, bx1 - 16, brief_bottom - 10)
        checker.draw_line(
            draw,
            f"brief{idx + 1}.kicker",
            inner.left,
            brief_top + 14,
            kicker,
            brief_kicker_font,
            COLORS["gold"],
            inner,
        )
        wrapped = balanced_wrap(draw, line_text, brief_text_font, inner.width)
        draw_lines(
            draw,
            checker,
            f"brief{idx + 1}.text",
            inner.left,
            brief_top + 36,
            24,
            wrapped,
            brief_text_font,
            COLORS["brief"],
            inner,
        )

    # Footer strip
    draw.rectangle([margin, 970, margin + full_w, 971], fill=COLORS["rule"])
    footer_box = Box(margin, 974, margin + full_w, 1012)
    checker.draw_line(
        draw,
        "footer.line",
        margin,
        983,
        FOOTER_TEXT,
        get_font("medium", 13),
        COLORS["footer"],
        footer_box,
    )

    # Deterministic PNG export under 1 MiB
    rgb = canvas.convert("RGB")
    rgb.save(OUTPUT_PATH, format="PNG", optimize=True)
    byte_size = OUTPUT_PATH.stat().st_size
    print(f"Rendered RGB PNG: {byte_size} bytes ({rgb.size[0]}x{rgb.size[1]})")
    if byte_size > MAX_BYTES:
        quantized = rgb.quantize(
            colors=256,
            method=Image.Quantize.MEDIANCUT,
            dither=Image.Dither.FLOYDSTEINBERG,
        )
        quantized.save(OUTPUT_PATH, format="PNG", optimize=True)
        byte_size = OUTPUT_PATH.stat().st_size
        print(f"Quantized PNG: {byte_size} bytes")

    return checker.errors


def main() -> int:
    errors = render_front_page()
    if errors:
        for err in errors:
            print(f"LAYOUT ERROR: {err}")
        return 1
    print("Layout validation passed (0 issues).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
