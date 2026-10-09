"""Evaluasi: CER OCR nomor ijazah per metode enhancement + uji deteksi TTD."""
import glob, os, sys, csv
import cv2
import verifier as V

GT = "571012022000056"          # nomor ijazah pada citra asli


def cer(ref, hyp):
    """Character Error Rate = Levenshtein(ref, hyp) / len(ref)."""
    d = list(range(len(hyp) + 1))
    for i, rc in enumerate(ref, 1):
        prev, d[0] = d[0], i
        for j, hc in enumerate(hyp, 1):
            cur = d[j]
            d[j] = min(d[j] + 1, d[j - 1] + 1, prev + (rc != hc))
            prev = cur
    return d[-1] / len(ref)


def main(folder="samples", out="results"):
    os.makedirs(out, exist_ok=True)
    files = sorted(glob.glob(os.path.join(folder, "*.png")) +
                   glob.glob(os.path.join(folder, "*.jpg")))
    rows, prep = [], {}
    for f in files:
        g = V.to_gray(cv2.imread(f))
        g = V.enhance_global(V.auto_rotate(g))
        prep[f] = g
    # ---- CER per enhancer ----
    for name in V.ENHANCERS:
        for f, g in prep.items():
            nomor, _ = V.ocr_nomor(V.crop_rel(g, V.ROI_NOMOR), name)
            rows.append((name, os.path.basename(f), nomor, cer(GT, nomor)))
    with open(f"{out}/cer_detail.csv", "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(["enhancer", "file", "ocr", "cer"]); w.writerows(rows)
    print(f"{'Enhancement':<24}{'CER rata-rata':>14}{'Exact match':>14}")
    summary = []
    for name in V.ENHANCERS:
        r = [x for x in rows if x[0] == name]
        mean = sum(x[3] for x in r) / len(r)
        exact = sum(x[3] == 0 for x in r)
        summary.append((name, mean, exact, len(r)))
    for name, mean, exact, n in sorted(summary, key=lambda x: x[1]):
        print(f"{name:<24}{mean:>14.4f}{exact:>10}/{n}")
    with open(f"{out}/cer_summary.csv", "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(["enhancer", "mean_cer", "exact", "n"])
        w.writerows(sorted(summary, key=lambda x: x[1]))
    # ---- uji TTD: positif (asli) vs negatif (area TTD dikosongkan) ----
    print("\nDeteksi tanda tangan (positif = citra asli, negatif = TTD dihapus)")
    tp = tn = 0
    for f, g in prep.items():
        pos = all(V.detect_signature(V.crop_rel(g, r))[0] for r in V.ROI_TTD.values())
        h = g.copy()
        for r in V.ROI_TTD.values():
            hh, ww = h.shape; x1, y1, x2, y2 = r
            h[int(y1*hh):int(y2*hh), int(x1*ww):int(x2*ww)] = int(g.mean() * 0 + 235)
        neg = not any(V.detect_signature(V.crop_rel(h, r))[0] for r in V.ROI_TTD.values())
        tp += pos; tn += neg
        print(f"  {os.path.basename(f):<42} asli={'PRESENT' if pos else 'ABSENT ':<8} dihapus={'ABSENT' if neg else 'PRESENT'}")
    print(f"Akurasi TTD: positif {tp}/{len(prep)}, negatif {tn}/{len(prep)}")


if __name__ == "__main__":
    main(*sys.argv[1:])
