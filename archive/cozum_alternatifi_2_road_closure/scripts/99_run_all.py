# -*- coding: utf-8 -*-
"""
99_run_all.py
==========================================================
Cozum Alternatifi 2: Tum pipeline'i uc uca calistirir.
==========================================================
"""
import subprocess
import sys
from pathlib import Path

CA2 = Path("D:/IE492/cozum_alternatifi_2_road_closure")
SCRIPTS = CA2 / "scripts"
SCRIPTS_LIST = [
    "01_prep_road_closure.py",
    "02_topsis_with_road.py",
    "03_fcm.py",
    "04_zero_one_ip_with_road.py",
    "05_compare.py",
    "06_final_xlsx.py",
    "07_map.py",
]

if __name__ == "__main__":
    print("=" * 60)
    print("COZUM ALTERNATIFI 2 - TUM PIPELINE")
    print("=" * 60)
    failed = []
    for s in SCRIPTS_LIST:
        path = SCRIPTS / s
        if not path.exists():
            print(f"[FAIL] {s} dosyasi yok")
            failed.append(s)
            continue
        print(f"\n>>> {s}")
        r = subprocess.run([sys.executable, str(path)], cwd=str(SCRIPTS.parent))
        if r.returncode != 0:
            print(f"[FAIL] {s} (returncode={r.returncode})")
            failed.append(s)
    print("\n" + "=" * 60)
    if failed:
        print(f"Basarisiz: {failed}")
    else:
        print("Tum scriptler basariyla calisti.")
    print("=" * 60)
