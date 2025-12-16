import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    theme: str
    playlist_id: str


class ConfigLoader:
    """
    README.md 안의 <!-- ... --> 주석 블록에서 설정을 읽어옵니다.

    예)
    <!--
    YT_CONFIG
    theme: default.svg
    playlist_id: PLxxxx
    -->
    """

    config_tag = "YT_MUSIC_CONFIG"
    default_theme = "default.svg"

    def from_markdown(self, md: str) -> Config:
        block: str | None = None

        for m in re.finditer(r"<!--(.*?)-->", md, flags=re.S):
            body = m.group(1).strip()
            if re.search(rf"^\s*{re.escape(self.config_tag)}\s*$", body, flags=re.M):
                block = body
                break

        if block is None:
            raise RuntimeError(
                f"README에 {self.config_tag} 주석 블록이 없어요.\n"
                "<!--\n"
                f"{self.config_tag}\n"
                "theme: ...\n"
                "playlist_id: ...\n"
                "-->"
            )

        cfg: dict[str, str] = {}
        for line in block.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line == self.config_tag:
                continue

            m = re.match(r"^([A-Za-z_][A-Za-z0-9_-]*)\s*:\s*(.+?)\s*$", line)
            if m:
                cfg[m.group(1).lower()] = m.group(2).strip()

        theme = cfg.get("theme", self.default_theme).strip()
        playlist_id = cfg.get("playlist_id", "").strip()

        if not playlist_id:
            raise RuntimeError(
                f"{self.config_tag}에 playlist_id: 가 필요해요.\n"
                "예) playlist_id: PLrpWLWlmavXBXidc7niUbK3dK39KVnugD"
            )

        if not re.fullmatch(r"[A-Za-z0-9_-]+", playlist_id):
            raise RuntimeError(
                f"playlist_id 형식이 올바르지 않아요: {playlist_id}\n"
                "URL이 아니라 ID만 입력해야 해요."
            )

        return Config(theme=theme, playlist_id=playlist_id)
