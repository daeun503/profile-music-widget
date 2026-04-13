import base64
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

from colorthief import ColorThief


@dataclass(frozen=True)
class RenderContext:
    channel_name: str
    title: str
    url: str
    thumb_data: str
    bg_data: str
    time_left: str
    time_right: str
    color_1: str
    color_2: str
    card_rx: str
    card_border_rx: str
    thumb_rx: str
    thumb_inner_rx: str
    track_dur_s: str


@dataclass(frozen=True)
class MarqueeParams:
    title_x2: int
    marquee_dx: int
    marquee_dur: float


def to_hex(rgb: tuple[int, int, int]) -> str:
    return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"


def cal_dist(a: tuple[int, int, int], b: tuple[int, int, int]) -> int:
    return (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2


def _to_linear_channel(v: int) -> float:
    c = v / 255.0
    if c <= 0.03928:
        return c / 12.92
    return ((c + 0.055) / 1.055) ** 2.4


def rel_luminance(rgb: tuple[int, int, int]) -> float:
    r, g, b = rgb
    return (
        0.2126 * _to_linear_channel(r)
        + 0.7152 * _to_linear_channel(g)
        + 0.0722 * _to_linear_channel(b)
    )


def contrast_ratio(a: tuple[int, int, int], b: tuple[int, int, int]) -> float:
    l1 = rel_luminance(a)
    l2 = rel_luminance(b)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def darken_to_meet_contrast(
    bg: tuple[int, int, int],
    fg: tuple[int, int, int] = (255, 255, 255),
    min_ratio: float = 4.5,
) -> tuple[int, int, int]:
    if contrast_ratio(bg, fg) >= min_ratio:
        return bg

    lo = 0.0
    hi = 1.0
    for _ in range(20):
        mid = (lo + hi) / 2
        candidate = (
            int(round(bg[0] * (1 - mid))),
            int(round(bg[1] * (1 - mid))),
            int(round(bg[2] * (1 - mid))),
        )
        if contrast_ratio(candidate, fg) >= min_ratio:
            hi = mid
        else:
            lo = mid

    return (
        int(round(bg[0] * (1 - hi))),
        int(round(bg[1] * (1 - hi))),
        int(round(bg[2] * (1 - hi))),
    )


class SvgRenderer:
    def _layout_for_template(self, template_name: str) -> tuple[int, int, int]:
        return 372, 160, 21

    def _channel_max_width(self, template_name: str) -> tuple[int, int]:
        if template_name == "yt_phone.svg":
            return 324, 15
        return 372, 12

    def render(self, template_path: Path, ctx: RenderContext) -> str:
        svg = template_path.read_text(encoding="utf-8")
        template_name = template_path.name
        clip_width, title_x, title_font_size = self._layout_for_template(template_name)
        channel_max_width, channel_font_size = self._channel_max_width(template_name)
        channel_name = self._truncate_with_ellipsis(
            text=ctx.channel_name,
            max_width=channel_max_width,
            font_size=channel_font_size,
        )

        est_width = self._estimate_text_width_px(ctx.title, title_font_size)
        use_flow = est_width > clip_width
        if use_flow:
            mp = self._compute_marquee_params(
                ctx.title,
                font_size=title_font_size,
                clip_width=clip_width,
                title_x=title_x,
            )

            svg = svg.replace("{{TITLE_X2}}", str(mp.title_x2))
            svg = svg.replace("{{MARQUEE_DX}}", str(mp.marquee_dx))
            svg = svg.replace("{{MARQUEE_DUR}}", f"{mp.marquee_dur:.2f}")

            svg = self._remove_block(
                svg, "DONT REMOVE: TITLE_STATIC_START", "DONT REMOVE: TITLE_STATIC_END"
            )
        else:
            svg = self._remove_block(
                svg, "DONT REMOVE: TITLE_FLOW_START", "DONT REMOVE: TITLE_FLOW_END"
            )

        svg = svg.replace("{{TITLE}}", escape(ctx.title))
        svg = svg.replace("{{URL}}", escape(ctx.url))
        svg = svg.replace("{{THUMB_URL}}", escape(ctx.thumb_data))
        svg = svg.replace("{{BG_URL}}", escape(ctx.bg_data))
        svg = svg.replace("{{TIME_LEFT}}", escape(ctx.time_left))
        svg = svg.replace("{{TIME_RIGHT}}", escape(ctx.time_right))
        svg = svg.replace("{{CHANNEL_NAME}}", escape(channel_name))
        svg = svg.replace("{{COLOR_1}}", escape(ctx.color_1))
        svg = svg.replace("{{COLOR_2}}", escape(ctx.color_2))
        svg = svg.replace("{{CARD_RX}}", escape(ctx.card_rx))
        svg = svg.replace("{{CARD_BORDER_RX}}", escape(ctx.card_border_rx))
        svg = svg.replace("{{THUMB_RX}}", escape(ctx.thumb_rx))
        svg = svg.replace("{{THUMB_INNER_RX}}", escape(ctx.thumb_inner_rx))
        svg = svg.replace("{{TITLE_FONT_SIZE}}", str(title_font_size))
        svg = svg.replace("{{TRACK_DUR}}", escape(ctx.track_dur_s))

        return svg

    def _compute_marquee_params(
        self,
        title: str,
        font_size: int,
        clip_width: int,
        title_x: int,
    ) -> MarqueeParams:
        est_width = self._estimate_text_width_px(title, font_size)

        gap = max(est_width + 70, int(clip_width * 1.35))
        title_x2 = title_x + gap
        dur = max(min(gap / 55.0, 28.0), 10.0)

        return MarqueeParams(
            title_x2=title_x2,
            marquee_dx=gap,
            marquee_dur=dur,
        )

    @staticmethod
    def _remove_block(svg: str, start: str, end: str) -> str:
        s = f"<!-- {start} -->"
        e = f"<!-- {end} -->"
        if s in svg and e in svg:
            return svg[: svg.index(s)] + svg[svg.index(e) + len(e) :]
        return svg

    @staticmethod
    def _estimate_text_width_px(text: str, font_size: int = 18) -> int:
        w = 0.0
        for ch in text:
            code = ord(ch)

            if ch.isspace():
                w += 0.33
            elif code >= 0x1100:
                w += 1.0
            elif ch.isupper():
                w += 0.72
            elif ch.islower() or ch.isdigit():
                w += 0.62
            else:
                w += 0.7

        return int(w * font_size)

    def _truncate_with_ellipsis(self, text: str, max_width: int, font_size: int) -> str:
        if self._estimate_text_width_px(text, font_size) <= max_width:
            return text

        ellipsis = "..."
        if self._estimate_text_width_px(ellipsis, font_size) > max_width:
            return ""

        lo = 0
        hi = len(text)
        while lo < hi:
            mid = (lo + hi + 1) // 2
            candidate = text[:mid].rstrip() + ellipsis
            if self._estimate_text_width_px(candidate, font_size) <= max_width:
                lo = mid
            else:
                hi = mid - 1
        return text[:lo].rstrip() + ellipsis

    @staticmethod
    def extract_color_from_img(thumb_data: str) -> tuple[str, str]:
        try:
            if thumb_data.startswith("data:"):
                _, b64 = thumb_data.split(",", 1)
            else:
                b64 = thumb_data
            ct = ColorThief(BytesIO(base64.b64decode(b64)))

            palette = ct.get_palette(color_count=6, quality=5)
            c1 = palette[0]
            c2 = next((c for c in palette[1:] if cal_dist(c1, c) >= 28**2), palette[0])
            c1 = darken_to_meet_contrast(c1)
            c2 = darken_to_meet_contrast(c2)
            return to_hex(c1), to_hex(c2)

        except Exception:
            return "#000000", "#000000"
