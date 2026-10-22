"""Prepare the pencil drawing for ASCII conversion.

source-photo.jpg -> source-prepped.png (grayscale, white background).

Steps: crop tight (top of the skull to the tie knot), grayscale, light blur,
moderate CLAHE, then very light grays are forced to pure white.
"""
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "source-photo.jpg"
OUT = ROOT / "source-prepped.png"

# Crop box (left, top, right, bottom) in source pixels, tuned for a 2048 px
# square drawing: top of the skull down to the tie knot. The ratio matches
# the ASCII grid (100 columns x 53 rows, characters about twice as tall as
# wide).
CROP = (377, 286, 1637, 1625)
BLUR_SIGMA = 2.0
CLAHE_CLIP = 1.8
CLAHE_TILE = 8
WHITE_ABOVE = 243  # grays lighter than this become pure white


def main() -> None:
    img = cv2.imread(str(SRC), cv2.IMREAD_COLOR)
    if img is None:
        raise SystemExit(f"Cannot read {SRC}")

    left, top, right, bottom = CROP
    img = img[top:bottom, left:right]

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (0, 0), BLUR_SIGMA)

    clahe = cv2.createCLAHE(clipLimit=CLAHE_CLIP, tileGridSize=(CLAHE_TILE, CLAHE_TILE))
    out = clahe.apply(gray)

    # The paper and the lightest hatching become pure white (mask taken
    # before CLAHE so the contrast boost cannot grey the background).
    out[gray >= WHITE_ABOVE] = 255

    cv2.imwrite(str(OUT), out)
    print(f"wrote {OUT.name} {out.shape[1]}x{out.shape[0]}, "
          f"white share {np.mean(out == 255):.0%}")


if __name__ == "__main__":
    main()
