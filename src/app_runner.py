from __future__ import annotations

import sys
from pathlib import Path


def selected_new_count(job: dict) -> int:
    """Return the number of candidate-pool containers the CLI should receive."""
    k_total = int(job["k_total"])
    kept = job.get("kept_mevcut") or []
    return k_total - len(kept) if kept else k_total


def build_solver_command(
    job: dict,
    model_info: dict,
    project_root: Path,
    python_executable: str | None = None,
) -> list[str]:
    """Build a Streamlit job command using each solver script's CLI contract."""
    supported_weights = model_info.get("weights")
    weight_type = job["weight_type"]
    if supported_weights and weight_type not in supported_weights:
        supported = ", ".join(supported_weights)
        raise ValueError(f"{model_info.get('script', 'Selected solver')} supports weight types: {supported}. Got: {weight_type}")

    executable = python_executable or sys.executable
    script_path = Path(project_root) / "src" / model_info["script"]
    cmd = [executable, str(script_path)]

    if model_info.get("k_is_total"):
        cmd.extend(["--K", str(job["k_total"])])
    else:
        cmd.extend(["--K", str(selected_new_count(job))])

    cmd.extend(["--weight", weight_type])

    if model_info.get("has_beta"):
        cmd.extend(["--beta", str(job["beta"])])
    if model_info.get("has_sigma"):
        cmd.extend(["--sigma", job["sigma"]])

    kept = job.get("kept_mevcut") or []
    if not kept:
        cmd.append("--no-mevcut")
    elif model_info.get("has_kept"):
        cmd.extend(["--kept", ",".join(map(str, kept))])

    fixed = job.get("fixed_aday") or []
    if fixed and model_info.get("has_fixed"):
        cmd.extend(["--fixed", ",".join(map(str, fixed))])

    return cmd


def latest_match(directory: Path, pattern: str) -> Path | None:
    files = sorted(Path(directory).glob(pattern), key=lambda x: x.stat().st_mtime)
    return files[-1] if files else None


def _sigma_suffix(sigma: str) -> str:
    return "" if sigma == "800" else f"_sg{sigma}"


def _truncate_suffix(value: float | str | None) -> str:
    if value is None:
        return ""
    value_f = float(value)
    return f"_t{value}" if value_f > 0 else ""


def ip_file_suffix(job: dict) -> str:
    sigma = job.get("sigma", "800")
    beta = float(job.get("beta", 0.30))
    truncate = job.get("truncate", 0.15)
    nm_str = "_nomez" if not job.get("kept_mevcut") else ""
    wt_str = f"_{job.get('weight_type', 'risk')}"
    return (
        f"S{job.get('scenario', 'A')}{_sigma_suffix(sigma)}"
        f"_b{int(beta * 100)}_K{int(job['k_total'])}"
        f"{_truncate_suffix(truncate)}{nm_str}{wt_str}"
    )


def variant_output_paths(job: dict, models_dir: Path, version: str, mcdm: str, scenario: str) -> dict[str, Path]:
    suffix = ip_file_suffix(job)
    return {
        "ip": Path(models_dir) / f"ip_{version}_{mcdm}_{scenario}_{suffix}.xlsx",
        "coverage": Path(models_dir) / f"coverage_{version}_{mcdm}_{scenario}_{suffix}.xlsx",
        "summary": Path(models_dir) / f"summary_all_{suffix}.xlsx",
    }


def equity_file_suffix(job: dict) -> str:
    sigma = job.get("sigma", "800")
    beta = float(job.get("beta", 0.30))
    truncate = job.get("truncate", 0.0)
    nm_str = "_nomez" if not job.get("kept_mevcut") else ""
    weight = job.get("weight_type", "risk")
    wt_str = f"_{weight}" if weight != "risk" else ""
    return (
        f"S{job.get('scenario', 'A')}{_sigma_suffix(sigma)}"
        f"{_truncate_suffix(truncate)}{nm_str}"
        f"_b{int(beta * 100)}_K{int(job['k_total'])}{wt_str}"
    )


def pareto_file_suffix(job: dict) -> str:
    sigma = job.get("sigma", "800")
    beta = float(job.get("beta", 0.30))
    nm_str = "_nomez" if not job.get("kept_mevcut") else ""
    return (
        f"S{job.get('scenario', 'A')}{_sigma_suffix(sigma)}"
        f"_b{int(beta * 100)}_K{int(job['k_total'])}"
        f"{nm_str}_{job.get('weight_type', 'risk')}"
    )


def mclp_radius(job: dict) -> int:
    try:
        return int(job.get("sigma", 800))
    except (TypeError, ValueError):
        return 800


def find_solver_outputs(
    job: dict,
    model_key: str,
    models_dir: Path,
    results_dir: Path,
) -> dict[str, Path | None]:
    """Find the primary files written by a finished app solver job."""
    outputs: dict[str, Path | None] = {"summary": None, "ip": None, "result": None}

    if model_key == "05_ip":
        suffix = ip_file_suffix(job)
        outputs["summary"] = latest_match(models_dir, f"summary_all_*{suffix}*")
        outputs["ip"] = latest_match(models_dir, f"ip_v1_*{suffix}*")
        outputs["result"] = outputs["summary"] or outputs["ip"]
        return outputs

    if model_key == "11_lex":
        result = results_dir / "lexicographic" / f"lexicographic_result_{equity_file_suffix(job)}.xlsx"
    elif model_key == "13_eps":
        result = results_dir / "eps_constraint" / f"pareto_results_{pareto_file_suffix(job)}.xlsx"
    elif model_key == "14_single":
        result = results_dir / "single_stage" / f"single_stage_result_{equity_file_suffix(job)}.xlsx"
    elif model_key == "16_mclp":
        nm_str = "_nomez" if not job.get("kept_mevcut") else ""
        result = (
            models_dir
            / f"MCLP_K{int(job['k_total'])}_S{mclp_radius(job)}_{job.get('weight_type', 'population')}{nm_str}_secilenler.xlsx"
        )
    else:
        result = None

    outputs["result"] = result if result and result.exists() else None
    return outputs


def project_relative(path: Path | None, project_root: Path) -> str | None:
    if path is None:
        return None
    try:
        return str(path.relative_to(project_root))
    except ValueError:
        return str(path)
