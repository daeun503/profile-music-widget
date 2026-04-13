import base64
import os
from dataclasses import dataclass
from pathlib import Path

from tools.media_client import YouTubeGifGenerator
from tools.render_svg import RenderContext, SvgRenderer
from tools.youtube_client import YouTubeClient

PROJECT_ROOT = Path(__file__).parent


@dataclass(frozen=True)
class Paths:
    themes_dir: Path = PROJECT_ROOT / "themes"
    out_dir: Path = PROJECT_ROOT / "dist"
    out_svg: Path = PROJECT_ROOT / "dist/youtube-music-widget.svg"
    out_bg_gif: Path = PROJECT_ROOT / "dist/bg.gif"


def to_base64(data: bytes, mime: str) -> str:
    b64 = base64.b64encode(data).decode("ascii")
    return f"data:{mime};base64,{b64}"


def to_plain_bg_data(color: str) -> str:
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16">'
        f'<rect width="100%" height="100%" fill="{color}"/>'
        "</svg>"
    )
    return to_base64(svg.encode("utf-8"), "image/svg+xml")


def parse_corner_radius_scale(raw: str) -> float:
    try:
        value = float(raw.strip())
    except ValueError as e:
        raise RuntimeError(
            f"Invalid YT_CORNER_RADIUS_SCALE: {raw!r}. Expected a number between 0.0 and 2.0."
        ) from e

    if value < 0.0 or value > 2.0:
        raise RuntimeError(
            f"YT_CORNER_RADIUS_SCALE out of range: {value}. Expected between 0.0 and 2.0."
        )
    return value


def scaled_rx(base: int, scale: float) -> str:
    value = max(0.0, base * scale)
    return f"{value:.2f}".rstrip("0").rstrip(".")


def parse_background(raw: str) -> str:
    value = raw.strip().lower()
    if value not in {"image", "plain"}:
        raise RuntimeError(
            f"Invalid YT_BACKGROUND: {raw!r}. Expected 'image' or 'plain'."
        )
    return value


class YouTubeCardGeneratorApp:
    def __init__(self) -> None:
        self.paths = Paths()
        self.yt_client = YouTubeClient()
        self.gif = YouTubeGifGenerator()
        self.svg = SvgRenderer()

    def run(self) -> None:
        theme_input = os.getenv("YT_THEME", "default.svg").strip()
        background_mode = parse_background(os.getenv("YT_BACKGROUND", "image"))
        if theme_input.lower() in {"plain", "plain.svg"}:
            print("[WARN] 'plain' theme is deprecated; use background=plain with theme=default.svg")
            theme_input = "default.svg"
            background_mode = "plain"
        theme_file = theme_input

        theme_path = self.paths.themes_dir / theme_file
        if not theme_path.exists():
            raise RuntimeError(f"Theme file not found: {theme_path}")
        corner_scale = parse_corner_radius_scale(os.getenv("YT_CORNER_RADIUS_SCALE", "1.0"))

        is_gif_theme = os.getenv("YT_IS_GIF_BG") == "true"

        playlist_id = os.getenv("YT_PLAYLIST_ID").strip()
        entry = self.yt_client.pick_random_entry(playlist_id)

        self.paths.out_dir.mkdir(parents=True, exist_ok=True)
        image_data = self.yt_client.image_url_to_base64(entry.thumbnail_url)
        thumb_data = to_base64(image_data[0], image_data[1])
        color1, color2 = self.svg.extract_color_from_img(thumb_data)

        bg_data = thumb_data
        if background_mode == "plain":
            bg_data = to_plain_bg_data(color1)
        elif is_gif_theme:
            try:
                gif_path = self.gif.make_10s_gif(entry.video_id, self.paths.out_bg_gif)
                bg_data = to_base64(gif_path.read_bytes(), "image/gif")
            except Exception as e:
                print(f"[WARN] Failed to generate GIF background → falling back to thumbnail: {e}")

        is_phone_theme = theme_file == "yt_phone.svg"
        card_base = 14 if is_phone_theme else 12
        card_border_base = 13 if is_phone_theme else card_base
        thumb_base = 8 if is_phone_theme else 6
        thumb_inner_base = 7 if is_phone_theme else thumb_base

        ctx = RenderContext(
            title=entry.title,
            url=entry.url,
            thumb_data=thumb_data,
            bg_data=bg_data,
            time_left="00:00",
            time_right=entry.duration_label,
            channel_name=entry.channel_name,
            color_1=color1,
            color_2=color2,
            card_rx=scaled_rx(card_base, corner_scale),
            card_border_rx=scaled_rx(card_border_base, corner_scale),
            thumb_rx=scaled_rx(thumb_base, corner_scale),
            thumb_inner_rx=scaled_rx(thumb_inner_base, corner_scale),
            track_dur_s=str(max(1, entry.duration_seconds)),
        )

        rendered = self.svg.render(theme_path, ctx)
        self.paths.out_svg.write_text(rendered, encoding="utf-8")
        print(f"Wrote: {self.paths.out_svg}")


def main() -> None:
    YouTubeCardGeneratorApp().run()


if __name__ == "__main__":
    main()
