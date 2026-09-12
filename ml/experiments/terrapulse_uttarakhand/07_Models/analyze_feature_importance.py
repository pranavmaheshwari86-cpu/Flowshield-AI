import pandas as pd
import joblib
import os

DATA_PATH="../06_ML_Dataset/terrapulse_improved_ml_dataset_2020_2023.csv"
RF_MODEL="improved_random_forest_tuned.joblib"
LR_MODEL="improved_logistic_tuned.joblib"

os.makedirs("../08_Reports",exist_ok=True)

df=pd.read_csv(DATA_PATH)

features=[
    "rainfall_1d","rainfall_3d","rainfall_7d","rainfall_14d",
    "rainfall_30d","rainfall_max_3d","rainfall_max_7d",
    "rainy_days_7d","rainfall_1d_to_7d","rainfall_3d_to_7d",
    "soil_moisture","mean_elevation","mean_slope","district"
]

numeric_features=[
    "rainfall_1d","rainfall_3d","rainfall_7d","rainfall_14d",
    "rainfall_30d","rainfall_max_3d","rainfall_max_7d",
    "rainy_days_7d","rainfall_1d_to_7d","rainfall_3d_to_7d",
    "soil_moisture","mean_elevation","mean_slope"
]

categorical_features=["district"]

X=df[features]

rf=joblib.load(RF_MODEL)

rf_preprocessor=rf.named_steps["preprocessor"]
rf_classifier=rf.named_steps["classifier"]

encoded_names=rf_preprocessor.get_feature_names_out()

rf_importance=pd.DataFrame({
    "feature":encoded_names,
    "importance":rf_classifier.feature_importances_
})

rf_importance["feature"]=rf_importance["feature"].str.replace("num__","",regex=False)
rf_importance["feature"]=rf_importance["feature"].str.replace("cat__district_","district_",regex=False)

rf_importance=rf_importance.sort_values(
    "importance",
    ascending=False
).reset_index(drop=True)

rf_importance.to_csv(
    "../08_Reports/random_forest_feature_importance.csv",
    index=False
)

lr=joblib.load(LR_MODEL)

lr_preprocessor=lr.named_steps["preprocessor"]
lr_classifier=lr.named_steps["classifier"]

lr_encoded_names=lr_preprocessor.get_feature_names_out()
lr_coefficients=lr_classifier.coef_[0]

lr_importance=pd.DataFrame({
    "feature":lr_encoded_names,
    "coefficient":lr_coefficients,
    "absolute_coefficient":abs(lr_coefficients)
})

lr_importance["feature"]=lr_importance["feature"].str.replace("num__","",regex=False)
lr_importance["feature"]=lr_importance["feature"].str.replace("cat__district_","district_",regex=False)

lr_importance=lr_importance.sort_values(
    "absolute_coefficient",
    ascending=False
).reset_index(drop=True)

lr_importance.to_csv(
    "../08_Reports/logistic_regression_feature_importance.csv",
    index=False
)

print("\nRANDOM FOREST FEATURE IMPORTANCE")
print("-"*45)
print(rf_importance.head(15).to_string(index=False))

print("\nLOGISTIC REGRESSION FEATURE IMPORTANCE")
print("-"*45)
print(lr_importance.head(15).to_string(index=False))

print("\nSaved:")
print("../08_Reports/random_forest_feature_importance.csv")
print("../08_Reports/logistic_regression_feature_importance.csv")