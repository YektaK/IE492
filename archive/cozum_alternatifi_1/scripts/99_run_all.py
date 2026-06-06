# -*- coding: utf-8 -*-
"""
99_run_all.py - End-to-end runner for Çözüm Alternatifi 1
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path("D:/IE492/cozum_alternatifi_1")
SCRIPTS = ROOT / "scripts"

SCRIPT_ORDER = [
    "01_ahp.py",
    "02_topsis.py",
    "03_fcm.py",
    "04_ip.py",
    "05_compare.py",
    "06_final_xlsx.py",
    "07_maps.py",
]

if __name__ == "__main__":
    print("=" * 60)
    print("ÇÖZÜM ALTERNATİFİ 1 - END-TO-END RUNNER")
    print("  C4 = İBB Tablo 5-4 barınma ihtiyacı (hane)")
    print("=" * 60)
    for s in SCRIPT_ORDER:
        path = SCRIPTS / s
        print(f"\n>>> {s}")
        if not path.exists():
            print(f"  [HATA] {path} bulunamadı.")
            sys.exit(1)
        try:
            res = subprocess.run(
                [sys.executable, str(path)],
                check=True, capture_output=True, text=True, encoding="utf-8"
            )
            out_lines = res.stdout.splitlines()
            for ln in out_lines[-15:]:
                print(f"  {ln}")
        except subprocess.CalledProcessError as e:
            print(f"  [HATA] {s} başarısız (exit {e.returncode}).")
            print(e.stdout[-2000:])
            print(e.stderr[-2000:])
            sys.exit(e.returncode)
    print("\n" + "=" * 60)
    print("TÜM ADIMLAR TAMAMLANDI.")
    print(f"Çıktılar: {ROOT}")
    print("=" * 60)
