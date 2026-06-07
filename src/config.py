import logging
import sys
from pathlib import Path

# Ensure sys.stdout has UTF-8 encoding on Windows
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# Proje Kök Dizini ve Klasör Yapısı
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "processed"
RESULTS_DIR = PROJECT_ROOT / "results"
MODELS_DIR = RESULTS_DIR / "models"
MAPS_DIR = PROJECT_ROOT / "figures" / "maps"
CHARTS_DIR = PROJECT_ROOT / "figures" / "charts"
JOBS_FILE = PROJECT_ROOT / "jobs.json"
COMPLETED_JOBS_FILE = PROJECT_ROOT / "completed_jobs_log.json"

# Logging Altyapısı Yapılandırması
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("IE492")


# Gerekli dizinl