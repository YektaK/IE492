import pandas as pd
from pathlib import Path

DATA_DIR = Path("d:/IE492/data/processed")
nuf = pd.read_excel(DATA_DIR / "mahalle_nufus.xlsx")
print("Dataset Neighborhood Names:")
print(nuf["mahalle"].tolist())
