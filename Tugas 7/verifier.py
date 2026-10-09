"""Prototype verifikasi ijazah: OCR nomor ijazah + deteksi tanda tangan.

Pipeline:
Citra -> Grayscale -> Enhancement -> (ROI Nomor: enhancement -> OCR)
                                  -> (ROI TTD: thresholding -> morphology -> deteksi)
"""
import re
import cv2
import numpy as np
import pytesseract

# ROI relatif (x1, y1, x2, y2) terhadap citra ijazah posisi tegak
ROI_NOMOR = (0.14, 0.88, 0.37, 0.97)   # hanya deret angka (tanpa label)
ROI_TTD = {"Rektor": (0.12, 0.68, 0.42, 0.84),
           "Dekan": (0.60, 0.66, 0.90, 0.84)}


# ---------- 1. Praproses global ----------
def to_gray(img):
    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if img.ndim == 3 else img


def enhance_global(gray):
    """Denoise ringan + CLAHE untuk menormalkan kontras."""
    den = cv2.fastNlMeansDenoising(gray, None, h=7)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    return clahe.apply(den)


def auto_rotate(gray):
    """Coba 4 orientasi, pilih yang OCR-nya memuat kata kunci ijazah."""
    codes = [None, cv2.ROTATE_90_CLOCKWISE, cv2.ROTATE_180,
             cv2.ROTATE_90_COUNTERCLOCKWISE]
    best, best_score = gray, -1
    for c in codes:
        g = gray if c is None else cv2.rotate(gray, c)
        big = cv2.resize(g, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        t = pytesseract.image_to_string(big, config="--psm 6").lower()
        score = sum(k in t for k in ("universitas", "indonesia", "ijazah",
                                     "rektor", "dekan", "nomor"))
        if score > best_score:
            best, best_score = g, score
    return best


# ---------- 2. Enhancement khusus ROI nomor (dibandingkan di evaluate.py) ----------
def _up(g, f=4):
    return cv2.resize(g, None, fx=f, fy=f, interpolation=cv2.INTER_CUBIC)


def enh_none(g):
    return _up(g)


def enh_otsu(g):
    return cv2.threshold(_up(g), 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]


def enh_clahe_otsu(g):
    c = cv2.createCLAHE(3.0, (4, 4)).apply(_up(g))
    return cv2.threshold(c, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]


def enh_adaptive(g):
    b = cv2.GaussianBlur(_up(g), (3, 3), 0)
    return cv2.adaptiveThreshold(b, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                 cv2.THRESH_BINARY, 41, 15)


def enh_denoise_sharpen_otsu(g):
    u = cv2.fastNlMeansDenoising(_up(g), None, h=10)
    blur = cv2.GaussianBlur(u, (0, 0), 3)
    sharp = cv2.addWeighted(u, 1.8, blur, -0.8, 0)
    return cv2.threshold(sharp, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]


def enh_flatfield_otsu(g):
    """Bagi dengan estimasi latar (median blur) -> regangkan kontras -> Otsu.
    Menormalkan pencahayaan/pudar sebelum binerisasi."""
    u = _up(g)
    bg = cv2.medianBlur(u, (max(u.shape) // 6) | 1)
    n = cv2.divide(u, bg, scale=255)
    n = cv2.normalize(n, None, 0, 255, cv2.NORM_MINMAX)
    return cv2.threshold(n, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]


ENHANCERS = {
    "tanpa_enhancement": enh_none,
    "otsu": enh_otsu,
    "clahe+otsu": enh_clahe_otsu,
    "adaptive_gaussian": enh_adaptive,
    "denoise+sharpen+otsu": enh_denoise_sharpen_otsu,
    "flatfield+otsu": enh_flatfield_otsu,
}


def crop_rel(img, roi):
    h, w = img.shape[:2]
    x1, y1, x2, y2 = roi
    return img[int(y1 * h):int(y2 * h), int(x1 * w):int(x2 * w)]


# ---------- 3. OCR ----------
def ocr_nomor(gray_roi, enhancer="otsu"):
    """Return (nomor_ijazah, teks_mentah). Hanya digit yang diizinkan."""
    proc = ENHANCERS[enhancer](gray_roi)
    proc = cv2.copyMakeBorder(proc, 20, 20, 20, 20, cv2.BORDER_CONSTANT, value=255)
    cfg = "--psm 7 -c tessedit_char_whitelist=0123456789"
    raw = pytesseract.image_to_string(proc, config=cfg).strip()
    return re.sub(r"\D", "", raw), raw


def extract_number(raw):
    """Ambil deret angka setelah label 'Nomor ijazah:'; fallback deret terpanjang.

    Koreksi salah-baca umum Tesseract pada digit: $->5, O->0, l/I->1, B->8.
    """
    table = str.maketrans({"$": "5", "S": "5", "O": "0", "o": "0",
                           "l": "1", "I": "1", "B": "8", "|": "1"})
    m = re.search(r":\s*([0-9$SOolIB| ]{8,})", raw)
    if m:
        return re.sub(r"\s", "", m.group(1).translate(table))
    nums = re.findall(r"\d{8,}", raw.translate(table).replace(" ", ""))
    return max(nums, key=len) if nums else ""


# ---------- 4. Deteksi tanda tangan ----------
def detect_signature(gray_roi, min_area=0.03, min_width=0.35, min_contrast=25):
    """Normalisasi latar -> thresholding Otsu -> morfologi -> komponen terbesar.

    1. Latar diestimasi dengan median blur besar lalu dibagi (flat-field) agar
       tahan terhadap citra pudar / pencahayaan tidak merata.
    2. Otsu memisahkan tinta dari kertas.
    3. Opening membuang bintik derau, closing menyambung goresan TTD.
    4. TTD = komponen menyambung yang besar dan lebar. Teks cetak terpecah
       menjadi komponen kecil; kertas kosong tidak punya komponen besar.
    """
    g = cv2.GaussianBlur(gray_roi, (3, 3), 0)
    k = (max(g.shape) // 2) | 1
    bg = cv2.medianBlur(g, k)
    norm = cv2.normalize(cv2.divide(g, bg, scale=255), None, 0, 255, cv2.NORM_MINMAX)
    _, bw = cv2.threshold(norm, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    contrast = float(np.median(g[bw == 0]) - np.median(g[bw > 0])) if bw.any() else 0.0
    bw = cv2.morphologyEx(bw, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
    bw = cv2.morphologyEx(bw, cv2.MORPH_CLOSE, cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE, (9, 9)))
    _, _, st, _ = cv2.connectedComponentsWithStats(bw)
    H, W = bw.shape
    best, present = 0.0, False
    for x, y, w, h, area in st[1:]:
        best = max(best, area / (H * W))
        if area / (H * W) >= min_area and w / W >= min_width:
            present = True
    return present and contrast >= min_contrast, best, bw


# ---------- 5. Pipeline utama ----------
def verify(path, enhancer="otsu", debug_dir=None):
    img = cv2.imread(path)
    if img is None:
        raise FileNotFoundError(path)
    gray = to_gray(img)
    gray = auto_rotate(gray)
    gray = enhance_global(gray)

    nomor, raw = ocr_nomor(crop_rel(gray, ROI_NOMOR), enhancer)

    ttd = {}
    for nama, roi in ROI_TTD.items():
        ok, ink, bw = detect_signature(crop_rel(gray, roi))
        ttd[nama] = (ok, ink)
        if debug_dir:
            cv2.imwrite(f"{debug_dir}/ttd_{nama}.png", bw)
    if debug_dir:
        cv2.imwrite(f"{debug_dir}/gray_enhanced.png", gray)
    present = all(v[0] for v in ttd.values())
    return {"nomor_ijazah": nomor, "raw_ocr": raw, "ttd_detail": ttd,
            "tanda_tangan": "PRESENT" if present else "ABSENT"}
