"""Tahap 1-2 pipeline: orientasi, grayscale, image enhancement global."""
import cv2
import numpy as np


def auto_orient(img):
    """Pastikan citra landscape & tegak. Ijazah sampel tersimpan portrait (miring 90 derajat)."""
    h, w = img.shape[:2]
    if h > w:
        img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
    return img


def to_gray(img):
    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if img.ndim == 3 else img


def enhance_global(gray):
    """Enhancement global ringan: denoise edge-preserving saja.
    Peningkatan kontras sengaja dilakukan per-ROI (lihat ENHANCERS) karena
    CLAHE/denoise kuat di tingkat global terbukti meratakan teks pudar."""
    return cv2.bilateralFilter(gray, 5, 25, 25)


# ---- Metode enhancement untuk area nomor (dibandingkan lewat CER) ----
def enh_none(g):
    return g


def enh_clahe(g):
    return cv2.createCLAHE(clipLimit=3.0, tileGridSize=(4, 4)).apply(g)


def enh_hist_eq(g):
    return cv2.equalizeHist(g)


def enh_gamma(g, gamma=0.7):
    lut = np.array([(i / 255.0) ** gamma * 255 for i in range(256)], np.uint8)
    return cv2.LUT(g, lut)


def enh_sharpen(g):
    blur = cv2.GaussianBlur(g, (0, 0), 1.2)
    return cv2.addWeighted(g, 1.8, blur, -0.8, 0)


def enh_bilateral_clahe(g):
    return cv2.createCLAHE(2.0, (4, 4)).apply(cv2.bilateralFilter(g, 5, 40, 40))


def enh_otsu(g):
    _, b = cv2.threshold(cv2.GaussianBlur(g, (3, 3), 0), 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return b


def enh_adaptive(g):
    return cv2.adaptiveThreshold(g, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 15)


def enh_combo(g):
    """CLAHE -> sharpen -> Otsu (kombinasi)."""
    return enh_otsu(enh_sharpen(enh_clahe(g)))


def enh_stretch(g):
    """Contrast stretching persentil 2-98 (efektif untuk citra low-contrast/faded)."""
    lo, hi = np.percentile(g, (0.5, 99.5))
    return np.clip((g.astype(np.float32) - lo) * 255.0 / max(hi - lo, 1), 0, 255).astype(np.uint8)


def enh_bgnorm(g):
    """Normalisasi latar (bagi dengan estimasi background) + stretch + sharpen ringan."""
    bg = cv2.medianBlur(cv2.dilate(g, np.ones((9, 9), np.uint8)), 21)
    n = cv2.divide(g, bg, scale=255)
    return enh_sharpen(enh_stretch(n))


ENHANCERS = {
    "stretch": enh_stretch,
    "bgnorm": enh_bgnorm,
    "none": enh_none,
    "hist_eq": enh_hist_eq,
    "clahe": enh_clahe,
    "gamma": enh_gamma,
    "sharpen": enh_sharpen,
    "bilateral+clahe": enh_bilateral_clahe,
    "otsu": enh_otsu,
    "adaptive": enh_adaptive,
    "clahe+sharpen+otsu": enh_combo,
}
