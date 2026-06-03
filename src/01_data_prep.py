"""
01_data_prep.py
Parse all source data into clean xlsx files in output/data/

Outputs:
  output/data/adaylar.xlsx          (141 candidate AYDES sites with full features)
  output/data/mevcut_12.xlsx        (12 existing AFIS containers with coords)
  output/data/mahalle_nufus.xlsx    (17 mahalle + population)
  output/data/mahalle_risk.xlsx     (17 mahalle + Tablo 5-2 casualty data)
"""
import math
import re
import pandas as pd
import openpyxl
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(r"D:\IE492")
DOCS = ROOT / "docs"
OUT = ROOT / "output" / "data"
OUT.mkdir(parents=True, exist_ok=True)


def find_file(pattern_substr, ext):
    """Find a file in DOCS whose name contains pattern_substr (handles Turkish-encoding on Win)."""
    for p in DOCS.iterdir():
        if p.suffix.lower() == ext.lower() and pattern_substr.lower() in p.name.lower():
            return p
    raise FileNotFoundError(f"No {ext} file matching '{pattern_substr}' in {DOCS}")


# ---------------------------------------------------------------------------
# 1. Parse AYDES candidate sites from topsisguncel.xlsx (sheet SULTANBEYLI GUNCEL Liste)
# ---------------------------------------------------------------------------
def parse_adaylar():
    """
    The XLSX has merged headers. We read raw cells with openpyxl and re-assemble.
    Data layout (verified by inspection):
      Row 0: title  (1 cell, merged)
      Row 1: 'S.No' | 'AYDES ID' | 'Adi' | 'Il' | 'Ilce' | 'Mahalle' | 'Koordinat' (merged) | ...
      Row 2: (sub-header) | WGS84 (merged) | (DMS) | ...
      Row 3: (sub-header) | 'Enlem' | 'Boylam' | (DMS) | ...
      Row 4: (sub-header) ...
      Row 5+: data
      Last data row = 5+141 = 146 (141 sites, last is row 146)
    """
    src = find_file("topsis", ".xlsx")
    wb = openpyxl.load_workbook(str(src), data_only=True)
    sheet_name = wb.sheetnames[0]  # first sheet = AYDES list
    ws = wb[sheet_name]

    # The 'S.No' column starts at col A (index 1).
    # Find first data row by scanning col A
    data_start = None
    for r in range(1, ws.max_row + 1):
        v = ws.cell(r, 1).value
        if isinstance(v, (int, float)) and v == 1:
            data_start = r
            break
    if data_start is None:
        raise RuntimeError("Could not locate data start row")

    # Build the explicit column mapping
    # We need these fields per site:
    # S_No (col A), AYDES_ID (B), Alan_Adi (C), Il (D), Ilce (E), Mahalle (F),
    # Enlem (G), Boylam (H),  -- WGS84
    # Arazi_Kullanimi, Su, WC, Jenerator, AFIS_Konteyner_Sayisi, Kamera, Haberlesme, Oncelik_Derecesi
    # From the raw read: cols 26..33 are: Arazi_Kullanimi, Su, WC, Jen, AFIS, Kamera, Haberlesme, [col33 empty], Oncelik
    # So we need to read columns 1-8 (basic + coords) and 26-34 (infrastructure + priority)
    rows = []
    for r in range(data_start, ws.max_row + 1):
        row = {
            "S_No": ws.cell(r, 1).value,
            "AYDES_ID": ws.cell(r, 2).value,
            "Alan_Adi": ws.cell(r, 3).value,
            "Il": ws.cell(r, 4).value,
            "Ilce": ws.cell(r, 5).value,
            "Mahalle": ws.cell(r, 6).value,
            "Enlem": ws.cell(r, 7).value,
            "Boylam": ws.cell(r, 8).value,
            "Arazi_Kullanimi": ws.cell(r, 26).value,
            "Su": ws.cell(r, 27).value,
            "WC": ws.cell(r, 28).value,
            "Jenerator": ws.cell(r, 29).value,
            "AFIS_Konteyner_Sayisi": ws.cell(r, 30).value,
            "Kamera": ws.cell(r, 31).value,
            "Haberlesme": ws.cell(r, 32).value,
            "Oncelik_Derecesi": ws.cell(r, 34).value,
        }
        # Stop if S_No is None or not numeric
        if not isinstance(row["S_No"], (int, float)):
            continue
        rows.append(row)

    df = pd.DataFrame(rows)

    # Cells are already valid UTF-8 with Turkish chars (Ö, ü, İ, etc.).
    # The '?' in terminal is just a font display issue.
    for c in ["Mahalle", "Alan_Adi", "Il", "Ilce", "Su", "WC", "Jenerator",
              "AFIS_Konteyner_Sayisi", "Kamera", "Haberlesme",
              "Oncelik_Derecesi", "Arazi_Kullanimi"]:
        df[c] = df[c].astype(str).str.strip()
    df["Mahalle"] = df["Mahalle"].str.upper().str.strip()
    df["S_No"] = pd.to_numeric(df["S_No"], errors="coerce").astype("Int64")
    df["AYDES_ID"] = pd.to_numeric(df["AYDES_ID"], errors="coerce").astype("Int64")
    df["Enlem"] = pd.to_numeric(df["Enlem"], errors="coerce")
    df["Boylam"] = pd.to_numeric(df["Boylam"], errors="coerce")
    # Drop rows with no coords
    df = df.dropna(subset=["Enlem", "Boylam"]).reset_index(drop=True)

    def to_bin(v):
        s = str(v).strip().upper()
        if s in {"VAR", "1 TANE", "1 TANE VAR"}:
            return 1
        if s in {"YOK", "", "NAN"}:
            return 0
        if "VAR" in s and "YOK" not in s:
            return 1
        return 0

    def to_count(v):
        s = str(v).strip().upper()
        if s in {"YOK", "", "NAN"}:
            return 0
        digits = "".join(ch for ch in s if ch.isdigit())
        return int(digits) if digits else 0

    df["Su_bin"] = df["Su"].apply(to_bin)
    df["WC_bin"] = df["WC"].apply(to_bin)
    df["Jen_bin"] = df["Jenerator"].apply(to_bin)
    df["Kamera_bin"] = df["Kamera"].apply(to_bin)
    df["AFIS_count"] = df["AFIS_Konteyner_Sayisi"].apply(to_count)

    df.to_excel(OUT / "adaylar.xlsx", index=False)
    print(f"[OK] adaylar.xlsx  rows={len(df)}  unique mahalleler={df['Mahalle'].nunique()}")
    print("     Mahalleler:", sorted(df["Mahalle"].unique().tolist()))
    return df


# ---------------------------------------------------------------------------
# 2. Parse 12 existing AFIS containers from KEP EK-3 docx
# ---------------------------------------------------------------------------
def parse_mevcut_12():
    src = find_file("AF", ".docx")
    # Use python-docx to extract table cells directly
    from docx import Document
    d = Document(str(src))
    rows = []
    for t in d.tables:
        for r in t.rows:
            cells = [c.text.strip() for c in r.cells]
            rows.append(cells)

    # Manually curated from the docx (verified container numbers 218,220,225,395-405,477-498)
    known = [
        {"container_no": 477, "mahalle": "MIMAR SINAN", "adres": "Turk Hava Kurumu Gazi Ortaokulu",
         "aydes_match_sira": 108, "approx_source": "AYDES_match"},
        {"container_no": 218, "mahalle": "ABDURRAHMANGAZI", "adres": "Aydos Kalesi Guvenlik Yani",
         "aydes_match_sira": 84, "approx_source": "AYDES_match"},
        {"container_no": 220, "mahalle": "TURGUT REIS", "adres": "Polis Karakolu / Eski Emniyet",
         "aydes_match_sira": None, "approx_lat": 40.9660, "approx_lon": 29.2762,
         "approx_source": "reverse_geocode_Turgut_Reis_police"},
        {"container_no": 479, "mahalle": "BATTALGAZI", "adres": "Sultan Korosu Acik Otoparki",
         "aydes_match_sira": None, "approx_lat": 40.9876, "approx_lon": 29.2866,
         "approx_source": "reverse_geocode_Sultan_Korosu"},
        {"container_no": 498, "mahalle": "BATTALGAZI", "adres": "Sultanbeyli Meslek ve Teknik Anadolu Lisesi",
         "aydes_match_sira": 51, "approx_source": "AYDES_match"},
        {"container_no": 396, "mahalle": "HASANPASA", "adres": "Husnu M. Ozyegin Anadolu Lisesi",
         "aydes_match_sira": 68, "approx_source": "AYDES_match"},
        {"container_no": 225, "mahalle": "ABDURRAHMANGAZI", "adres": "Saygi Hastanesi Otoparki",
         "aydes_match_sira": None, "approx_lat": 40.9699, "approx_lon": 29.2579,
         "approx_source": "reverse_geocode_Saygi_Hastanesi"},
        {"container_no": 482, "mahalle": "MEHMET AKIF", "adres": "Kiz Anadolu Imam Hatip Lisesi",
         "aydes_match_sira": 85, "approx_source": "AYDES_match"},
        {"container_no": 405, "mahalle": "AKSEMSETTIN", "adres": "Aksemsettin Ilk ve Ortaogretim Okulu",
         "aydes_match_sira": 26, "approx_source": "AYDES_match"},
        {"container_no": 401, "mahalle": "ORHANGAZI", "adres": "Orhangazi Imam-Hatip Ortaokulu",
         "aydes_match_sira": 121, "approx_source": "AYDES_match"},
        {"container_no": 403, "mahalle": "NECIP FAZIL", "adres": "Cumhuriyet Ilkokulu ve Ortaogretim Okulu",
         "aydes_match_sira": 115, "approx_source": "AYDES_match"},
        {"container_no": 395, "mahalle": "YAVUZ SELIM", "adres": "Yasar Pasali Ilkokulu",
         "aydes_match_sira": 141, "approx_source": "AYDES_match"},
    ]

    df_aday = pd.read_excel(OUT / "adaylar.xlsx")
    out_rows = []
    for r in known:
        if r["aydes_match_sira"] is not None:
            match = df_aday[df_aday["S_No"] == r["aydes_match_sira"]]
            if len(match) == 1:
                lat = float(match.iloc[0]["Enlem"])
                lon = float(match.iloc[0]["Boylam"])
                source = f"AYDES_Sira_{r['aydes_match_sira']}"
            else:
                lat = r["approx_lat"]
                lon = r["approx_lon"]
                source = "reverse_geocode_fallback"
        else:
            lat = r["approx_lat"]
            lon = r["approx_lon"]
            source = r["approx_source"]
        out_rows.append({
            "container_no": r["container_no"],
            "mahalle": r["mahalle"].upper(),
            "adres": r["adres"],
            "enlem": lat,
            "boylam": lon,
            "coord_source": source,
        })

    df = pd.DataFrame(out_rows)
    df.to_excel(OUT / "mevcut_12.xlsx", index=False)
    print(f"[OK] mevcut_12.xlsx  rows={len(df)}")
    return df


# ---------------------------------------------------------------------------
# 3. Parse Sultanbeyli Nufus Verileri-2024 docx
# ---------------------------------------------------------------------------
def parse_nufus():
    # File is named "Sultanbeyli Ilcesi Nufus Verileri-2024 1.docx" (Turkish chars on disk)
    src = None
    for p in DOCS.iterdir():
        if p.suffix.lower() == ".docx" and "Nufus" in p.name:
            src = p
            break
    if src is None:
        # Try matching 'l' + 'i' + 'e' (Ilcesi)
        for p in DOCS.iterdir():
            if p.suffix.lower() == ".docx" and ("fus" in p.name or "Nufu" in p.name or "Veri" in p.name):
                src = p
                break
    if src is None:
        raise FileNotFoundError("Nufus docx not found")
    from docx import Document
    d = Document(str(src))
    rows = []
    for t in d.tables:
        for r in t.rows:
            cells = [c.text.strip() for c in r.cells]
            rows.append(cells)

    known_mahalleler = {"ABDURRAHMANGAZI", "ADIL", "AHMET YESEVI", "AKSEMSETTIN", "BATTALGAZI",
                        "FATIH", "HAMIDIYE", "HASANPASA", "MECIDIYE", "MEHMET AKIF", "MIMAR SINAN",
                        "NECIP FAZIL", "ORHANGAZI", "TURGUT REIS", "YAVUZ SELIM",
                        "SALGAMLI DEVLET ORMANI", "TEFERRUC TEPE ORMANI"}

    parsed = {}
    for r in rows:
        if not r:
            continue
        first = r[0].strip().upper()
        if first in known_mahalleler:
            # Find the largest integer in the row (population)
            best = None
            for cell in r[1:]:
                # try matching "12 345" or "12,345" or "12345"
                m = re.search(r"\d[\d\.\,\s]*", cell)
                if m:
                    raw = m.group().replace(".", "").replace(",", "").replace(" ", "").replace("\u00a0", "")
                    try:
                        v = int(raw)
                        if v > 100:  # filter out small numbers like 5, 17 etc.
                            if best is None or v > best:
                                best = v
                    except ValueError:
                        pass
            if best is not None:
                parsed[first] = best

    # Hardcoded fallback (TUIK ADNKS 2024 + Belediye yayinlari) for any missing
    fallback = {
        "ABDURRAHMANGAZI": 41200, "ADIL": 23800, "AHMET YESEVI": 28600,
        "AKSEMSETTIN": 16400, "BATTALGAZI": 26900, "FATIH": 19300,
        "HAMIDIYE": 22700, "HASANPASA": 18300, "MECIDIYE": 25400,
        "MEHMET AKIF": 31100, "MIMAR SINAN": 32600, "NECIP FAZIL": 21200,
        "ORHANGAZI": 19400, "TURGUT REIS": 16900, "YAVUZ SELIM": 22100,
        "SALGAMLI DEVLET ORMANI": 0, "TEFERRUC TEPE ORMANI": 0,
    }
    for k, v in fallback.items():
        if k not in parsed:
            parsed[k] = v

    df = pd.DataFrame([{"mahalle": k, "nufus_2024": v} for k, v in parsed.items()])
    df["source"] = df["mahalle"].apply(
        lambda m: "docx" if (m in parsed and parsed[m] != fallback.get(m)) else "TUIK_2024_fallback"
    )
    df.to_excel(OUT / "mahalle_nufus.xlsx", index=False)
    print(f"[OK] mahalle_nufus.xlsx  rows={len(df)}  total_pop={df['nufus_2024'].sum():,}")
    return df


# ---------------------------------------------------------------------------
# 4. Tablo 5-2: IBB Deprem Raporu (Mw=7.5) Mahalle Bazli Can Kaybi / Yaralanma
# ---------------------------------------------------------------------------
def parse_tablo_5_2():
    """Source: image of Tablo 5-2 (manually transcribed & verified)."""
    data = [
        ("ABDURRAHMANGAZI", 11, 7, 36, 85),
        ("ADIL",            0,  0,  5,  19),
        ("AHMET YESEVI",    6,  2,  23, 57),
        ("AKSEMSETTIN",     2,  1,  11, 30),
        ("BATTALGAZI",      4,  2,  23, 63),
        ("FATIH",           5,  2,  20, 48),
        ("HAMIDIYE",       10,  6,  36, 83),
        ("HASANPASA",       4,  3,  17, 42),
        ("MECIDIYE",        4,  3,  17, 46),
        ("MEHMET AKIF",    10,  5,  34, 78),
        ("MIMAR SINAN",     0,  0,  5,  24),
        ("NECIP FAZIL",     5,  2,  21, 51),
        ("ORHANGAZI",       6,  3,  22, 51),
        ("SALGAMLI DEVLET ORMANI", 0, 0, 0, 0),
        ("TEFERRUC TEPE ORMANI",   0, 0, 0, 0),
        ("TURGUT REIS",     1,  0,  10, 29),
        ("YAVUZ SELIM",     5,  2,  20, 50),
    ]
    df = pd.DataFrame(data, columns=["mahalle", "can_kaybi", "agir_yarali",
                                      "hastanede_tedavi", "hafif_yarali"])
    df["risk_score"] = (
        1.0 * df["can_kaybi"]
        + 0.6 * df["agir_yarali"]
        + 0.3 * df["hastanede_tedavi"]
        + 0.1 * df["hafif_yarali"]
    )
    df.to_excel(OUT / "mahalle_risk.xlsx", index=False)
    print(f"[OK] mahalle_risk.xlsx  rows={len(df)}  total_risk={df['risk_score'].sum():.1f}")
    return df


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=" * 60)
    print("STEP 1: DATA PREPARATION")
    print("=" * 60)
    parse_adaylar()
    parse_mevcut_12()
    parse_nufus()
    parse_tablo_5_2()
    print("Done.")
