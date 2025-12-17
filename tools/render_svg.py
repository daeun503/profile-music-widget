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


@dataclass(frozen=True)
class MarqueeParams:
    title_x2: int
    marquee_dx: int
    marquee_dur: float


def to_hex(rgb: tuple[int, int, int]) -> str:
    return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"


def cal_dist(a: tuple[int, int, int], b: tuple[int, int, int]) -> int:
    return (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2


class SvgRenderer:
    TITLE_CLIP_WIDTH = 372

    def render(self, template_path: Path, ctx: RenderContext) -> str:
        svg = template_path.read_text(encoding="utf-8")

        est_width = self._estimate_text_width_px(ctx.title)
        use_flow = est_width > self.TITLE_CLIP_WIDTH
        if use_flow:
            mp = self._compute_marquee_params(ctx.title)

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
        svg = svg.replace("{{CHANNEL_NAME}}", escape(ctx.channel_name))
        svg = svg.replace("{{COLOR_1}}", escape(ctx.color_1))
        svg = svg.replace("{{COLOR_2}}", escape(ctx.color_2))

        return svg

    def _compute_marquee_params(self, title: str, font_size: int = 18) -> MarqueeParams:
        est_width = self._estimate_text_width_px(title, font_size)

        gap = max(est_width + 70, 520)
        title_x2 = 160 + gap
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

    @staticmethod
    def extract_color_from_img(thumb_data: str) -> tuple[str, str] | None:
        try:
            if thumb_data.startswith("data:"):
                _, b64 = thumb_data.split(",", 1)
            else:
                b64 = thumb_data
            ct = ColorThief(BytesIO(base64.b64decode(b64)))

            palette = ct.get_palette(color_count=6, quality=5)
            c1 = palette[0]
            c2 = next((c for c in palette[1:] if cal_dist(c1, c) >= 28**2), palette[0])
            return to_hex(c1), to_hex(c2)

        except Exception:
            return "#000000", "#000000"
