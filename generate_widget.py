import base64
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from tools.load_config import ConfigLoader
from tools.media_client import YouTubeGifGenerator
from tools.render_svg import RenderContext, SvgRenderer
from tools.youtube_client import YouTubeClient

PROJECT_ROOT = Path(__file__).parent


@dataclass(frozen=True)
class Paths:
    readme_path: Path = PROJECT_ROOT / "README.md"
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

        self.yt_config = ConfigLoader()
        self.yt_client = YouTubeClient()

        self.gif = YouTubeGifGenerator()
        self.svg = SvgRenderer()

    def run(self) -> None:
        md = self.paths.readme_path.read_text(encoding="utf-8")
        yt_config = self.yt_config.from_markdown(md)

        theme_path = self.paths.themes_dir / yt_config.theme
        if not theme_path.exists():
            raise RuntimeError(f"theme 파일을 찾을 수 없어요: {theme_path}")

        entry = self.yt_client.pick_random_entry(yt_config.playlist_id)

        self.paths.out_dir.mkdir(parents=True, exist_ok=True)
        image_data = self.yt_client.image_url_to_base64(entry.thumbnail_url)
        thumb_data = to_base64(image_data[0], image_data[1])

        try:
            gif_path = self.gif.make_10s_gif(entry.video_id, self.paths.out_bg_gif)
            bg_data = to_base64(gif_path.read_bytes(), "image/gif")
        except Exception as e:
            print(f"[WARN] GIF background 생성 실패 → 썸네일로 대체합니다: {e}")
            bg_data = thumb_data

        ctx = RenderContext(
            title=entry.title,
            url=entry.url,
            thumb_url=thumb_data,
            bg_url=bg_data,
            time_left="00:00",
            time_right=datetime.now().strftime("%m:%d"),
            channel_name=entry.channel_name,
        )

        rendered = self.svg.render(theme_path, ctx)
        self.paths.out_svg.write_text(rendered, encoding="utf-8")
        print(f"Wrote: {self.paths.out_svg}")


def main() -> None:
    YouTubeCardGeneratorApp().run()


if __name__ == "__main__":
    main()
