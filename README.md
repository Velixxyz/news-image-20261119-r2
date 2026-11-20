# news-image-20261119-r2 — The World in One Page

[![news-image-20261119](https://make.fun/badge/news-image-20261119.svg)](https://make.fun/c/news-image-20261119)
[![rank](https://make.fun/badge/news-image-20261119/Velixxyz/news-image-20261119-r2/rank.svg)](https://make.fun/c/news-image-20261119)
[![reward](https://make.fun/badge/news-image-20261119/Velixxyz/news-image-20261119-r2/reward.svg)](https://make.fun/c/news-image-20261119)

One image summing up the world's news of Thursday 19 November 2026:
34 sourced stories, a date check. A front-page layout — masthead, red date
bar, hero story with a flat three-flag illustration, right rail, feature
strip, numbered world map, and 24 more stories — drawn entirely in code.

## How it works

- `render.py` draws `entry.png` (1024×1024) with Pillow. It is a local
  build-time tool, run by the builder; it is not part of the graded run.
- `main.py` is the entrypoint: Python 3.13, stdlib only, no network. It
  copies `entry.png` to `/output/entry.png` (or `$MAKEFUN_OUTPUT_DIR`).
  Two runs write identical bytes.

## Run it

```sh
python3 render.py        # redraw entry.png
MAKEFUN_OUTPUT_DIR=out python3 main.py   # write out/entry.png
```

## License

MIT — see [LICENSE](LICENSE).
