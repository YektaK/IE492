"""
run_all_scenarios.py
Config-driven experiment runner. Reads experiments_config.json and executes
each experiment by calling the appropriate Python scripts with CLI arguments.

Usage:
    python src/run_all_scenarios.py                     # run all experiments
    python src/run_all_scenarios.py --name Baseline_SA  # run specific experiment
    python src/run_all_scenarios.py --name TwoTier      # run experiments matching name
    python src/run_all_scenarios.py --list               # list available experiments

CLI args from the config are passed through to each script automatically.
Standard output is shown in real-time (capture_output=False).
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

SRC = Path(__file__).resolve().parent
ROOT = SRC.parent
CONFIG_FILE = ROOT / "experiments_config.json"
STEPS_PRIORITY = {
    "05_ip": SRC / "05_ip.py",
    "08_lscp": SRC / "08_lscp.py",
    "11_lexicographic": SRC / "11_lexicographic.py",
    "13_eps_constraint": SRC / "13_eps_constraint.py",
    "14_single_stage": SRC / "14_single_stage.py",
    "15_compromise": SRC / "15_compromise.py",
}


def build_args(cfg: dict, step: str) -> list[str]:
    """Build CLI args for a given step, passing only params the script supports."""
    args = [sys.executable, str(STEPS_PRIORITY[step])]
    # All scripts accept --scenario
    if "scenario" in cfg:
        args += ["--scenario", cfg["scenario"]]
    # --beta, --K, --truncate, --no-mevcut: all IP methods now support these
    if step != "15_compromise":
        if "sigma" in cfg:
            args += ["--sigma", cfg["sigma"]]
        if "K" in cfg:
            args += ["--K", str(cfg["K"])]
        if cfg.get("truncate", 0) > 0:
            args += ["--truncate", str(cfg["truncate"])]
        if cfg.get("no_mevcut", False):
            args.append("--no-mevcut")
    # --beta: 05_ip, 11_lex, 13_eps, 14_single all support it
    if step in ("05_ip", "11_lexicographic", "13_eps_constraint", "14_single_stage"):
        if "beta" in cfg:
            args += ["--beta", str(cfg["beta"])]
    return args


def run(label: str, cmd: list[str]) -> bool:
    print()
    print("=" * 70)
    print(f"  [{label}] {' '.join(cmd)}")
    print("=" * 70)
    t0 = time.time()
    r = subprocess.run(cmd, cwd=str(ROOT), capture_output=False)
    dt = time.time() - t0
    ok = r.returncode == 0
    if ok:
        print(f"  [OK] {dt:.1f}s")
    else:
        print(f"  !! HATA: returncode={r.returncode} ({dt:.1f}s)")
    return ok


def ensure_fcm(sigma: str, label: str = "") -> bool:
    """Run 04_fcm.py for given sigma if files don't already exist."""
    fcm_dir = ROOT / "results" / "fcm"
    suffix = f"_s{sigma}" if sigma != "800" else ""
    f1 = fcm_dir / f"mu_aday_140x17{suffix}.xlsx"
    f2 = fcm_dir / f"mu_mevcut_12x17{suffix}.xlsx"
    if f1.exists() and f2.exists():
        return True  # already exists
    return run(f"FCM sigma={sigma} {label}",
               [sys.executable, str(SRC / "04_fcm.py"), "--sigma", sigma])


def run_experiment(cfg: dict) -> bool:
    name = cfg["name"]
    print()
    print("#" * 70)
    print(f"#  EXPERIMENT: {name}")
    pars = {k: cfg[k] for k in ["scenario", "sigma", "beta", "K", "truncate", "no_mevcut"] if k in cfg}
    print(f"#  Params: {json.dumps(pars)}")
    print("#" * 70)

    # Ensure FCM files exist
    sigma = cfg.get("sigma", "800")
    if not ensure_fcm(sigma, name):
        return False

    all_ok = True
    for step in cfg.get("steps", list(STEPS_PRIORITY)):
        cmd = build_args(cfg, step)
        ok = run(f"{name} {step}", cmd)
        if not ok:
            all_ok = False
    return all_ok


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Run experiment configurations")
    parser.add_argument("--name", type=str, default=None,
                        help="Run only experiment(s) whose name contains this string")
    parser.add_argument("--list", action="store_true", help="List available experiments")
    args = parser.parse_args()

    with open(CONFIG_FILE, encoding="utf-8") as f:
        config = json.load(f)

    experiments = config["experiments"]

    if args.list:
        print("Available experiments:")
        for exp in experiments:
            name = exp["name"]
            sigma = exp.get("sigma", "800")
            scenario = exp.get("scenario", "?")
            beta = exp.get("beta", "?")
            K = exp.get("K", "?")
            trunc = exp.get("truncate", 0)
            nomev = " Y" if exp.get("no_mevcut") else " N"
            steps = ", ".join(exp.get("steps", []))
            sweep = exp.get("_beta_sweep", [])
            sw = f" beta_sweep={sweep}" if sweep else ""
            print(f"  {name:25s} | S={scenario} sigma={sigma:8s} beta={beta} K={K}"
                  f" trunc={trunc} nomev={nomev}{sw}")
            print(f"  {'':25s}   steps: {steps}")
        return

    total = 0
    ok_count = 0
    for exp in experiments:
        name = exp["name"]
        if args.name and args.name.lower() not in name.lower():
            continue

        # Handle beta sweeps
        beta_sweep = exp.pop("_beta_sweep", None)
        if beta_sweep:
            for b in beta_sweep:
                sweep_cfg = dict(exp)
                sweep_cfg["beta"] = b
                sweep_cfg["name"] = f"{name}_b{int(b*100)}"
                total += 1
                if run_experiment(sweep_cfg):
                    ok_count += 1
            exp["_beta_sweep"] = beta_sweep  # restore for listing
        else:
            total += 1
            if run_experiment(exp):
                ok_count += 1

    print()
    print("=" * 70)
    print(f"  TUM DENEYSEL COZUMLER TAMAMLANDI: {ok_count}/{total} basarili")
    print("=" * 70)
    return 0 if ok_count == total else 1


if __name__ == "__main__":
    sys.exit(main())
