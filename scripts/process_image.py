"""
Prepare a portrait photo for clean ASCII conversion.
"""

import os
import sys

import cv2
import numpy as np
from PIL import Image
from rembg import remove

HERE = os.path.dirname(os.path.abspath(__file__))

INP = (
    sys.argv[1]
    if len(sys.argv) > 1
    else os.path.join(HERE, "..", "data", "profile.jpg")
)

OUT = (
    sys.argv[2]
    if len(sys.argv) > 2
    else os.path.join(HERE, "..", "data", "source-prepped.png")
)

# 1. Remove the background
cut = remove(Image.open(INP).convert("RGBA"))

rgb = np.array(cut.convert("RGB"))
alpha = np.array(cut.split()[-1])

# 2. Increase local contrast
gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)

clahe = cv2.createCLAHE(
    clipLimit=2.6,
    tileGridSize=(8, 8)
)

gray = clahe.apply(gray)

# Slight global brightness adjustment
gray = cv2.convertScaleAbs(
    gray,
    alpha=1.05,
    beta=18
)

# 3. Put the subject on a white background
mask = alpha.astype(np.float32) / 255.0

mask = cv2.GaussianBlur(
    mask,
    (0, 0),
    1.0
)

out = (
    gray.astype(np.float32) * mask
    + 255.0 * (1.0 - mask)
)

out = np.clip(
    out,
    0,
    255
).astype(np.uint8)

Image.fromarray(
    out,
    mode="L"
).save(OUT)

print("wrote", OUT, out.shape)