import pandas as pd
files = [
    r'D:\IE492\archive\cozum_alternatifi_2_road_closure\results\ahp_weights_CA2.xlsx',
    r'D:\IE492\archive\cozum_alternatifi_7_risk_proportional_coverage\data\ahp_weights.xlsx',
    r'D:\IE492\archive\cozum_alternatifi_9a_min_one_per_mahalle\data\ahp_weights.xlsx',
]
for f in files:
    df = pd.read_excel(f)
    name = f.split('\\')[-3]
    print(f'=== {name} ===')
    print('cols:', list(df.columns))
    print(df.head(3).to_string())
    print()
