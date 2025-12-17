# profile-music-widget

YouTube(Playlist)에서 랜덤 곡을 골라 **GitHub README에 넣을 SVG 음악 위젯 카드**를 생성하는 레포입니다.  

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
- `{{ YOUR_THEME }}`: 사용할 테마. 현재 지원 테마: default.svg (추후 추가 예정)

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

      - name: Deploy dist to output branch
        uses: crazy-max/ghaction-github-pages@v4
        with:
          target_branch: output
          build_dir: dist
          keep_history: false
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```