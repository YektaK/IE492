import json
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

# Yaygın sabitler
MAHALLE_COUNT = 15
COVERAGE_THRESHOLD = 0.50
TRUNCATION_THRESHOLD = 0.15
DEFAULT_BETA = 0.30
EQUITY_ALPHA = 0.20
EARTH_RADIUS = 6_371_000.0
DATA_DIR = PROJECT_ROOT / "data" / "processed"
RESULTS_DIR = PROJECT_ROOT / "results"
MODELS_DIR = RESULTS_DIR / "models"
MAPS_DIR = PROJECT_ROOT / "figures" / "maps"
CHARTS_DIR = PROJECT_ROOT / "figures" / "charts"
JOBS_FILE = PROJECT_ROOT / "jobs.json"
COMPLETED_JOBS_FILE = PROJECT_ROOT / "completed_jobs_log.json"

# Logging Altyapısı Yapılandırması
_log_dir = PROJECT_ROOT / "logs"
_log_dir.mkdir(parents=True, exist_ok=True)
_log_formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s:%(funcName)s:%(lineno)d %(message)s")

_stdout_handler = logging.StreamHandler(sys.stdout)
_stdout_handler.setFormatter(_log_formatter)

_file_handler = logging.FileHandler(_log_dir / "ie492.log", encoding="utf-8")
_file_handler.setFormatter(_log_formatter)

logging.basicConfig(
    level=logging.INFO,
    handlers=[_stdout_handler, _file_handler]
)
logger = logging.getLogger("IE492")


class JobLoggerAdapter(logging.LoggerAdapter):
    """Bir iş (job) bağlamında yapılandırılmış loglama için adapter."""
    def __init__(self, logger: logging.Logger, job_context: dict | None = None):
        super().__init__(logger, {})
        self.job_context = job_context or {}

    def process(self, msg: str, kwargs) -> tuple[str, dict]:
        ctx = " ".join(f"{k}={v}" for k, v in sorted(self.job_context.items()))
        if ctx:
            msg = f"[{ctx}] {msg}"
        return msg, kwargs


def job_logger(job: dict | None = None) -> JobLoggerAdapter:
    """job dict'inden context çıkararak JobLoggerAdapter döndürür."""
    ctx = {}
    if job:
        ctx["job_id"] = job.get("id", "")
        ctx["model"] = job.get("model", "")
        ctx["weight"] = job.get("weight_type", "")
        ctx["K"] = job.get("k_total", "")
    return JobLoggerAdapter(logger, ctx)


# Gerekli dizinlerin var olduğundan emin ol
MODELS_DIR.mkdir(parents=True, exist_ok=True)
MAPS_DIR.mkdir(parents=True, exist_ok=True)
CHARTS_DIR.mkdir(parents=True, exist_ok=True)

# completed_jobs_log.json varsayılan olarak oluştur
if not COMPLETED_JOBS_FILE.exists():
    COMPLETED_JOBS_FILE.write_text("[]", encoding="utf-8")

def get_mevcut_indices() -> list[int]:
    """Mevcut konteyner sayısını mevcut_12.xlsx'ten okuyarak index listesi döndürür."""
    try:
        import pandas as pd
        df = pd.read_excel(DATA_DIR / "mevcut_12.xlsx")
        return list(range(len(df)))
    except (FileNotFoundError, ImportError):
        return list(range(12))


def norm_mahalle(s: str) -> str:
    """Tek merkezi Türkçe karakter normalizasyonu."""
    if not isinstance(s, str):
        return ""
    tr = str.maketrans({"Ç":"C","Ğ":"G","İ":"I","Ö":"O","Ş":"S","Ü":"U",
                        "ç":"C","ğ":"G","ı":"I","ö":"O","ş":"S","ü":"U"})
    return s.strip().translate(tr).upper()
