"""
99_run_all.py — CA7 tam pipeline calistirici
"""
import subprocess
import sys
import os
import io

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = [
    "01_prep.py",
    "02_ip_gamma_sweep.py",
    "03_ip_lexicographic.py",
    "04_compare_to_baseline.py",
    "05_final_xlsx.py",
    "06_map.py",
]

for s in SCRIPTS:
    print(f"\n=== {s} ===")
    p = subprocess.run([sys.executable, os.path.join(SCRIPTS_DIR, s)], capture_output=True, text=True)
    out = p.stdout
    try:
        out = out.encode("cp1254", errors="replace").decode("cp1254")
    except Exception:
        pass
    print(out[-2000:] if len(out) > 2000 else out)
    if p.returncode != 0:
        print(f"[HATA] {s} basarisiz, returncode={p.returncode}")
        print("STDERR:", p.stderr[-1000:])
        break
    print(f"[OK] {s}")

print("\n=== TAMAMLANDI ===")
print("Ciktilar: cozum_alternatifi_7_risk_proportional_coverage/{results,comparison,final,maps}/")
