import argparse, os
from verifier import verify, ENHANCERS

p = argparse.ArgumentParser(description="Verifikasi ijazah: OCR nomor + deteksi TTD")
p.add_argument("image")
p.add_argument("--enhancer", default="otsu", choices=ENHANCERS)
p.add_argument("--debug", help="folder keluaran citra antara")
a = p.parse_args()
if a.debug:
    os.makedirs(a.debug, exist_ok=True)
r = verify(a.image, a.enhancer, a.debug)
print(f"Nomor Ijazah : {r['nomor_ijazah'] or '(tidak terbaca)'}")
print(f"Tanda Tangan : {r['tanda_tangan']}")
for k, (ok, ink) in r["ttd_detail"].items():
    print(f"  - {k}: {'PRESENT' if ok else 'ABSENT'} (ink={ink:.3f})")
