import base64
import os
from dataclasses import dataclass
from datetime import datetime
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


class YouTubeCardGeneratorApp:
    def __init__(self) -> None:
        self.paths = Paths()
        self.yt_client = YouTubeClient()
        self.gif = YouTubeGifGenerator()
        self.svg = SvgRenderer()

    def run(self) -> None:
        theme_path = self.paths.themes_dir / os.getenv("YT_THEME").strip()
        if not theme_path.exists():
            raise RuntimeError(f"Theme file not found: {theme_path}")

        is_gif_theme = os.getenv("YT_IS_GIF_BG") == "true"

        playlist_id = os.getenv("YT_PLAYLIST_ID").strip()
        entry = self.yt_client.pick_random_entry(playlist_id)

        self.paths.out_dir.mkdir(parents=True, exist_ok=True)
        image_data = self.yt_client.image_url_to_base64(entry.thumbnail_url)
        thumb_data = to_base64(image_data[0], image_data[1])

        bg_data = thumb_data
        if is_gif_theme:
            try:
                gif_path = self.gif.make_10s_gif(entry.video_id, self.paths.out_bg_gif)
                bg_data = to_base64(gif_path.read_bytes(), "image/gif")
            except Exception as e:
                print(f"[WARN] Failed to generate GIF background → falling back to thumbnail: {e}")

        try:
            time_right = self.gif.get_video_duration__format_mmss(entry.video_id)
        except Exception as e:
            print(f"[WARN] Failed to get video duration: {e}")
            time_right = datetime.now().strftime("%m:%d")

        color1, color2 = self.svg.extract_color_from_img(thumb_data)
        ctx = RenderContext(
            title=entry.title,
            url=entry.url,
            thumb_data=thumb_data,
            bg_data=bg_data,
            time_left="00:00",
            time_right=time_right,
            channel_name=entry.channel_name,
            color_1=color1,
            color_2=color2,
        )

        rendered = self.svg.render(theme_path, ctx)
        self.paths.out_svg.write_text(rendered, encoding="utf-8")
        print(f"Wrote: {self.paths.out_svg}")


def main() -> None:
    YouTubeCardGeneratorApp().run()


if __name__ == "__main__":
    main()
