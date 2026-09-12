import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import yaml
from ml.pipeline.feature_engineering import engineer_features
from ml.pipeline.independent_labeler import independent_labeler

raw_path = Path('ml/data/raw/rainfall/mandi_era5_hourly_raw.csv')
if not raw_path.exists():
    raw_path = Path('data/real/mandi_era5_hourly_raw.csv')

df_raw = pd.read_csv(raw_path)
df_raw['datetime_utc'] = pd.to_datetime(df_raw['time'], utc=True)

with open('ml/configs/regions/himachal_pradesh.yaml', 'r', encoding='utf-8') as f:
    cfg = yaml.safe_load(f)

feats = engineer_features(df_raw)
labeled = independent_labeler.label_station_forecasting(feats, region_slug='himachal_pradesh', region_config=cfg, lead_hours=6)

out_dir = Path('ml/data/processed/himachal_pradesh')
out_dir.mkdir(parents=True, exist_ok=True)
out_csv = out_dir / 'himachal_pradesh_processed_dataset.csv'
labeled.to_csv(out_csv, index=False)
print(f"Saved HP processed dataset: {len(labeled)} rows, {labeled['flood_occurred'].sum()} flood hours to {out_csv}")
print(labeled.groupby(labeled['datetime_utc'].dt.strftime('%Y-%m'))['flood_occurred'].value_counts())
