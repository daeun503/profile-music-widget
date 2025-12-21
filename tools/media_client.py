import json
import random
import subprocess
from pathlib import Path

START_CANDIDATES = [20, 30, 40, 60]


class YouTubeGifGenerator:
    def make_10s_gif(self, video_id: str, out_gif: Path) -> Path:
        start = random.choice(START_CANDIDATES)

        out_gif.parent.mkdir(parents=True, exist_ok=True)
        tmp_mp4 = out_gif.with_suffix(".mp4")

        # 1) Download only a 10-second segment as an MP4
        subprocess.check_call(
            [
                "yt-dlp",
                "-f",
                "best[ext=mp4]/best",
                "--download-sections",
                f"*{start}-{start + 10}",
                "--merge-output-format",
                "mp4",
                "-o",
                str(tmp_mp4),
                f"https://www.youtube.com/watch?v={video_id}",
            ]
        )

        # 2) local mp4 -> GIF
        subprocess.check_call(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(tmp_mp4),
                "-vf",
                "fps=12,scale=560:-1:flags=lanczos,split[s0][s1];"
                "[s0]palettegen[p];[s1][p]paletteuse=dither=bayer",
                "-loop",
                "0",
                str(out_gif),
            ]
        )

        try:
            tmp_mp4.unlink(missing_ok=True)
        except Exception:
            pass

        return out_gif

    def get_video_duration__format_mmss(self, video_id: str) -> str:
        url = f"https://www.youtube.com/watch?v={video_id}"
        proc = subprocess.run(
            ["yt-dlp", "-j", "--no-playlist", url],
            capture_output=True,
            text=True,
            check=True,
        )

        info = json.loads(proc.stdout)

        duration = int(info["duration"])
        m, s = divmod(duration, 60)
        return f"{m:02d}:{s:02d}"
