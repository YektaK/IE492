# -*- coding: utf-8 -*-
"""
99_run_all_CA6.py
==========================================================
Cozum Alternatifi 3: Tum pipeline'i calistir.
01 -> 02 -> 03 -> 04 -> 05 -> 06 -> 07
==========================================================
"""
import subprocess
import sys
from pathlib import Path

CA6 = Path("D:/IE492/cozum_alternatifi_6_full_reloc_baseline/scripts")

STEPS = [
    "01_prep_full_relocation.py",
    "02_topsis.py",
    "03_fcm.py",
    "04_zero_one_ip.py",
    "05_compare.py",
    "06_final_xlsx.py",
    "07_map.py",
]

if __name__ == "__main__":
    print("=" * 70)
    print("CA6 - Full Relocation (baseline) - End-to-End Pipeline")
    print("=" * 70)
    for step in STEPS:
        print(f"\n>>> Running {step} ...")
        result = subprocess.run([sys.executable, str(CA6 / step)],
                                capture_output=True, text=True, encoding="utf-8",
                                errors="replace")
        try:
            print(result.stdout)
        except UnicodeEncodeError:
            print(result.stdout.encode("ascii", "replace").decode("ascii"))
        if result.returncode != 0:
            print(f"[HATA] {step} basarisiz. Stderr:")
            try:
                print(result.stderr[:2000])
            except UnicodeEncodeError:
                print(result.stderr[:2000].encode("ascii", "replace").decode("ascii"))
            sys.exit(1)
    print("\n" + "=" * 70)
    print("CA6 PIPELINE TAMAMLANDI")
    print("=" * 70)


