"""99_run_all.py - CA9a orchestrator"""
import os, subprocess
ROOT = "D:/IE492"
CA = "cozum_alternatifi_9a_min_one_per_mahalle"
scripts = ["01_prep.py", "02_ip.py", "03_compare.py", "04_final_xlsx.py", "05_map.py"]
for s in scripts:
    p = os.path.join(ROOT, CA, "scripts", s)
    print(f"\n=== {s} ===")
    try:
        subprocess.run(["python", p], check=True)
    except subprocess.CalledProcessError as e:
        print(f"[HATA] {s}: {e}")
print("\n[OK] Tum scriptler tamamlandi")
