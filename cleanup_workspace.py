#!/usr/bin/env python3
"""
cleanup_workspace.py — Archive clutter, clean workspace, provide .gitignore rules.

Usage:
    python cleanup_workspace.py          # dry-run (preview only)
    python cleanup_workspace.py --run     # execute archiving

Make sure to review the DRY_RUN toggle and the TARGET_DIRS / MD_KEYWORDS /
DB_EXTENSIONS lists below before executing.
"""

import shutil
import logging
import sys
from pathlib import Path

# ─── CONFIGURATION ──────────────────────────────────────────────────────────

DRY_RUN: bool = True  # True = preview only; False = execute moves

# Directories (relative to project root) to relocate into _project_archive/
TARGET_DIRS: list[str] = [
    "archive",
    "cache",
    "scratch",
    "temp",
    "tmp",
    "old",
    "legacy",
    "proposed_changes",
    "numba_results",
    "sota_results",
    "paper_prompts",
    "docs/planlar",
]

# Markdown docs whose filename (stem) contains any of these keywords
# will be archived.  README.md is always excluded.
MD_KEYWORDS: list[str] = ["review", "refactor", "summary"]

# Database / SQLite file extensions to archive
DB_EXTENSIONS: list[str] = [".db", ".sqlite", ".sqlite3"]

# Specific files (relative paths) to archive — useful for one-off items
# that don't match the general patterns above.
SPECIFIC_TARGETS: list[str] = [
    "docs/plan_CA7_risk_proportional.md",
    "docs/plan_CA8_fcm_refinement.md",
    "docs/plan_CA9_min_one_per_mahalle.md",
    "docs/ACADEMIC_EVALUATION_REPORT.md",
]

PROJECT_ROOT: Path = Path(".").resolve()
ARCHIVE_DIR: Path = PROJECT_ROOT / "_project_archive"

# Files / directories to *exclude* from scanning (beyond the archive dir itself)
EXCLUDE_NAMES: set[str] = {".git"}

# ─── SETUP LOGGING ──────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("cleanup")

# ─── COLLECTION ─────────────────────────────────────────────────────────────

def _excluded(path: Path) -> bool:
    return any(part.startswith(".") and part in EXCLUDE_NAMES for part in path.parts)


def collect_targets() -> list[Path]:
    found: list[Path] = []

    # 1 — target directories (only if they exist)
    for dirname in TARGET_DIRS:
        d = PROJECT_ROOT / dirname
        if d.is_dir() and not _excluded(d):
            found.append(d)

    # 2 — markdown files with "review"/"refactor"/"summary" in filename (stem)
    for md in PROJECT_ROOT.rglob("*.md"):
        if md.name.lower() == "readme.md":
            continue
        if _excluded(md) or ARCHIVE_DIR in md.parents:
            continue
        stem_lower = md.stem.lower()
        if any(kw in stem_lower for kw in MD_KEYWORDS):
            found.append(md)

    # 3 — database files
    for db in PROJECT_ROOT.rglob("*"):
        if _excluded(db) or ARCHIVE_DIR in db.parents:
            continue
        if db.suffix.lower() in DB_EXTENSIONS:
            found.append(db)

    # 4 — specific file paths listed in SPECIFIC_TARGETS
    for rel_path in SPECIFIC_TARGETS:
        p = PROJECT_ROOT / rel_path
        if p.exists():
            found.append(p)

    # Deduplicate (a file inside a captured directory is already covered)
    deduped: list[Path] = []
    for target in sorted(set(found), key=lambda p: str(p)):
        # Skip if this path is already inside another target in the list
        parents_in_list = any(
            other != target and other in target.parents for other in found
        )
        if not parents_in_list:
            deduped.append(target)

    return deduped


# ─── ARCHIVE LOGIC ───────────────────────────────────────────────────────────

def archive(targets: list[Path]) -> None:
    if not targets:
        log.info("Nothing to archive — found 0 targets.")
        return

    action = "Would archive" if DRY_RUN else "Archiving"
    log.info("%s %d item(s) → %s", action, len(targets), ARCHIVE_DIR)

    for src in targets:
        try:
            rel = src.relative_to(PROJECT_ROOT)
        except ValueError:
            rel = Path(src.name)
        dst = ARCHIVE_DIR / rel

        if DRY_RUN:
            log.info("  [DRY] %s → %s", src, dst)
            continue

        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))
        log.info("  MOVED %s → %s", src, dst)


def print_summary(targets: list[Path]) -> None:
    """Tabulate what would be moved (even outside DRY_RUN for user review)."""
    if not targets:
        return

    dirs = [t for t in targets if t.is_dir()]
    files = [t for t in targets if t.is_file()]

    log.info("=" * 60)
    log.info("SUMMARY — directories: %d, files: %d", len(dirs), len(files))
    log.info("=" * 60)

    if dirs:
        log.info("--- Directories ---")
        for d in dirs:
            size = sum(f.stat().st_size for f in d.rglob("*") if f.is_file())
            log.info("  %s  (%s bytes, %d items)", d, _fmt(size), _count_items(d))

    if files:
        log.info("--- Files ---")
        for f in files:
            log.info("  %s  (%s bytes)", f, _fmt(f.stat().st_size))


def _fmt(b: int) -> str:
    """Human-readable file size."""
    for unit in ("B", "KB", "MB", "GB"):
        if abs(b) < 1024:
            return f"{b:.1f}{unit}"
        b /= 1024
    return f"{b:.1f}TB"


def _count_items(d: Path) -> int:
    return sum(1 for _ in d.rglob("*"))


# ─── GITIGNORE SUGGESTIONS ──────────────────────────────────────────────────

GITIGNORE_BLOCK = r"""
# === Cleanup archive ===============================================
_project_archive/

# === Python =========================================================
__pycache__/
*.pyc
*.pyo
.pytest_cache/

# === Streamlit ======================================================
.streamlit/

# === Numba / JIT ====================================================
numba_results/

# === IDE / Editor ===================================================
.wrongstack/
.vscode/
.idea/
*.swp
*.swo

# === OS =============================================================
Thumbs.db
.DS_Store
"""


def print_gitignore_instructions() -> None:
    print("\n" + "#" * 70)
    print("# Recommended .gitignore additions")
    print("#" * 70 + "\n")
    print(GITIGNORE_BLOCK)
    print("# Add the block above to your .gitignore file.\n")


# ─── MAIN ───────────────────────────────────────────────────────────────────

def main() -> None:
    args = set(sys.argv[1:])

    if "--run" in args:
        global DRY_RUN
        DRY_RUN = False

    if DRY_RUN:
        log.info("DRY RUN MODE — use --run to execute\n")
    else:
        log.info("EXECUTION MODE — archiving items now\n")

    targets = collect_targets()
    print_summary(targets)
    archive(targets)
    print_gitignore_instructions()

    if DRY_RUN:
        log.info("\nDry-run complete. Review the list, then run with --run to execute.")
    else:
        log.info("\nArchiving complete. Review .gitignore suggestions above.")


if __name__ == "__main__":
    main()
