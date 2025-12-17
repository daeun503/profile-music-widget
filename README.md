# profile-music-widget

This repository generates an **SVG music widget card** for your GitHub README  
by randomly selecting a song from a **YouTube playlist**.

(* Background GIF themes are currently not supported due to yt-dlp bot issues)

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

Create your **`USERNAME` repository** with the following structure,  
then write the `main.yml` file as shown below.

```
USERNAME/
├── README.md
└── .github/
    └── workflows/
        └── main.yml
```

Required changes

- {{ YOUR_PLAYLIST_ID }}: Replace with the YouTube playlist ID to display in the widget
- {{ YOUR_THEME }}: The theme to use. Currently supported themes: default.svg (more themes coming soon)

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