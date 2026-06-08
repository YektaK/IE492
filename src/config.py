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


# Gerekli dizinlerin var olduğundan emin ol
MODELS_DIR.mkdir(parents=True, exist_ok=True)
MAPS_DIR.mkdir(parents=True, exist_ok=True)
CHARTS_DIR.mkdir(parents=True, exist_ok=True)

def norm_mahalle(s: str) -> str:
    """Tek merkezi Türkçe karakter normalizasyonu."""
    if not isinstance(s, str):
        return ""
    tr = str.maketrans({"Ç":"C","Ğ":"G","İ":"I","Ö":"O","Ş":"S","Ü":"U",
                        "ç":"C","ğ":"G","ı":"I","ö":"O","ş":"S","ü":"U"})
    return s.strip().translate(tr).upper()
