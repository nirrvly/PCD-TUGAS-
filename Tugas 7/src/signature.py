"""Area tanda tangan -> thresholding -> morfologi -> deteksi tanda tangan."""
import cv2
import numpy as np
from .ocr import crop

# ROI tanda tangan pejabat (Rektor, kiri) dan (Dekan, kanan), relatif
ROI_TTD = {
    "rektor": (0.12, 0.72, 0.42, 0.85),
    "dekan": (0.62, 0.68, 0.90, 0.82),
}
MIN_INK_RATIO = 0.015     # minimal rasio piksel tinta
MIN_COMPONENT_AREA = 40   # buang noise kecil
MIN_DYNAMIC_RANGE = 25    # rentang kontras minimum agar ROI dianggap berisi goresan
MAX_BG_LEVEL = 215        # piksel tinta harus jauh lebih gelap dari latar (skala 0-255 setelah normalisasi)


def binarize(g):
    g = cv2.GaussianBlur(g, (3, 3), 0)
    _, b = cv2.threshold(g, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    return b


def clean_morph(b):
    k_open = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2))
    k_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 3))
    b = cv2.morphologyEx(b, cv2.MORPH_OPEN, k_open)    # hapus bintik noise
    b = cv2.morphologyEx(b, cv2.MORPH_CLOSE, k_close)  # sambung goresan putus
    return b


def detect(gray, roi):
    """Return dict: present(bool), ink_ratio, bbox, mask."""
    r = crop(gray, roi)
    # normalisasi latar (hilangkan gradasi/pencahayaan) sebelum threshold
    bg = cv2.medianBlur(cv2.dilate(r, np.ones((15, 15), np.uint8)), 21)
    norm = cv2.divide(r, bg, scale=255)
    # guard: ROI tanpa goresan nyaris datar -> rentang dinamis (median - persentil gelap) kecil
    dyn = float(np.median(norm) - np.percentile(norm, 0.5))
    if dyn < MIN_DYNAMIC_RANGE:
        return {"present": False, "ink_ratio": 0.0, "bbox": None, "mask": np.zeros_like(norm), "dyn": dyn}
    lo, hi = np.percentile(norm, (0.5, 99.5))                    # contrast stretching
    norm = np.clip((norm.astype(np.float32) - lo) * 255 / max(hi - lo, 1), 0, 255).astype(np.uint8)
    mask = binarize(norm)
    mask[norm >= MAX_BG_LEVEL] = 0
    mask = clean_morph(mask)
    n, lab, stats, _ = cv2.connectedComponentsWithStats(mask, 8)
    keep = np.zeros_like(mask)
    for i in range(1, n):
        if stats[i, cv2.CC_STAT_AREA] >= MIN_COMPONENT_AREA:
            keep[lab == i] = 255
    ink = float(np.count_nonzero(keep)) / keep.size
    ys, xs = np.where(keep > 0)
    bbox = None
    if len(xs):
        bbox = (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()))
    span_ok = bbox is not None and (bbox[2] - bbox[0]) > 0.35 * keep.shape[1]
    return {"present": bool(ink >= MIN_INK_RATIO and span_ok),
            "ink_ratio": ink, "bbox": bbox, "mask": keep, "dyn": dyn}


def detect_signatures(gray):
    return {k: detect(gray, roi) for k, roi in ROI_TTD.items()}
