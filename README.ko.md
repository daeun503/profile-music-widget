# profile-music-widget

YouTube(Playlist)에서 랜덤 곡을 골라 **GitHub README에 넣을 SVG 음악 위젯 카드**를 생성하는 레포입니다.  
(* 배경 GIF 테마는 yt-dlp 봇 이슈로 현재 지원하지 않습니다)

<div align="center">
  <p>
    ꜱᴀᴍᴘʟᴇ<br/>
    ▾
  </p>

<img src="./sample/sample2.svg" alt="playing" />

<br/>
<br/>

<img src="./sample/sample1.svg" alt="playing" />
<br/>
</div>

<br/>
<br/>

당신의 **`USERNAME` 레포지토리**를 다음과 같은 구조로 만든 후, `main.yml` 파일에 아래 파일대로 작성합니다.
```
USERNAME/
├── README.md
└── .github/
    └── workflows/
        └── main.yml
```


변경이 필요한 부분
- `{{ YOUR_PLAYLIST_ID }}`: 위젯에 표시할 YouTube 플레이리스트 ID로 변경
- `{{ YOUR_THEME }}`: 사용할 테마. 지원값: `default.svg`, `yt_phone.svg`
- `{{ YOUR_BACKGROUND }}`: 선택 사항. `image`(기본값) 또는 앨범 색상 단색 배경 `plain`
- `{{ YOUR_CORNER_RADIUS_SCALE }}`: 선택 사항. 모서리 둥글기 비율 `0.0`~`2.0` (`1.0` 기본값, 낮을수록 각짐)

```yml
# main.yml
name: build profile assets

on:
  schedule:
    - cron: "0 */24 * * *"
  workflow_dispatch:
  push:
    branches: [main]

jobs:
  generate:
    permissions:
      contents: write
    runs-on: ubuntu-latest
    timeout-minutes: 10

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: generate youtube music widget
        uses: daeun503/profile-music-widget@v1
        with:
          playlist_id: {{ YOUR_PLAYLIST_ID }}
          theme: {{ YOUR_THEME }}
          background: {{ YOUR_BACKGROUND }}
          corner_radius_scale: {{ YOUR_CORNER_RADIUS_SCALE }}

      - name: Deploy dist to output branch
        uses: crazy-max/ghaction-github-pages@v4
        with:
          target_branch: output
          build_dir: dist
          keep_history: false
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```
