"""Entry point for the make.fun news-image-20261119 entry.

Stdlib-only: copies the pre-rendered entry.png (drawn by render.py in this
repository, a Pillow script run by the builder) to the output directory.
Deterministic: two runs write identical bytes because the source file never
changes during a run. No network, no randomness, no clock.
"""

import os
import shutil


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    src = os.path.join(here, "entry.png")
    if not os.path.isfile(src):
        raise SystemExit("entry.png missing next to main.py")
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    dest = os.path.join(out_dir, "entry.png")
    shutil.copyfile(src, dest)
    print("wrote", dest, os.path.getsize(dest), "bytes")


if __name__ == "__main__":
    main()
