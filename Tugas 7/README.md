# Verifikasi Ijazah: OCR Nomor Ijazah & Deteksi Tanda Tangan

Mini project Pengolahan Citra Digital. Input: citra ijazah → Output: nomor ijazah dan status tanda tangan.

```
Input : ijazah_001.png
Output: Nomor Ijazah : 571012022000056
        Tanda Tangan : PRESENT
```

## Cara menjalankan

```bash
# 1. Install Tesseract OCR (sistem)
sudo apt install tesseract-ocr          # Ubuntu/Debian
brew install tesseract                  # macOS
# Windows: https://github.com/UB-Mannheim/tesseract/wiki  (tambahkan ke PATH)

# 2. Library Python
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 3. Verifikasi satu citra
python main.py samples/ijazah_008_jpeg_artifacts.png
python main.py samples/ijazah_004_highnoise.png --enhancer otsu --debug results/debug

# 4. Evaluasi CER seluruh sampel + uji deteksi TTD
python evaluate.py
```

Struktur: `verifier.py` (pipeline), `main.py` (CLI), `evaluate.py` (CER & uji TTD), `samples/` (9 kondisi citra), `results/` (hasil evaluasi).

## Metode (sesuai pipeline)

| Tahap | Metode | Alasan |
|---|---|---|
| Orientasi | Coba 4 rotasi, pilih yang OCR-nya memuat kata kunci ("universitas", "ijazah", "rektor", ...) | Citra sampel terputar 90° |
| Grayscale | `cv2.cvtColor` BGR→Gray | Warna tidak dibutuhkan; kuning kertas jadi noise |
| Enhancement global | Non-Local Means denoising + CLAHE | Kurangi derau, normalkan kontras lokal |
| ROI nomor | Crop relatif (x 14–37%, y 88–97%) bagian angka | Hindari label "Nomor ijazah" yang sering salah baca |
| Enhancement ROI | Upscale 4× bicubic + **Otsu** (dibandingkan 6 metode) | Tulisan kecil (±10 px) perlu diperbesar dan dibinerkan |
| OCR | Tesseract `--psm 7`, whitelist digit `0-9` | Satu baris, hanya angka; koreksi `$→5`, `O→0`, dst. |
| ROI TTD | Area Rektor dan Dekan | Dua tanda tangan pejabat |
| Thresholding | Flat-field (bagi dengan estimasi latar) + Otsu | Tahan citra pudar / pencahayaan tidak merata |
| Morfologi | Opening 2×2 (buang bintik), closing elips 9×9 (sambung goresan) | Goresan TTD jadi satu komponen |
| Deteksi TTD | Connected components: area ≥ 3% ROI, lebar ≥ 35% ROI, kontras ≥ 25 | Teks cetak terpecah-pecah, TTD menyambung dan besar |

Hasil akhir `PRESENT` bila **kedua** TTD (Rektor dan Dekan) terdeteksi.

## Hasil evaluasi

CER = Levenshtein(GT, OCR) / panjang GT, GT = `571012022000056`, pada 9 citra degradasi (`results/cer_detail.csv`).

| Enhancement | CER rata-rata | Exact match |
|---|---|---|
| **Otsu** | **0.2889** | 4/9 |
| flat-field + Otsu | 0.3037 | 1/9 |
| denoise + sharpen + Otsu | 0.3481 | 2/9 |
| tanpa enhancement | 0.4963 | 2/9 |
| adaptive Gaussian | 0.5037 | 1/9 |
| CLAHE + Otsu | 0.8963 | 0/9 |

**Kesimpulan:** Otsu paling efektif (CER terendah). Pada teks kecil, tinta gelap pada kertas terang, Otsu memberi pemisahan foreground–background yang bersih tanpa memperkuat derau. CLAHE+Otsu terburuk karena CLAHE sudah dipakai di tahap global; pemakaian kedua memperkuat derau/tekstur kertas hingga menjadi "karakter". Adaptive threshold memecah goresan tipis pada ukuran digit sekecil ini.

**Deteksi TTD:** 9/9 benar pada citra asli (PRESENT) dan 9/9 benar pada citra yang TTD-nya dihapus (ABSENT).

## Keterbatasan (jujur)
- Citra sampel sangat kecil (302–601 px); OCR gagal total pada `lowcontrast`, `faded_underexposed`, `combined_degradation` (CER ≈ 0,9–1,0). Hanya 4/9 citra terbaca persis.
- ROI memakai posisi relatif tetap, hanya cocok untuk templat ijazah UI ini. Template lain perlu ROI baru (atau deteksi label dengan `image_to_data`).
- Uji negatif TTD bersifat sintetis (area dikosongkan), bukan ijazah tanpa TTD sungguhan; deteksi hanya menyatakan ada/tidaknya goresan, **bukan** keaslian TTD.
- Hanya satu ijazah (dengan 9 degradasi) yang diuji, sehingga kesimpulan CER belum bisa digeneralisasi.
