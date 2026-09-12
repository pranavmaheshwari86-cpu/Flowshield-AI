import pandas as pd
import numpy as np

RAINFALL_PATH="../05_Features/rainfall_district_daily_2020_2023.csv"
SOIL_PATH="../05_Features/soil_moisture_features_2020_2023.csv"
TERRAIN_PATH="../05_Features/terrain_features_uttarakhand.csv"
LABEL_PATH="../05_Features/flood_labels_2020_2023.csv"
OUTPUT_PATH="terrapulse_improved_ml_dataset_2020_2023.csv"

rainfall=pd.read_csv(RAINFALL_PATH)
soil=pd.read_csv(SOIL_PATH)
terrain=pd.read_csv(TERRAIN_PATH)
labels=pd.read_csv(LABEL_PATH)

for df in [rainfall,soil,labels]:
    df["date"]=pd.to_datetime(df["date"])

rainfall=rainfall.sort_values(["district","date"]).copy()

group=rainfall.groupby("district")["rainfall_mm"]

rainfall["rainfall_1d"]=rainfall["rainfall_mm"]
rainfall["rainfall_3d"]=group.transform(lambda x:x.rolling(3).sum())
rainfall["rainfall_7d"]=group.transform(lambda x:x.rolling(7).sum())
rainfall["rainfall_14d"]=group.transform(lambda x:x.rolling(14).sum())
rainfall["rainfall_30d"]=group.transform(lambda x:x.rolling(30).sum())

rainfall["rainfall_max_3d"]=group.transform(lambda x:x.rolling(3).max())
rainfall["rainfall_max_7d"]=group.transform(lambda x:x.rolling(7).max())

rainfall["rainy_days_7d"]=group.transform(lambda x:x.rolling(7).apply(lambda y:(y>1).sum(),raw=True))

rainfall["rainfall_1d_to_7d"]=rainfall["rainfall_1d"]/(rainfall["rainfall_7d"]+1e-6)
rainfall["rainfall_3d_to_7d"]=rainfall["rainfall_3d"]/(rainfall["rainfall_7d"]+1e-6)

rainfall=rainfall.drop(columns=["rainfall_mm"])

df=rainfall.merge(soil,on=["date"],how="left")
df=df.merge(terrain,on=["district"],how="left")
df=df.merge(labels,on=["date","district"],how="left")

df=df.sort_values(["date","district"]).reset_index(drop=True)

feature_columns=[
    "rainfall_1d",
    "rainfall_3d",
    "rainfall_7d",
    "rainfall_14d",
    "rainfall_30d",
    "rainfall_max_3d",
    "rainfall_max_7d",
    "rainy_days_7d",
    "rainfall_1d_to_7d",
    "rainfall_3d_to_7d",
    "soil_moisture",
    "mean_elevation",
    "mean_slope",
    "flood_label"
]

df=df[["date","district"]+feature_columns]

df=df.dropna(subset=feature_columns)

df.to_csv(OUTPUT_PATH,index=False)

print("\nIMPROVED ML DATASET CREATED")
print("-"*40)
print("Rows:",len(df))
print("Columns:",len(df.columns))
print("Date range:",df["date"].min().date(),"to",df["date"].max().date())
print("Districts:",df["district"].nunique())
print("Missing values:",int(df.isna().sum().sum()))
print("Duplicate date-district:",int(df.duplicated(["date","district"]).sum()))
print("Flood labels:")
print(df["flood_label"].value_counts().sort_index())
print("\nColumns:")
print(df.columns.tolist())
print("\nSaved:",OUTPUT_PATH)