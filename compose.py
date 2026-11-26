#!/usr/bin/env python3
"""Render 'The World Today' (25 November 2026) 1024x1024 front-page graphic."""

from __future__ import annotations

import io
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from PIL import Image, ImageDraw, ImageFont

CANVAS_SIZE = (1024, 1024)
MAX_BYTES = 1_048_576

FONT_DIR = Path("/usr/share/fonts/truetype/dejavu")
FONT_BOLD = FONT_DIR / "DejaVuSans-Bold.ttf"
FONT_REGULAR = FONT_DIR / "DejaVuSans.ttf"


@dataclass(frozen=True)
class Palette:
    page_bg: tuple[int, int, int] = (10, 15, 24)
    card_bg: tuple[int, int, int] = (16, 23, 36)
    card_border: tuple[int, int, int] = (38, 49, 68)
    rule_subtle: tuple[int, int, int] = (46, 58, 78)
    gold: tuple[int, int, int] = (218, 173, 62)
    white: tuple[int, int, int] = (248, 250, 252)
    body_text: tuple[int, int, int] = (218, 226, 237)
    footer_text: tuple[int, int, int] = (176, 189, 208)
    scrim_rgb: tuple[int, int, int] = (8, 12, 20)
    shadow_rgb: tuple[int, int, int] = (4, 7, 12)


@dataclass(frozen=True)
class Box:
    x: int
    y: int
    w: int
    h: int

    @property
    def x2(self) -> int:
        return self.x + self.w

    @property
    def y2(self) -> int:
        return self.y + self.h


@dataclass(frozen=True)
class FeatureStory:
    photo: str
    focal_y: float
    kicker: str
    headline: str
    body: str


@dataclass(frozen=True)
class BriefStory:
    kicker: str
    lines: tuple[str, str]


COLORS = Palette()

DATE_LINE = "WEDNESDAY 25 NOVEMBER 2026"
MASTHEAD_TITLE = "THE WORLD TODAY"
MASTHEAD_SUBTITLE = "THE DAY IN ONE PICTURE"

HERO_PHOTO = "hero-space.jpg"
HERO_KICKER = "SPACE · TIANGONG"
HERO_HEADLINE = "CHINA LAUNCHES SHENZHOU-24"
HERO_SUBLINE = (
    "China launched Shenzhou-24 to the Tiangong space station with three astronauts, "
    "including the first Pakistani astronaut — the first foreign astronaut in China's space programme."
)

PANELS: tuple[FeatureStory, FeatureStory] = (
    FeatureStory(
        photo="panel-chess.jpg",
        focal_y=0.52,
        kicker="GENEVA · WORLD CHESS CHAMPIONSHIP",
        headline="GAME 2: 20-MOVE DRAW — MATCH TIED 1–1",
        body=(
            "Champion Gukesh (White) and challenger Sindarov drew Game 2 in just 20 moves "
            "by threefold repetition; Gukesh surprised with the London System (3.Bf4). "
            "Score 1–1; Game 3 is Thursday with Sindarov White."
        ),
    ),
    FeatureStory(
        photo="panel-samara.jpg",
        focal_y=0.45,
        kicker="SAMARA · OIL WAR",
        headline="UKRAINE STRIKES SAMARA REFINERIES",
        body=(
            "Ukrainian drones hit two Rosneft refineries in the Samara region, about 800 km "
            "from the border; fires reported, one person killed and power cuts — a day after "
            "President Putin vowed retaliation for refinery strikes."
        ),
    ),
)

BRIEFS: tuple[BriefStory, BriefStory] = (
    BriefStory(
        kicker="INDONESIA · DISASTER",
        lines=("BOGOR GOLD MINE FLOOD:", "9 DEAD, 17 STILL TRAPPED"),
    ),
    BriefStory(
        kicker="KYIV · WAR FUNDING",
        lines=("ZELENSKY: UKRAINE NEEDS", "€115BN FOREIGN AID FOR 2027"),
    ),
)

FOOTER_TEXT = "NORTH KOREA EXPELS SWISS DIPLOMATS, ORDERS EMBASSY SHUT IN 48 HOURS"


def load_font(path: Path, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(path), size=size)


def fit_single_line_font(
    draw: ImageDraw.ImageDraw,
    text: str,
    font_path: Path,
    max_width: int,
    max_size: int,
    min_size: int = 12,
) -> ImageFont.FreeTypeFont:
    for size in range(max_size, min_size - 1, -1):
        font = load_font(font_path, size)
        if draw.textlength(text, font=font) <= max_width:
            return font
    return load_font(font_path, min_size)


def wrap_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont,
    max_width: int,
) -> list[str]:
    words = text.split()
    if not words:
        return []
    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        candidate = f"{current} {word}"
        if draw.textlength(candidate, font=font) <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def load_cover_photo(
    path: Path,
    target_w: int,
    target_h: int,
    focal_y: float = 0.5,
    jpeg_quality: int | None = None,
) -> Image.Image:
    with Image.open(path) as raw:
        img = raw.convert("RGB")
    src_w, src_h = img.size
    scale = max(target_w / src_w, target_h / src_h)
    resized_w = max(target_w, round(src_w * scale))
    resized_h = max(target_h, round(src_h * scale))
    img = img.resize((resized_w, resized_h), Image.Resampling.LANCZOS)

    left = (resized_w - target_w) // 2
    max_top = resized_h - target_h
    top = max(0, min(max_top, round(max_top * focal_y)))
    cropped = img.crop((left, top, left + target_w, top + target_h))

    if jpeg_quality is not None:
        buf = io.BytesIO()
        cropped.save(buf, format="JPEG", quality=jpeg_quality, subsampling=2)
        buf.seek(0)
        with Image.open(buf) as recompressed:
            cropped = recompressed.convert("RGB")
    return cropped


def vertical_gradient(
    width: int,
    height: int,
    rgb: tuple[int, int, int],
    max_alpha: int,
    power: float = 1.5,
) -> Image.Image:
    strip = Image.new("RGBA", (1, height))
    pixels = []
    denom = max(1, height - 1)
    for row in range(height):
        t = (row / denom) ** power
        alpha = min(255, max(0, round(max_alpha * t)))
        pixels.append((*rgb, alpha))
    strip.putdata(pixels)
    return strip.resize((width, height), Image.Resampling.NEAREST)


def fit_shared_font(
    draw: ImageDraw.ImageDraw,
    texts: Sequence[str],
    font_path: Path,
    max_width: int,
    max_size: int,
    min_size: int = 12,
) -> ImageFont.FreeTypeFont:
    for size in range(max_size, min_size - 1, -1):
        font = load_font(font_path, size)
        if all(draw.textlength(t, font=font) <= max_width for t in texts):
            return font
    return load_font(font_path, min_size)


def draw_masthead(draw: ImageDraw.ImageDraw, margin_x: int, content_w: int) -> None:
    title_font = load_font(FONT_BOLD, 46)
    sub_font = load_font(FONT_BOLD, 15)
    date_font = load_font(FONT_BOLD, 16)

    draw.text((margin_x, 16), MASTHEAD_TITLE, font=title_font, fill=COLORS.white)

    rule_y = 70
    draw.rectangle((margin_x, rule_y, margin_x + content_w, rule_y + 2), fill=COLORS.gold)

    sub_y = 79
    draw.text((margin_x, sub_y), MASTHEAD_SUBTITLE, font=sub_font, fill=COLORS.gold)

    date_w = draw.textlength(DATE_LINE, font=date_font)
    draw.text(
        (margin_x + content_w - date_w, sub_y - 1),
        DATE_LINE,
        font=date_font,
        fill=COLORS.white,
    )

    draw.line(
        ((margin_x, 105), (margin_x + content_w, 105)),
        fill=COLORS.rule_subtle,
        width=1,
    )


def draw_hero(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    box: Box,
    assets_dir: Path,
    photo_quality: int | None,
) -> None:
    photo = load_cover_photo(
        assets_dir / HERO_PHOTO,
        box.w,
        box.h,
        focal_y=0.06,
        jpeg_quality=photo_quality,
    )
    canvas.paste(photo, (box.x, box.y))

    scrim_h = 250
    scrim = vertical_gradient(box.w, scrim_h, COLORS.scrim_rgb, max_alpha=248, power=1.25)
    canvas.paste(scrim, (box.x, box.y2 - scrim_h), scrim)

    pad_x = 22
    text_w = box.w - 2 * pad_x

    kicker_font = load_font(FONT_BOLD, 14)
    headline_font = fit_single_line_font(draw, HERO_HEADLINE, FONT_BOLD, text_w, 44, 28)
    sub_font = load_font(FONT_REGULAR, 17)
    sub_lines = wrap_text(draw, HERO_SUBLINE, sub_font, text_w)

    sub_line_h = 23
    sub_total_h = len(sub_lines) * sub_line_h
    sub_top = box.y2 - 18 - sub_total_h
    headline_top = sub_top - 56
    kicker_top = headline_top - 22

    # Subtle shadow for crisp legibility over the rocket exhaust plume
    draw.text(
        (box.x + pad_x + 1, kicker_top + 1),
        HERO_KICKER,
        font=kicker_font,
        fill=COLORS.shadow_rgb,
    )
    draw.text((box.x + pad_x, kicker_top), HERO_KICKER, font=kicker_font, fill=COLORS.gold)

    draw.text(
        (box.x + pad_x + 2, headline_top + 2),
        HERO_HEADLINE,
        font=headline_font,
        fill=COLORS.shadow_rgb,
    )
    draw.text((box.x + pad_x, headline_top), HERO_HEADLINE, font=headline_font, fill=COLORS.white)

    for idx, line in enumerate(sub_lines):
        draw.text(
            (box.x + pad_x, sub_top + idx * sub_line_h),
            line,
            font=sub_font,
            fill=COLORS.body_text,
        )

    draw.rectangle(
        (box.x, box.y, box.x2 - 1, box.y2 - 1),
        outline=COLORS.card_border,
        width=1,
    )


def draw_feature_panel(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    box: Box,
    story: FeatureStory,
    headline_font: ImageFont.FreeTypeFont,
    assets_dir: Path,
    photo_quality: int | None,
) -> None:
    draw.rectangle((box.x, box.y, box.x2 - 1, box.y2 - 1), fill=COLORS.card_bg)

    photo_h = 160
    photo = load_cover_photo(
        assets_dir / story.photo,
        box.w,
        photo_h,
        focal_y=story.focal_y,
        jpeg_quality=photo_quality,
    )
    canvas.paste(photo, (box.x, box.y))

    fade_h = 46
    fade = vertical_gradient(box.w, fade_h, COLORS.card_bg, max_alpha=255, power=1.65)
    canvas.paste(fade, (box.x, box.y + photo_h - fade_h), fade)

    pad_x = 15
    text_w = box.w - 2 * pad_x

    kicker_font = load_font(FONT_BOLD, 12)
    body_font = load_font(FONT_REGULAR, 14)

    kicker_y = box.y + photo_h + 4
    headline_y = kicker_y + 19
    body_y = headline_y + 26

    draw.text((box.x + pad_x, kicker_y), story.kicker, font=kicker_font, fill=COLORS.gold)
    draw.text((box.x + pad_x, headline_y), story.headline, font=headline_font, fill=COLORS.white)

    body_lines = wrap_text(draw, story.body, body_font, text_w)
    line_h = 20
    for idx, line in enumerate(body_lines):
        draw.text(
            (box.x + pad_x, body_y + idx * line_h),
            line,
            font=body_font,
            fill=COLORS.body_text,
        )

    draw.rectangle(
        (box.x, box.y, box.x2 - 1, box.y2 - 1),
        outline=COLORS.card_border,
        width=1,
    )


def draw_brief(
    draw: ImageDraw.ImageDraw,
    box: Box,
    brief: BriefStory,
    headline_font: ImageFont.FreeTypeFont,
) -> None:
    draw.rectangle((box.x, box.y, box.x2 - 1, box.y2 - 1), fill=COLORS.card_bg)
    draw.rectangle((box.x, box.y, box.x2 - 1, box.y2 - 1), outline=COLORS.card_border, width=1)
    draw.rectangle((box.x, box.y, box.x2 - 1, box.y + 3), fill=COLORS.gold)

    pad_x = 15
    kicker_font = load_font(FONT_BOLD, 12)

    draw.text((box.x + pad_x, box.y + 17), brief.kicker, font=kicker_font, fill=COLORS.gold)

    line_h = 24
    start_y = box.y + 39
    for idx, line in enumerate(brief.lines):
        draw.text(
            (box.x + pad_x, start_y + idx * line_h),
            line,
            font=headline_font,
            fill=COLORS.white,
        )


def draw_footer(draw: ImageDraw.ImageDraw, margin_x: int, content_w: int) -> None:
    draw.line(
        ((margin_x, 976), (margin_x + content_w, 976)),
        fill=COLORS.rule_subtle,
        width=1,
    )
    footer_font = load_font(FONT_REGULAR, 13)
    draw.text((margin_x, 987), FOOTER_TEXT, font=footer_font, fill=COLORS.footer_text)


def render_page(assets_dir: Path, photo_quality: int | None = None) -> Image.Image:
    canvas = Image.new("RGB", CANVAS_SIZE, COLORS.page_bg)
    draw = ImageDraw.Draw(canvas)

    margin_x = 32
    content_w = CANVAS_SIZE[0] - 2 * margin_x
    gutter = 18
    col_w = (content_w - gutter) // 2

    draw_masthead(draw, margin_x, content_w)

    hero_box = Box(margin_x, 114, content_w, 410)
    draw_hero(canvas, draw, hero_box, assets_dir, photo_quality)

    panel_y = 538
    panel_h = 304
    panel_boxes: Sequence[Box] = (
        Box(margin_x, panel_y, col_w, panel_h),
        Box(margin_x + col_w + gutter, panel_y, col_w, panel_h),
    )
    panel_headline_font = fit_shared_font(
        draw,
        [story.headline for story in PANELS],
        FONT_BOLD,
        col_w - 30,
        19,
        14,
    )
    for box, story in zip(panel_boxes, PANELS):
        draw_feature_panel(canvas, draw, box, story, panel_headline_font, assets_dir, photo_quality)

    brief_y = 856
    brief_h = 108
    brief_boxes: Sequence[Box] = (
        Box(margin_x, brief_y, col_w, brief_h),
        Box(margin_x + col_w + gutter, brief_y, col_w, brief_h),
    )
    all_brief_lines = [line for brief in BRIEFS for line in brief.lines]
    brief_headline_font = fit_shared_font(
        draw,
        all_brief_lines,
        FONT_BOLD,
        col_w - 30,
        18,
        13,
    )
    for box, brief in zip(brief_boxes, BRIEFS):
        draw_brief(draw, box, brief, brief_headline_font)

    draw_footer(draw, margin_x, content_w)
    return canvas


def encode_png(image: Image.Image) -> bytes:
    buf = io.BytesIO()
    image.save(buf, format="PNG", optimize=True, compress_level=9)
    return buf.getvalue()


def main() -> None:
    root = Path(__file__).resolve().parent
    assets_dir = root / "assets"
    output_path = root / "entry.png"

    quality_steps: Sequence[int | None] = (None, 88, 80, 72)
    png_bytes = b""
    chosen_quality: int | None = None

    for quality in quality_steps:
        page = render_page(assets_dir, photo_quality=quality)
        candidate = encode_png(page)
        png_bytes = candidate
        chosen_quality = quality
        if len(candidate) <= MAX_BYTES:
            break

    output_path.write_bytes(png_bytes)
    print(
        f"Wrote {output_path} ({len(png_bytes):,} bytes, "
        f"size={CANVAS_SIZE[0]}x{CANVAS_SIZE[1]}, photo_quality={chosen_quality})"
    )


if __name__ == "__main__":
    main()
