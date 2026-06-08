# -*- coding: utf-8 -*-
"""
excel_report_generator.py
Seçilen çözüm için 4 sayfalı zengin içerikli Excel raporu oluşturur.
"""

import json
from pathlib import Path
import pandas as pd
from config import MODELS_DIR, DATA_DIR, norm_mahalle, logger
from app_runner import variant_output_paths

def generate_excel_report(metadata_path: Path, output_excel_path: Path, vname: str, mcdm_sel: str, scen_sel: str):
    """
    Metadata ve varyant seçimlerine bağlı olarak 4 sayfalı detaylı Excel raporunu yazar.
    """
    logger.info(f"Excel Raporu olusturuluyor: {output_excel_path.name}")
    
    # 1. Metadata oku
    with open(metadata_path, "r", encoding="utf-8") as f:
        meta = json.load(f)
        
    p = meta["parameters"]
    
    paths = variant_output_paths(p, MODELS_DIR, vname, mcdm_sel, scen_sel)
    ip_path = paths["ip"]
    cov_path = paths["coverage"]
    summary_path = paths["summary"]
    
    # Sayfa 1: Özet ve Parametreler
    z_val, rxc_val, min_c, avg_c = 0.0, 0.0, 0.0, 0.0
    if summary_path.exists():
        try:
            df_s = pd.read_excel(summary_path)
            row = df_s[(df_s["mcdm"] == mcdm_sel) & (df_s["senaryo"] == scen_sel)]
            if not row.empty:
                z_val = float(row.iloc[0].get("Z_total", 0.0))
                rxc_val = float(row.iloc[0].get("RxC", 0.0))
                min_c = float(row.iloc[0].get("min_mahalle_cov", 0.0))
                avg_c = float(row.iloc[0].get("avg_mahalle_cov", 0.0))
        except Exception as e:
            logger.warning(f"Summary excel okunamadi: {e}")
            
    param_data = {
        "Model Parametresi": [
            "Model Tipi",
            "Toplam Konteyner Bütçesi (K)",
            "Optimizasyon Hedefi",
            "Fuzzy Kapsama Dağılımı (Sigma)",
            "MCDA Kalite Ağırlığı (Beta)",
            "Senaryo Tipi",
            "Çalıştırma Zaman Damgası",
            "Seçilen Varyant"
        ],
        "Değer": [
            p.get("model_label", "IP Modeli"),
            p["k_total"],
            p["weight_type"].upper(),
            p["sigma"],
            p["beta"],
            "Mevcutları Koru + Yeni Ekle" if len(p["kept_mevcut"]) > 0 else "Tümünü Sıfırdan Yerleştir (Serbest)",
            meta.get("timestamp", ""),
            f"{vname.upper()} | {mcdm_sel.upper()} | {scen_sel}"
        ]
    }
    df_params = pd.DataFrame(param_data)
    
    metric_data = {
        "Optimizasyon KPI Metriği": [
            "Amaç Fonksiyonu Değeri (Z_total)",
            "Toplam Fayda Skoru (RxC)",
            "Eşitlik Seviyesi (Minimum Mahalle Kapsaması)",
            "Hizmet Seviyesi (Ortalama Mahalle Kapsaması)"
        ],
        "Değer": [z_val, rxc_val, min_c, avg_c]
    }
    df_metrics = pd.DataFrame(metric_data)
    
    # Sayfa 2: Seçilen Konteyner Lokasyonları
    df_ip = pd.DataFrame()
    if ip_path.exists():
        df_ip = pd.read_excel(ip_path)
        # Sütunları daha temiz başlıklarla düzenleyelim
        rename_cols = {
            "S_No": "Aday Parsel No",
            "Alan_Adi": "Alan Adı / Adresi",
            "Mahalle": "Bulunduğu Mahalle",
            "Enlem": "Enlem (Latitude)",
            "Boylam": "Boylam (Longitude)",
            "toplam_mu_saglanan": "Sağladığı Toplam Bulanık Kapsama",
            "p_access_road": "Erişim Yolu Açık Kalma Olasılığı"
        }
        for c in df_ip.columns:
            if c.startswith("q_"):
                rename_cols[c] = f"MCDM Karar Skoru ({c[2:].upper()})"
        df_ip.rename(columns=rename_cols, inplace=True)
        
    # Sayfa 3: Mahalle Bazlı Kapsama Analizi (Demografilerle birleştirilerek)
    df_cov = pd.DataFrame()
    if cov_path.exists():
        try:
            df_cov = pd.read_excel(cov_path)
            df_nuf = pd.read_excel(DATA_DIR / "mahalle_nufus.xlsx")
            df_risk = pd.read_excel(DATA_DIR / "mahalle_risk.xlsx")
            df_bar = pd.read_excel(DATA_DIR / "mahalle_barinma.xlsx")
            
            df_nuf["mahalle_norm"] = df_nuf["mahalle"].apply(norm_mahalle)
            df_risk["mahalle_norm"] = df_risk["mahalle"].apply(norm_mahalle)
            df_bar["mahalle_norm"] = df_bar["mahalle"].apply(norm_mahalle)
            df_cov["mahalle_norm"] = df_cov["mahalle"].apply(norm_mahalle)
            
            df_cov = df_cov.merge(df_nuf[["mahalle_norm", "nufus_2024"]], on="mahalle_norm", how="left")
            df_cov = df_cov.merge(df_risk[["mahalle_norm", "risk_score"]], on="mahalle_norm", how="left")
            df_cov = df_cov.merge(df_bar[["mahalle_norm", "hane_ihtiyaci"]], on="mahalle_norm", how="left")
            
            df_cov.drop(columns=["mahalle_norm"], inplace=True)
            df_cov.rename(columns={
                "mahalle": "Mahalle Adı",
                "mu_mevcut_toplam": "Mevcut Konteyner Kapsaması",
                "yeni_kapsama": "Yeni Konteyner Kapsaması",
                "toplam_kapsama": "Toplam Kapsama Oranı (Hizmet Seviyesi)",
                "nufus_2024": "Gece Nüfusu (2024)",
                "risk_score": "Deprem Risk Skoru (İBB)",
                "hane_ihtiyaci": "Barınma İhtiyacı (Hane Sayısı)"
            }, inplace=True)
        except Exception as e:
            logger.warning(f"Mahalle demografik birlesim hatasi: {e}")
            if not df_cov.empty:
                df_cov.rename(columns={
                    "mahalle": "Mahalle Adı",
                    "mu_mevcut_toplam": "Mevcut Konteyner Kapsaması",
                    "yeni_kapsama": "Yeni Konteyner Kapsaması",
                    "toplam_kapsama": "Toplam Kapsama Oranı"
                }, inplace=True)
                
    # Sayfa 4: Tüm 12 MCDM Varyant Karşılaştırması
    df_all_s = pd.DataFrame()
    if summary_path.exists():
        try:
            df_all_s = pd.read_excel(summary_path)
            df_all_s.rename(columns={
                "vname": "Varyant Kodu",
                "mcdm": "MCDM Karar Yöntemi",
                "senaryo": "MCDM Ağırlık Senaryosu",
                "Z_total": "Amaç Değeri (Z_total)",
                "RxC": "Toplam Fayda (RxC)",
                "min_mahalle_cov": "Minimum Kapsama (Eşitlik)",
                "avg_mahalle_cov": "Ortalama Kapsama (Hizmet Seviyesi)"
            }, inplace=True)
        except Exception as e:
            logger.warning(f"Summary tablosu okunamadi: {e}")
            
    # ExcelWriter ile dosyayı oluştur ve sayfaları yaz
    with pd.ExcelWriter(output_excel_path, engine="openpyxl") as writer:
        df_params.to_excel(writer, sheet_name="Özet ve Parametreler", index=False)
        df_metrics.to_excel(writer, sheet_name="Özet ve Parametreler", startrow=len(df_params) + 3, index=False)
        
        if not df_ip.empty:
            df_ip.to_excel(writer, sheet_name="Seçilen Parseller", index=False)
        if not df_cov.empty:
            df_cov.to_excel(writer, sheet_name="Mahalle Kapsama Analizi", index=False)
        if not df_all_s.empty:
            df_all_s.to_excel(writer, sheet_name="Tüm Varyant Karşılaştırması", index=False)
            
    logger.info(f"Excel Raporu başarıyla oluşturuldu: {output_excel_path}")
