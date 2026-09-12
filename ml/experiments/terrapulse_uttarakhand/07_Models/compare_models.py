import pandas as pd
import os

results=[
    {
        "model":"Original Logistic Regression",
        "feature_set":"Original",
        "threshold":0.65,
        "TP":26,
        "FP":817,
        "FN":29,
        "precision":0.0308,
        "recall":0.4727,
        "F1":0.0579,
        "ROC_AUC":0.7509,
        "PR_AUC":0.0460
    },
    {
        "model":"Original Random Forest",
        "feature_set":"Original",
        "threshold":0.05,
        "TP":7,
        "FP":232,
        "FN":48,
        "precision":0.0293,
        "recall":0.1273,
        "F1":0.0476,
        "ROC_AUC":0.6551,
        "PR_AUC":0.0237
    },
    {
        "model":"Improved Logistic Regression",
        "feature_set":"Improved Rainfall Features",
        "threshold":0.65,
        "TP":30,
        "FP":867,
        "FN":25,
        "precision":0.0334,
        "recall":0.5455,
        "F1":0.0630,
        "ROC_AUC":0.7914,
        "PR_AUC":0.0400
    },
    {
        "model":"Improved Random Forest",
        "feature_set":"Improved Rainfall Features",
        "threshold":0.01,
        "TP":26,
        "FP":635,
        "FN":29,
        "precision":0.0393,
        "recall":0.4727,
        "F1":0.0726,
        "ROC_AUC":0.7619,
        "PR_AUC":0.0374
    }
]

df=pd.DataFrame(results)

os.makedirs("../08_Reports",exist_ok=True)

output_path="../08_Reports/model_comparison.csv"
df.to_csv(output_path,index=False)

print("\nTERRAPULSE MODEL COMPARISON")
print("="*90)
print(df.to_string(index=False))

best_f1=df.loc[df["F1"].idxmax()]
best_recall=df.loc[df["recall"].idxmax()]
best_auc=df.loc[df["ROC_AUC"].idxmax()]
best_precision=df.loc[df["precision"].idxmax()]

print("\nBEST BY F1")
print(best_f1["model"],"->",best_f1["F1"])

print("\nBEST BY RECALL")
print(best_recall["model"],"->",best_recall["recall"])

print("\nBEST BY ROC-AUC")
print(best_auc["model"],"->",best_auc["ROC_AUC"])

print("\nBEST BY PRECISION")
print(best_precision["model"],"->",best_precision["precision"])

print("\nSaved:",output_path)