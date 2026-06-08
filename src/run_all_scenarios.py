"""
run_all_scenarios.py
Config-driven experiment runner. Reads experiments_config.json and executes
each experiment by calling the appropriate Python scripts with CLI arguments.

Usage:
    python src/run_all_scenarios.py                     # run all experiments
    python src/run_all_scenarios.py --name Baseline_SA  # run specific experiment
    python src/run_all_scenarios.py --name Adaptive     # run experiments matching name
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

from scenario_utils import fuzzy_coverage_paths

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

STEPS_WITH_TRUNCATE = {"05_ip", "08_lscp", "11_lexicographic", "14_single_stage"}


def total_k_from_config(cfg: dict) -> int:
    """Convert config K (new containers) to total containers for scripts that need totals."""
    k_new = int(cfg.get("K", 8))
    return k_new if cfg.get("no_mevcut", False) else k_new + 12


def build_args(cfg: dict, step: str) -> list[str]:
    """Build CLI args for a given step, passing only params the script supports."""
    args = [sys.executable, str(STEPS_PRIORITY[step])]
    if step != "15_compromise" and "scenario" in cfg:
        args += ["--scenario", cfg["scenario"]]
    if step != "15_compromise":
        if "sigma" in cfg:
            args += ["--sigma", cfg["sigma"]]
        if "K" in cfg and step != "08_lscp":
            k_value = total_k_from_config(cfg) if step == "05_ip" else int(cfg["K"])
            args += ["--K", str(k_value)]
        if step in STEPS_WITH_TRUNCATE and "truncate" in cfg:
            args += ["--truncate", str(cfg["truncate"])]
        if cfg.get("no_mevcut", False):
            args.append("--no-mevcut")
    # --beta: 05_ip, 11_lex, 13_eps, 14_single all support it
    if step in ("05_ip", "11_lexicographic", "13_eps_constraint", "14_single_stage"):
        if "beta" in cfg:
            args += ["--beta", str(cfg["beta"])]
    if step == "15_compromise":
        if "scenario" in cfg:
            args += ["--scenario", cfg["scenario"]]
        if "sigma" in cfg:
            args += ["--sigma", cfg["sigma"]]
        if "beta" in cfg:
            args += ["--beta", str(cfg["beta"])]
        if "K" in cfg:
            args += ["--K", str(total_k_from_config(cfg))]
        if "weight" in cfg:
            args += ["--weight", str(cfg["weight"])]
        if cfg.get("no_mevcut", False):
            args.append("--no-mevcut")
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


def coverage_files_exist(sigma: str) -> bool:
    """Return True when the current fuzzy coverage inputs for sigma exist."""
    paths = fuzzy_coverage_paths(sigma)
    required = ["mu_aday", "mu_mevcut", "Q_i_vector"]
    return all(paths[key].exists() for key in required)


def coverage_generation_command(sigma: str) -> list[str]:
    """Build the command that generates fuzzy coverage files for sigma."""
    return [sys.executable, str(SRC / "04_fuzzy_coverage.py"), "--sigma", sigma]


def ensure_fuzzy_coverage(sigma: str, label: str = "") -> bool:
    """Run 04_fuzzy_coverage.py for sigma if files do not already exist."""
    if coverage_files_exist(sigma):
        return True
    return run(f"Fuzzy coverage sigma={sigma} {label}", coverage_generation_command(sigma))


def ensure_fcm(sigma: str, label: str = "") -> bool:
    """Backward-compatible alias for older callers."""
    return ensure_fuzzy_coverage(sigma, label)


def run_experiment(cfg: dict, dry_run: bool = False) -> bool:
    name = cfg["name"]
    print()
    print("#" * 70)
    print(f"#  EXPERIMENT: {name}")
    pars = {k: cfg[k] for k in ["scenario", "sigma", "beta", "K", "truncate", "no_mevcut"] if k in cfg}
    print(f"#  Params: {json.dumps(pars)}")
    print("#" * 70)

    # Ensure fuzzy coverage files exist
    sigma = cfg.get("sigma", "800")
    if dry_run:
        if not coverage_files_exist(sigma):
            print(f"[DRY-RUN] would generate coverage: {' '.join(coverage_generation_command(sigma))}")
    elif not ensure_fuzzy_coverage(sigma, name):
        return False

    all_ok = True
    for step in cfg.get("steps", list(STEPS_PRIORITY)):
        cmd = build_args(cfg, step)
        if dry_run:
            print(f"[DRY-RUN] {name} {step}: {' '.join(cmd)}")
            ok = True
        else:
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
    parser.add_argument("--dry-run", action="store_true", help="Print commands without executing them")
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
    matched_any = False
    for exp in experiments:
        name = exp["name"]
        if args.name and args.name.lower() not in name.lower():
            continue
        matched_any = True

        # Handle beta sweeps
        beta_sweep = exp.pop("_beta_sweep", None)
        if beta_sweep:
            for b in beta_sweep:
                sweep_cfg = dict(exp)
                sweep_cfg["beta"] = b
                sweep_cfg["name"] = f"{name}_b{int(b*100)}"
                total += 1
                if run_experiment(sweep_cfg, dry_run=args.dry_run):
                    ok_count += 1
            exp["_beta_sweep"] = beta_sweep  # restore for listing
        else:
            total += 1
            if run_experiment(exp, dry_run=args.dry_run):
                ok_count += 1

    if not matched_any:
        print(f"No experiments matched --name={args.name!r}. Use --list to see available experiments.")
        return 1

    print()
    print("=" * 70)
    label = "DRY-RUN TAMAMLANDI" if args.dry_run else "TUM DENEYSEL COZUMLER TAMAMLANDI"
    print(f"  {label}: {ok_count}/{total} basarili")
    print("=" * 70)
    return 0 if ok_count == total else 1


if __name__ == "__main__":
    sys.exit(main())
