import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler,OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import precision_score,recall_score,f1_score,confusion_matrix,roc_auc_score,average_precision_score
import joblib

DATA_PATH="../06_ML_Dataset/terrapulse_improved_ml_dataset_2020_2023.csv"

df=pd.read_csv(DATA_PATH)
df["date"]=pd.to_datetime(df["date"])

train_df=df[df["date"].dt.year<=2021].copy()
val_df=df[df["date"].dt.year==2022].copy()
test_df=df[df["date"].dt.year==2023].copy()

features=[
    "rainfall_1d","rainfall_3d","rainfall_7d","rainfall_14d",
    "rainfall_30d","rainfall_max_3d","rainfall_max_7d",
    "rainy_days_7d","rainfall_1d_to_7d","rainfall_3d_to_7d",
    "soil_moisture","mean_elevation","mean_slope","district"
]

target="flood_label"

numeric_features=[
    "rainfall_1d","rainfall_3d","rainfall_7d","rainfall_14d",
    "rainfall_30d","rainfall_max_3d","rainfall_max_7d",
    "rainy_days_7d","rainfall_1d_to_7d","rainfall_3d_to_7d",
    "soil_moisture","mean_elevation","mean_slope"
]

categorical_features=["district"]

X_train=train_df[features]
y_train=train_df[target]
X_val=val_df[features]
y_val=val_df[target]
X_test=test_df[features]
y_test=test_df[target]

def create_model():
    preprocessor=ColumnTransformer([
        ("num",StandardScaler(),numeric_features),
        ("cat",OneHotEncoder(handle_unknown="ignore"),categorical_features)
    ])
    return Pipeline([
        ("preprocessor",preprocessor),
        ("classifier",LogisticRegression(
            class_weight="balanced",
            max_iter=2000,
            random_state=42
        ))
    ])

model=create_model()
model.fit(X_train,y_train)

val_prob=model.predict_proba(X_val)[:,1]

thresholds=[
    0.05,0.10,0.15,0.20,0.25,0.30,0.35,0.40,0.45,0.50,
    0.55,0.60,0.65,0.70,0.75,0.80,0.85,0.90,0.95
]

results=[]

print("\n2022 VALIDATION RESULTS")
print("-"*75)
print("Threshold | Precision | Recall | F1 | TP | FP | FN")

for threshold in thresholds:
    val_pred=(val_prob>=threshold).astype(int)
    tn,fp,fn,tp=confusion_matrix(y_val,val_pred,labels=[0,1]).ravel()
    precision=precision_score(y_val,val_pred,zero_division=0)
    recall=recall_score(y_val,val_pred,zero_division=0)
    f1=f1_score(y_val,val_pred,zero_division=0)
    results.append((threshold,precision,recall,f1,tp,fp,fn))
    print(f"{threshold:9.2f} | {precision:9.4f} | {recall:6.4f} | {f1:6.4f} | {tp:2d} | {fp:3d} | {fn:2d}")

best=max(results,key=lambda x:(x[3],x[2],x[1]))
best_threshold=best[0]

print("\nSelected threshold:",best_threshold)
print("Validation F1:",round(best[3],4))

final_model=create_model()
final_model.fit(
    pd.concat([X_train,X_val]),
    pd.concat([y_train,y_val])
)

test_prob=final_model.predict_proba(X_test)[:,1]
test_pred=(test_prob>=best_threshold).astype(int)

tn,fp,fn,tp=confusion_matrix(
    y_test,test_pred,labels=[0,1]
).ravel()

precision=precision_score(y_test,test_pred,zero_division=0)
recall=recall_score(y_test,test_pred,zero_division=0)
f1=f1_score(y_test,test_pred,zero_division=0)
roc_auc=roc_auc_score(y_test,test_prob)
pr_auc=average_precision_score(y_test,test_prob)

print("\n2023 FINAL TEST RESULTS")
print("-"*40)
print("Threshold:",best_threshold)
print("TN:",tn)
print("FP:",fp)
print("FN:",fn)
print("TP:",tp)
print("Precision:",round(precision,4))
print("Recall:",round(recall,4))
print("F1:",round(f1,4))
print("ROC-AUC:",round(roc_auc,4))
print("PR-AUC:",round(pr_auc,4))

joblib.dump(final_model,"improved_logistic_tuned.joblib")

with open("improved_logistic_threshold.txt","w") as f:
    f.write(str(best_threshold))

print("\nSaved:")
print("improved_logistic_tuned.joblib")
print("improved_logistic_threshold.txt")