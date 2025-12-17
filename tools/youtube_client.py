import random
from dataclasses import dataclass

import feedparser
import requests


@dataclass(frozen=True)
class YouTubeVideo:
    video_id: str
    channel_name: str
    title: str
    url: str
    thumbnail_url: str


class YouTubeClient:
    def __init__(self, *, timeout: int = 25) -> None:
        self.timeout = timeout

    def fetch_playlist_entries(self, playlist_id: str) -> list:
        playlist_url = (
            f"https://www.youtube.com/feeds/videos.xml?playlist_id={playlist_id}"
        )
        r = requests.get(
            playlist_url,
            headers={
                "User-Agent": "Mozilla/5.0",
                "Accept": "application/atom+xml,application/xml;q=0.9,*/*;q=0.8",
            },
            timeout=self.timeout,
        )
        r.raise_for_status()

        playlist_entries = feedparser.parse(r.content).entries
        if not playlist_entries:
            raise RuntimeError(f"Failed to read the playlist RSS: {playlist_url}")

        return playlist_entries

    def pick_random_entry(self, playlist_id: str) -> YouTubeVideo:
        entries = self.fetch_playlist_entries(playlist_id)
        entry = random.choice(entries)

        video_id = entry.get("yt:videoId") or entry.get("id").split(":")[-1]
        title = entry.get("title")
        url = entry.get("link")
        if not video_id or not title or not url:
            raise RuntimeError("An invalid video entry was selected.")

        thumb_url = f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"
        channel_name = "Unknown"
        if "author" in entry:
            channel_name = entry.author
        elif "authors" in entry and entry.authors:
            channel_name = entry.authors[0].get("name", "Unknown")

        return YouTubeVideo(
            video_id=video_id,
            title=title,
            url=url,
            thumbnail_url=thumb_url,
            channel_name=channel_name.strip(),
        )

    def image_url_to_base64(self, url: str) -> tuple[bytes, str]:
        data = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0", "Accept": "image/*,*/*;q=0.8"},
            timeout=self.timeout,
        )
        data.raise_for_status()

        ctype = data.headers.get("Content-Type", "").split(";")[0].strip().lower()
        if not ctype:
            ctype = "image/jpeg"

        return data.content, ctype
