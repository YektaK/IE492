import sys
from pathlib import Path
import json
import pandas as pd
from fpdf import FPDF

# Proje yollarını ekle
sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import MODELS_DIR, RESULTS_DIR

def to_ascii(s):
    """Türkçe karakterleri Latin-1 destekli karakterlere dönüştürür."""
    if not isinstance(s, str):
        return str(s)
    tr = str.maketrans({
        "ç": "c", "ğ": "g", "ı": "i", "ö": "o", "ş": "s", "ü": "u",
        "Ç": "C", "Ğ": "G", "İ": "I", "Ö": "O", "Ş": "S", "Ü": "U",
        "â": "a", "î": "i", "û": "u"
    })
    return s.translate(tr)

class DisasterReportPDF(FPDF):
    def header(self):
        # Başlık ve logo alanı
        self.set_fill_color(14, 17, 23) # Koyu tema başlık bandı
        self.rect(0, 0, 210, 40, 'F')
        
        self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", "B", 16)
        self.cell(0, 10, "SULTANBEYLI AFET KONTEYNER OPTIMIZASYONU", align='C', new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "I", 10)
        self.cell(0, 5, "Optimizasyon ve Karar Destek Sistemi Raporu", align='C', new_x="LMARGIN", new_y="NEXT")
        self.ln(15)

    def footer(self):
        # Sayfa numarası
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f"Sayfa {self.page_no()}/{{nb}} | Sultanbeyli Master Plan 2026", align='C')

def generate_pdf_report(metadata_path: Path, output_pdf_path: Path):
    """Verilen metadata JSON dosyasından PDF raporu oluşturur."""
    with open(metadata_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    p = data["parameters"]
    f_info = data["files"]
    
    pdf = DisasterReportPDF()
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.set_font("Helvetica", size=10)
    pdf.set_text_color(30, 30, 30)
    
    # 1. PARAMETRELER BÖLÜMÜ
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, "1. Deney ve Model Parametreleri", new_x="LMARGIN", new_y="NEXT")
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(2)
    
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(90, 8, to_ascii(f"Model Tipi: {p.get('model_label', 'IP Modeli')}"), new_x="RIGHT", new_y="TOP")
    pdf.cell(90, 8, to_ascii(f"Toplam Konteyner Butcesi (K): {p['k_total']}"), new_x="LMARGIN", new_y="NEXT")
    
    pdf.cell(90, 8, to_ascii(f"Optimizasyon Hedefi: {p['weight_type'].upper()}"), new_x="RIGHT", new_y="TOP")
    pdf.cell(90, 8, to_ascii(f"Fuzzy Kapsama Dagilimi (Sigma): {p['sigma']}"), new_x="LMARGIN", new_y="NEXT")
    
    pdf.cell(90, 8, to_ascii(f"MCDA Kalite Agirligi (Beta): {p['beta']}"), new_x="RIGHT", new_y="TOP")
    pdf.cell(90, 8, to_ascii(f"Senaryo Tipi: {p.get('scenario_tag', 'Ekleme')}"), new_x="LMARGIN", new_y="NEXT")
    
    pdf.ln(5)
    
    # 2. METRİKLER VE SONUÇLAR
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, "2. Optimizasyon Metrikleri ve Performans", new_x="LMARGIN", new_y="NEXT")
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(2)
    
    pdf.set_font("Helvetica", "", 10)
    # Excel summary oku
    summary_file = f_info.get("summary_file")
    if summary_file:
        sp = MODELS_DIR / summary_file
        if sp.exists():
            df_s = pd.read_excel(sp)
            for idx, row in df_s.iterrows():
                mcdm_name = row.get("mcdm", "MCDM")
                scen_name = row.get("senaryo", "Senaryo")
                z_val = row.get("Z_total", 0.0)
                rxc_val = row.get("RxC", 0.0)
                min_c = row.get("min_mahalle_cov", 0.0)
                avg_c = row.get("avg_mahalle_cov", 0.0)
                
                pdf.cell(0, 8, to_ascii(f"- {mcdm_name} ({scen_name}) -> Z={z_val:.4f} | RxC={rxc_val:.4f} | Min Cov={min_c:.4f} | Avg Cov={avg_c:.4f}"), new_x="LMARGIN", new_y="NEXT")
        else:
            pdf.cell(0, 8, "Summary Excel dosyasi bulunamadi, metrikler listelenemedi.", new_x="LMARGIN", new_y="NEXT")
    else:
        pdf.cell(0, 8, "Summary dosyasi tanimlanmamis.", new_x="LMARGIN", new_y="NEXT")
        
    pdf.ln(5)
    
    # 3. SEÇİLEN PARSELLER
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, "3. Secilen Konteyner Lokasyonlari", new_x="LMARGIN", new_y="NEXT")
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    
    ip_file = f_info.get("ip_file")
    if ip_file:
        ipp = MODELS_DIR / ip_file
        if ipp.exists():
            df_ip = pd.read_excel(ipp)
            
            # Tablo başlıkları
            pdf.set_font("Helvetica", "B", 9)
            pdf.cell(15, 7, "No", 1, 0, 'C')
            pdf.cell(45, 7, "Mahalle", 1, 0, 'C')
            pdf.cell(65, 7, "Alan Adi", 1, 0, 'C')
            pdf.cell(25, 7, "Enlem", 1, 0, 'C')
            pdf.cell(25, 7, "Boylam", 1, 0, 'C')
            pdf.cell(15, 7, "Skor", 1, 1, 'C')
            
            pdf.set_font("Helvetica", "", 8)
            for idx, row in df_ip.head(15).iterrows(): # İlk 15 satırı göster
                s_no = str(row.get("S_No", idx))
                mah = to_ascii(str(row.get("Mahalle", "")))[:20]
                alan = to_ascii(str(row.get("Alan_Adi", "")))[:30]
                lat = f"{row.get('Enlem', 0.0):.4f}"
                lon = f"{row.get('Boylam', 0.0):.4f}"
                score = f"{row.get('toplam_mu_saglanan', 0.0):.2f}"
                
                pdf.cell(15, 6, s_no, 1, 0, 'C')
                pdf.cell(45, 6, mah, 1, 0, 'L')
                pdf.cell(65, 6, alan, 1, 0, 'L')
                pdf.cell(25, 6, lat, 1, 0, 'C')
                pdf.cell(25, 6, lon, 1, 0, 'C')
                pdf.cell(15, 6, score, 1, 1, 'C')
                
            if len(df_ip) > 15:
                pdf.cell(0, 6, to_ascii(f"...ve {len(df_ip) - 15} adet ek lokasyon daha secildi."), new_x="LMARGIN", new_y="NEXT")
        else:
            pdf.cell(0, 8, "Lokasyon Excel dosyasi bulunamadi.", new_x="LMARGIN", new_y="NEXT")
    else:
         pdf.cell(0, 8, "Lokasyon dosyasi tanimlanmamis.", new_x="LMARGIN", new_y="NEXT")
         
    # PDF'i kaydet
    pdf.output(str(output_pdf_path))
    print(f"[+] PDF raporu kaydedildi: {output_pdf_path}")

if __name__ == "__main__":
    if len(sys.argv) > 2:
        meta_p = Path(sys.argv[1])
        out_pdf = Path(sys.argv[2])
        generate_pdf_report(meta_p, out_pdf)
    else:
        # Test amaçlı en son metadata dosyasını bul
        meta_files = sorted(MODELS_DIR.glob("*_metadata.json"), key=lambda x: x.stat().st_mtime)
        if meta_files:
            latest = meta_files[-1]
            out = RESULTS_DIR / "test_report.pdf"
            generate_pdf_report(latest, out)
        else:
            print("Hic metadata dosyasi bulunamadi. Rapor uretilemedi.")
