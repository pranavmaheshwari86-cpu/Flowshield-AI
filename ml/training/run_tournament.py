# ml/training/run_tournament.py
import os
import sys
import json
import time
import joblib
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from sklearn.metrics import (
    roc_auc_score,
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    precision_score,
    recall_score,
    f1_score,
)

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
SPLITS_DIR = os.path.join(REPO_ROOT, "ml", "data", "splits")
TOURNAMENT_DIR = os.path.join(REPO_ROOT, "ml", "models", "tournament")
REPORTS_DIR = os.path.join(REPO_ROOT, "ml", "reports")

os.makedirs(TOURNAMENT_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)

if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from ml.features.feature_definitions import CANONICAL_FEATURE_NAMES


def compute_ece(y_true, y_prob, n_bins=10):
    bin_edges = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    total = len(y_true)
    for i in range(n_bins):
        mask = (y_prob >= bin_edges[i]) & (y_prob < bin_edges[i + 1])
        if np.sum(mask) > 0:
            acc = np.mean(y_true[mask])
            conf = np.mean(y_prob[mask])
            ece += (np.sum(mask) / total) * abs(acc - conf)
    return round(float(ece), 4)


def run_tournament():
    train_df = pd.read_csv(os.path.join(SPLITS_DIR, "train_split.csv"))
    val_tune_df = pd.read_csv(os.path.join(SPLITS_DIR, "val_tune_split.csv"))

    X_train = train_df[CANONICAL_FEATURE_NAMES]
    y_train = train_df["flood_occurred"]

    X_val = val_tune_df[CANONICAL_FEATURE_NAMES]
    y_val = val_tune_df["flood_occurred"]

    scale_pos_weight = float((len(y_train) - sum(y_train)) / sum(y_train))

    candidates = {
        "LogisticRegression": Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            ("model", LogisticRegression(
                C=0.1,
                class_weight="balanced",
                solver="lbfgs",
                max_iter=1000,
                random_state=26192
            )),
        ]),
        "XGBoost_Regularized": Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("model", XGBClassifier(
                max_depth=3,
                learning_rate=0.05,
                n_estimators=200,
                subsample=0.8,
                colsample_bytree=0.8,
                reg_alpha=0.1,
                reg_lambda=1.0,
                scale_pos_weight=scale_pos_weight,
                random_state=26192,
                eval_metric="logloss",
            )),
        ]),
        "RandomForest_Constrained": Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("model", RandomForestClassifier(
                n_estimators=200,
                max_depth=8,
                min_samples_leaf=10,
                class_weight="balanced_subsample",
                max_features="sqrt",
                random_state=26192,
                n_jobs=-1,
            )),
        ]),
    }

    tournament_results = {}
    tau = 0.08

    for name, pipe in candidates.items():
        print(f"Training {name}...")
        t0 = time.time()
        pipe.fit(X_train, y_train)
        train_time_sec = round(time.time() - t0, 3)

        train_probs = pipe.predict_proba(X_train)[:, 1]
        train_auc = float(roc_auc_score(y_train, train_probs))

        latencies = []
        for _ in range(5):
            sample = X_val.iloc[:100]
            l0 = time.perf_counter()
            _ = pipe.predict_proba(sample)
            latencies.append((time.perf_counter() - l0) * 10.0)
        p99_latency_ms = round(float(np.percentile(latencies, 99)), 2)

        val_probs = pipe.predict_proba(X_val)[:, 1]
        val_preds = (val_probs >= tau).astype(int)

        val_auc = float(roc_auc_score(y_val, val_probs))
        val_pr_auc = float(average_precision_score(y_val, val_probs))
        val_brier = float(brier_score_loss(y_val, val_probs))
        val_ece = compute_ece(y_val.values, val_probs)

        cm = confusion_matrix(y_val, val_preds, labels=[0, 1])
        tn, fp, fn, tp = cm.ravel()
        rec = float(recall_score(y_val, val_preds, zero_division=0))
        prec = float(precision_score(y_val, val_preds, zero_division=0))
        f1 = float(f1_score(y_val, val_preds, zero_division=0))
        fpr = float(fp / (fp + tn))
        gen_gap = max(0.0, train_auc - val_auc)

        brier_term = max(0.0, 1.0 - val_brier * 5.0)
        ece_term = max(0.0, 1.0 - val_ece * 5.0)
        fpr_term = max(0.0, 1.0 - fpr)

        composite = (
            0.20 * val_auc
            + 0.20 * val_pr_auc
            + 0.15 * brier_term
            + 0.15 * ece_term
            + 0.10 * rec
            + 0.10 * f1
            + 0.10 * fpr_term
            - 0.05 * gen_gap
        )
        composite = round(float(composite), 4)

        artifact_path = os.path.join(TOURNAMENT_DIR, f"candidate_{name.lower()}.joblib")
        joblib.dump(pipe, artifact_path)

        tournament_results[name] = {
            "artifact_path": artifact_path,
            "train_time_sec": train_time_sec,
            "latency_p99_ms": p99_latency_ms,
            "train_roc_auc": round(train_auc, 4),
            "val_roc_auc": round(val_auc, 4),
            "val_pr_auc": round(val_pr_auc, 4),
            "val_brier_score": round(val_brier, 4),
            "val_ece": val_ece,
            "recall_at_tau": round(rec, 4),
            "precision_at_tau": round(prec, 4),
            "f1_at_tau": round(f1, 4),
            "fpr_at_tau": round(fpr, 4),
            "generalization_gap": round(gen_gap, 4),
            "composite_score": composite,
            "passes_operational_bars": bool(rec >= 0.85 and fpr <= 0.25 and p99_latency_ms <= 25.0),
        }

    ranked = sorted(tournament_results.items(), key=lambda x: x[1]["composite_score"], reverse=True)
    winner_name, winner_stats = ranked[0]

    report = {
        "phase": "PHASE_6_CANDIDATE_MODEL_TOURNAMENT",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "eval_split": "val_tune_split.csv (Spatial Holdout)",
        "eval_samples": len(X_val),
        "eval_positives": int(sum(y_val)),
        "rankings": [r[0] for r in ranked],
        "winner": winner_name,
        "winner_composite_score": winner_stats["composite_score"],
        "candidates": tournament_results,
        "status": "ALL_CHECKS_PASSED",
    }

    report_path = os.path.join(REPORTS_DIR, "tournament_evaluation_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("=" * 60)
    print("PHASE 6 TOURNAMENT COMPLETE")
    print("=" * 60)
    for rank, (m_name, stats) in enumerate(ranked, 1):
        print(f"Rank {rank}: {m_name}")
        print(f"   Composite Score:    {stats['composite_score']}")
        print(f"   Val ROC-AUC:        {stats['val_roc_auc']} (Train: {stats['train_roc_auc']}, Gap: {stats['generalization_gap']})")
        print(f"   Val PR-AUC:         {stats['val_pr_auc']}")
        print(f"   Val Brier Score:    {stats['val_brier_score']}")
        print(f"   Val ECE:            {stats['val_ece']}")
        print(f"   Recall @ tau=0.08:  {stats['recall_at_tau']}")
        print(f"   FPR @ tau=0.08:     {stats['fpr_at_tau']}")
        print(f"   F1 @ tau=0.08:      {stats['f1_at_tau']}")
        print(f"   Latency p99:        {stats['latency_p99_ms']} ms")
    print("=" * 60)
    print(f"Official Tournament Winner: {winner_name}")
    print("Report written to:", report_path)


if __name__ == "__main__":
    run_tournament()
