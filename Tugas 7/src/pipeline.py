"""Orkestrasi pipeline lengkap."""
import cv2
from .preprocess import auto_orient, to_gray, enhance_global
from .ocr import read_nomor, read_nomor_ensemble
from .signature import detect_signatures


def verify(path, ocr_method="clahe", debug_dir=None):
    img = cv2.imread(path)
    if img is None:
        raise FileNotFoundError(path)
    img = auto_orient(img)
    gray = enhance_global(to_gray(img))
    if ocr_method == "ensemble":
        nomor, cands = read_nomor_ensemble(gray)
        raw = " | ".join(cands)
        enh = read_nomor(gray, "clahe+sharpen+otsu")[2]
    else:
        nomor, raw, enh = read_nomor(gray, ocr_method)
    sig = detect_signatures(gray)
    present = all(v["present"] for v in sig.values())
    res = {"nomor": nomor, "raw": raw, "ttd": sig, "present": present}
    if debug_dir:
        import os
        os.makedirs(debug_dir, exist_ok=True)
        b = os.path.splitext(os.path.basename(path))[0]
        cv2.imwrite(f"{debug_dir}/{b}_gray_enh.png", gray)
        cv2.imwrite(f"{debug_dir}/{b}_nomor_roi.png", enh)
        for k, v in sig.items():
            cv2.imwrite(f"{debug_dir}/{b}_ttd_{k}.png", v["mask"])
    return res
