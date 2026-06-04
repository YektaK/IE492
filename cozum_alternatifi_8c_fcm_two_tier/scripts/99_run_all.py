"""99_run_all.py - CA8c orchestrator"""
import subprocess, sys, os
ROOT = "D:/IE492"
CA = "cozum_alternatifi_8c_fcm_two_tier"
SCRIPTS = os.path.join(ROOT, CA, "scripts")
for s in ["01_fcm.py", "02_ip.py"]:
    p = os.path.join(SCRIPTS, s)
    print(f"\n=== {s} ===")
    r = subprocess.run([sys.executable, p], capture_output=True, text=True)
    print(r.stdout)
    if r.returncode != 0:
        print(r.stderr)
        sys.exit(1)
print("\n[OK] CA8c tamamlandi.")
