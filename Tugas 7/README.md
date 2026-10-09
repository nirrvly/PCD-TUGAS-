# Verifikasi Ijazah: OCR Nomor Ijazah & Deteksi Tanda Tangan

Mini project Pengolahan Citra Digital. Input: citra ijazah → Output: nomor ijazah dan status tanda tangan.

```
Input : ijazah_008_jpeg_artifacts.png
Output: Nomor Ijazah : 571012022000056
        Tanda Tangan : PRESENT
          - Rektor: PRESENT (ink=0.076)
          - Dekan: PRESENT (ink=0.179)
```

## Struktur repositori

```
ijazah-verifier/
├── ijazah_verifier.ipynb   # Notebook lengkap (pipeline + visualisasi + evaluasi CER), berdiri sendiri
├── verifier.py             # Modul pipeline (versi skrip)
├── main.py                 # CLI: verifikasi satu citra
├── evaluate.py             # Evaluasi CER + uji deteksi TTD (versi skrip)
├── requirements.txt
├── samples/                # 9 citra ijazah dengan kondisi degradasi berbeda
└── results/                # cer_detail.csv, cer_summary.csv, evaluasi.txt, cer_chart.png
```

Ada dua cara menjalankan, hasilnya sama: **Notebook** (disarankan, ada visualisasi) atau **skrip Python**.

## Prasyarat

1. **Python 3.9+**
2. **Tesseract OCR** (program terpisah, bukan library Python):
   - Windows: unduh installer dari https://github.com/UB-Mannheim/tesseract/wiki (lokasi bawaan `C:\Program Files\Tesseract-OCR`)
   - Ubuntu/Debian: `sudo apt install tesseract-ocr`
   - macOS: `brew install tesseract`
3. **Library Python**:

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install matplotlib             # tambahan untuk grafik di notebook
```

> **Windows:** jika `tesseract` tidak dikenali di terminal, tambahkan baris berikut di `verifier.py` tepat setelah `import pytesseract`
> (notebook sudah menanganinya otomatis):
> ```python
> pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
> ```

## Cara menjalankan

### A. Notebook (`ijazah_verifier.ipynb`)

1. Letakkan notebook sejajar dengan folder `samples/`.
2. Buka di VS Code (ekstensi Jupyter) atau `jupyter notebook`, pilih kernel Python yang sudah berisi library.
3. Klik **Run All**.

Isi notebook: instalasi dan konfigurasi Tesseract → modul pipeline → visualisasi tiap tahap → verifikasi satu citra → evaluasi CER semua metode enhancement (tabel + grafik) → uji deteksi tanda tangan → kesimpulan.
Untuk mengganti citra uji, ubah variabel `PATH` pada sel visualisasi.

### B. Skrip Python

```bash
# Verifikasi satu citra
python main.py samples/ijazah_008_jpeg_artifacts.png

# Pilih metode enhancement dan simpan citra antara (debug)
python main.py samples/ijazah_004_highnoise.png --enhancer otsu --debug results/debug

# Evaluasi CER seluruh sampel + uji deteksi TTD
python evaluate.py
```

Pilihan `--enhancer`: `tanpa_enhancement`, `otsu` (default), `clahe+otsu`, `adaptive_gaussian`, `denoise+sharpen+otsu`, `flatfield+otsu`.
Di Windows (CMD) gunakan `samples\ijazah_008_jpeg_artifacts.png`.

## Metode (sesuai pipeline)

```
Citra Ijazah → Grayscale → Enhancement global
      ├─ ROI Nomor → Enhancement (Otsu) → OCR → Nomor Ijazah
      └─ ROI TTD   → Thresholding → Morfologi → Signature Detection
                         └──────────→ Hasil Verifikasi
```

| Tahap | Metode | Alasan |
|---|---|---|
| Orientasi | Coba 4 rotasi, pilih yang OCR-nya memuat kata kunci ("universitas", "ijazah", "rektor", ...) | Citra sampel terputar 90° |
| Grayscale | `cv2.cvtColor` BGR→Gray | Warna tidak dibutuhkan; kuning kertas jadi noise |
| Enhancement global | Non-Local Means denoising + CLAHE | Kurangi derau, normalkan kontras lokal |
| ROI nomor | Crop relatif (x 14–37%, y 88–97%) bagian angka saja | Hindari label "Nomor ijazah" yang sering salah baca |
| Enhancement ROI | Upscale 4× bicubic + **Otsu** (dibandingkan 6 metode) | Tulisan kecil (±10 px) perlu diperbesar dan dibinerkan |
| OCR | Tesseract `--psm 7`, whitelist digit `0-9`, koreksi `$→5`, `O→0`, `l→1`, `B→8` | Satu baris, hanya angka |
| ROI TTD | Area Rektor (x 12–42%, y 68–84%) dan Dekan (x 60–90%, y 66–84%) | Dua tanda tangan pejabat |
| Thresholding | Flat-field (bagi dengan estimasi latar, median blur) + Otsu | Tahan citra pudar / pencahayaan tidak merata |
| Morfologi | Opening 2×2 (buang bintik), closing elips 9×9 (sambung goresan) | Goresan TTD jadi satu komponen |
| Deteksi TTD | Connected components: area ≥ 3% ROI, lebar ≥ 35% ROI, kontras tinta–kertas ≥ 25 | Teks cetak terpecah-pecah; TTD menyambung dan besar |

Hasil akhir `PRESENT` bila **kedua** TTD (Rektor dan Dekan) terdeteksi.

## Hasil evaluasi

CER = Levenshtein(GT, OCR) / panjang GT, dengan GT = `571012022000056`, pada 9 citra degradasi (`results/cer_detail.csv`, `results/cer_summary.csv`).

| Enhancement | CER rata-rata | Exact match |
|---|---|---|
| **Otsu** | **0.2889** | 4/9 |
| flat-field + Otsu | 0.3037 | 1/9 |
| denoise + sharpen + Otsu | 0.3481 | 2/9 |
| tanpa enhancement | 0.4963 | 2/9 |
| adaptive Gaussian | 0.5037 | 1/9 |
| CLAHE + Otsu | 0.8963 | 0/9 |

Hasil OCR per citra dengan metode Otsu:

| Citra | OCR | CER |
|---|---|---|
| 001 highquality_enhanced | 71912023000056 | 0.20 |
| 002 lowcontrast | (kosong) | 1.00 |
| 003 blurred | 71012022000056 | 0.07 |
| 004 highnoise | 571012022000056 | 0.00 |
| 005 lowres_upsampled | 571012022000056 | 0.00 |
| 006 faded_underexposed | 7 | 0.93 |
| 007 colorshift_warmtint | 571012022000056 | 0.00 |
| 008 jpeg_artifacts | 571012022000056 | 0.00 |
| 009 combined_degradation | 7143422000054 | 0.40 |

**Kesimpulan:** Otsu paling efektif (CER terendah). Pada teks kecil berupa tinta gelap di atas kertas terang, Otsu memberi pemisahan foreground–background yang bersih tanpa memperkuat derau. CLAHE+Otsu terburuk karena CLAHE sudah dipakai di tahap global; pemakaian kedua memperkuat derau/tekstur kertas hingga terbaca sebagai "karakter". Adaptive threshold memecah goresan tipis pada ukuran digit sekecil ini.

**Deteksi TTD:** 9/9 benar pada citra asli (PRESENT) dan 9/9 benar pada citra yang area TTD-nya dikosongkan (ABSENT).

## Keterbatasan

- Citra sampel sangat kecil (302–601 px); OCR gagal total pada `lowcontrast`, `faded_underexposed`, dan `combined_degradation` (CER ≈ 0,4–1,0). Hanya 4/9 citra terbaca persis.
- ROI memakai posisi relatif tetap, hanya cocok untuk templat ijazah UI ini. Templat lain perlu ROI baru (atau pencarian label dengan `pytesseract.image_to_data`).
- Uji negatif TTD bersifat sintetis (area dikosongkan), bukan ijazah tanpa TTD sungguhan; deteksi hanya menyatakan ada/tidaknya goresan, **bukan** keaslian tanda tangan.
- Hanya satu ijazah (dengan 9 degradasi) yang diuji, sehingga kesimpulan CER belum bisa digeneralisasi.
- Angka CER dapat sedikit berbeda di komputer lain bergantung versi Tesseract/OpenCV (diuji dengan Tesseract 5 dan OpenCV 4.13).
