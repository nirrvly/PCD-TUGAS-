"""Area nomor ijazah -> enhancement -> OCR (Tesseract)."""
import re
import cv2
import pytesseract
from .preprocess import ENHANCERS

# ROI relatif (x0, y0, x1, y1) terhadap citra landscape tegak
# ROI baris "Nomor ijazah: <digit>" (layout template ijazah UI tetap, koordinat relatif)
ROI_NOMOR = (0.04, 0.895, 0.36, 0.975)

CFG = "--oem 1 --psm 7 -c tessedit_char_whitelist=0123456789NomrijazahC.-: "


def crop(img, roi):
    h, w = img.shape[:2]
    x0, y0, x1, y1 = roi
    return img[int(y0 * h):int(y1 * h), int(x0 * w):int(x1 * w)]


def upscale(g, target_h=130):
    f = max(3.0, target_h / g.shape[0])
    return cv2.resize(g, None, fx=f, fy=f, interpolation=cv2.INTER_CUBIC)


def parse_nomor(text):
    """Ambil deretan digit panjang (nomor ijazah) dari hasil OCR."""
    t = text.replace("O", "0").replace("o", "0")
    m = re.findall(r"\d{10,}", re.sub(r"[\s.\-]", "", t.split(":")[-1]))
    if m:
        return max(m, key=len)
    digits = re.sub(r"\D", "", text)
    return digits


def read_nomor(gray, method="clahe", roi=ROI_NOMOR):
    """Kembalikan (nomor, teks_mentah, citra_roi_enhanced)."""
    roi_img = upscale(crop(gray, roi))
    enh = ENHANCERS[method](roi_img)
    enh = cv2.copyMakeBorder(enh, 15, 15, 15, 15, cv2.BORDER_REPLICATE)
    raw = pytesseract.image_to_string(enh, lang="eng", config=CFG).strip()
    return parse_nomor(raw), raw, enh


ENSEMBLE = ["clahe+sharpen+otsu", "gamma", "otsu", "none", "stretch", "sharpen"]
EXPECTED_LEN = 15


def read_nomor_ensemble(gray, methods=ENSEMBLE):
    """Voting karakter-per-posisi antar metode enhancement (hanya hasil ber-panjang 15 digit
    yang ikut voting); jika tidak ada, kembalikan hasil terpanjang."""
    from collections import Counter
    cands = [read_nomor(gray, m)[0] for m in methods]
    valid = [c for c in cands if len(c) == EXPECTED_LEN]
    if not valid:
        return max(cands, key=len), cands
    voted = "".join(Counter(c[i] for c in valid).most_common(1)[0][0] for i in range(EXPECTED_LEN))
    return voted, cands
