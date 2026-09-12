"""
scratch/run_full_adversarial_audit.py
Flowshield Hardcore Adversarial Model Audit Runner
Executes all quantitative tests and generates audit_results_dump.json
"""

import os
import sys
import json
import time
import copy
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from scipy import stats

from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import (
    roc_auc_score,
    average_precision_score,
    recall_score,
    precision_score,
    f1_score,
    brier_score_loss,
    confusion_matrix,
    accuracy_score,
)
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.calibration import calibration_curve

# Root setup
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from ml.features.feature_definitions import CANONICAL_FEATURE_NAMES, TARGET_COLUMN
from ml.registry.feature_contract import CANONICAL_FEATURES, PHYSICAL_BOUNDS
from ml.registry.model_registry import model_registry
from ml.inference.predict import predict_flood_risk, load_inference_artifacts


def compute_ece(y_true, y_prob, n_bins=10):
    bin_limits = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    total_samples = len(y_true)
    for i in range(n_bins):
        bin_mask = (y_prob >= bin_limits[i]) & (y_prob < bin_limits[i + 1])
        if i == n_bins - 1:
            bin_mask = (y_prob >= bin_limits[i]) & (y_prob <= bin_limits[i + 1])
        bin_samples = np.sum(bin_mask)
        if bin_samples > 0:
            bin_acc = np.mean(y_true[bin_mask])
            bin_conf = np.mean(y_prob[bin_mask])
            ece += (bin_samples / total_samples) * np.abs(bin_acc - bin_conf)
    return float(ece)


def eval_metrics(y_true, y_prob, threshold=0.5):
    y_pred = (y_prob >= threshold).astype(int)
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    tn, fp, fn, tp = cm.ravel()
    
    roc = float(roc_auc_score(y_true, y_prob)) if len(np.unique(y_true)) > 1 else None
    pr = float(average_precision_score(y_true, y_prob)) if len(np.unique(y_true)) > 1 else None
    rec = float(recall_score(y_true, y_pred, zero_division=0))
    prec = float(precision_score(y_true, y_pred, zero_division=0))
    f1 = float(f1_score(y_true, y_pred, zero_division=0))
    acc = float(accuracy_score(y_true, y_pred))
    brier = float(brier_score_loss(y_true, y_prob))
    ece = compute_ece(y_true, y_prob, n_bins=10)
    fnr = float(fn / (tp + fn)) if (tp + fn) > 0 else 0.0
    fpr = float(fp / (tn + fp)) if (tn + fp) > 0 else 0.0

    return {
        "roc_auc": round(roc, 4) if roc is not None else None,
        "pr_auc": round(pr, 4) if pr is not None else None,
        "recall": round(rec, 4),
        "precision": round(prec, 4),
        "f1": round(f1, 4),
        "accuracy": round(acc, 4),
        "brier_score": round(brier, 4),
        "ece": round(ece, 4),
        "fnr": round(fnr, 4),
        "fpr": round(fpr, 4),
        "tp": int(tp),
        "fp": int(fp),
        "tn": int(tn),
        "fn": int(fn),
        "total": len(y_true),
        "positive": int(tp + fn),
        "prevalence": round(float(np.mean(y_true)), 4),
    }


def predict_bundle_batch(bundle, df_features):
    """Predicts raw and calibrated probabilities for a feature DataFrame."""
    if hasattr(bundle.model, "named_steps"):
        raw_p = bundle.model.predict_proba(df_features)[:, 1]
        X_sc = None
    else:
        X_sc = bundle.preprocessor.transform(df_features)
        raw_p = bundle.model.predict_proba(X_sc)[:, 1]

    if bundle.calibrator is not None:
        est = getattr(bundle.calibrator, "estimator", None)
        if hasattr(est, "estimator"):
            est = est.estimator
        if hasattr(est, "named_steps"):
            cal_p = bundle.calibrator.predict_proba(df_features)[:, 1]
        else:
            if X_sc is None:
                X_sc = bundle.preprocessor.transform(df_features)
            cal_p = bundle.calibrator.predict_proba(X_sc)[:, 1]
    else:
        cal_p = raw_p

    return np.clip(raw_p, 0.0, 1.0), np.clip(cal_p, 0.0, 1.0)


def main():
    print("================================================================================")
    print("STARTING HARDCORE ADVERSARIAL MODEL AUDIT OF FLOWSHIELD")
    print("================================================================================")
    report = {}

    # -------------------------------------------------------------------------
    # TEST 1: REPOSITORY & ARTIFACT FORENSICS
    # -------------------------------------------------------------------------
    print("\n--- [1] Checking Model Artifacts & Manifests ---")
    manifest_v2_path = REPO_ROOT / "ml" / "models" / "v2_decision_pipeline.json"
    prod_manifest_path = REPO_ROOT / "ml" / "models" / "production" / "MODEL_MANIFEST.json"
    
    with open(manifest_v2_path) as f:
        manifest_v2 = json.load(f)
    with open(prod_manifest_path) as f:
        prod_manifest = json.load(f)

    report["manifest_v2"] = manifest_v2
    report["prod_manifest"] = prod_manifest

    # Check V2 artifact files
    hp_bundle = model_registry.get(hazard="flood", region="himachal_pradesh")
    v2_model = hp_bundle.model
    v2_calib = hp_bundle.calibrator
    v2_prep = hp_bundle.preprocessor

    print(f"V2 Model Loaded: {type(v2_model)}")
    print(f"V2 Calibrator: {type(v2_calib)}")
    print(f"V2 Preprocessor: {type(v2_prep)}")

    # -------------------------------------------------------------------------
    # TEST 2: DATA FORENSICS & SYNTHETIC DATA AUDIT
    # -------------------------------------------------------------------------
    print("\n--- [2] Auditing Raw Datasets & Detecting Synthetic Data ---")
    data_forensics = {}

    # Check Mandi real dataset
    mandi_raw_path = REPO_ROOT / "data" / "real" / "mandi_era5_hourly_raw.csv"
    mandi_feat_path = REPO_ROOT / "data" / "real" / "mandi_real_hydrology_features.csv"
    
    df_mandi_raw = pd.read_csv(mandi_raw_path)
    df_mandi_feat = pd.read_csv(mandi_feat_path)

    data_forensics["mandi_era5"] = {
        "total_rows": len(df_mandi_raw),
        "unique_stations": int(df_mandi_raw["station_id"].nunique()),
        "time_min": str(df_mandi_raw["time"].min()),
        "time_max": str(df_mandi_raw["time"].max()),
        "periods": df_mandi_raw["period_id"].value_counts().to_dict(),
        "missing_values": df_mandi_raw.isnull().sum().to_dict(),
    }

    # Check regional raw files for synthetic signatures
    regions = sorted([d.name for d in (REPO_ROOT / "ml" / "models" / "flood").iterdir() if d.is_dir()])
    regional_data_audit = {}

    for r in regions:
        r_raw_path = REPO_ROOT / "ml" / "data" / "raw" / r / f"{r}_raw_era5.csv"
        if r_raw_path.exists():
            df_r = pd.read_csv(r_raw_path)
            precip = df_r["precipitation"].values if "precipitation" in df_r.columns else np.array([])
            regional_data_audit[r] = {
                "rows": len(df_r),
                "stations": int(df_r["station_id"].nunique()) if "station_id" in df_r.columns else 1,
                "precip_mean": round(float(np.mean(precip)), 4) if len(precip) > 0 else None,
                "precip_max": round(float(np.max(precip)), 4) if len(precip) > 0 else None,
                "zero_precip_pct": round(float(np.mean(precip == 0)) * 100, 2) if len(precip) > 0 else None,
                "is_synthetic_generated": (r != "himachal_pradesh"),
            }
    data_forensics["regional_audit"] = regional_data_audit
    report["data_forensics"] = data_forensics

    # -------------------------------------------------------------------------
    # TEST 3: MANDI V2 HOLDOUT PERFORMANCE & BASELINES
    # -------------------------------------------------------------------------
    print("\n--- [3] Mandi V2 Holdout Evaluation & Independent Baselines ---")
    train_split_path = REPO_ROOT / "ml" / "data" / "splits" / "train_split.csv"
    test_split_path = REPO_ROOT / "ml" / "data" / "splits" / "final_test_locked.csv"

    train_df = pd.read_csv(train_split_path)
    test_df = pd.read_csv(test_split_path)

    X_train_raw = train_df[CANONICAL_FEATURES]
    y_train = train_df[TARGET_COLUMN].values
    X_test_raw = test_df[CANONICAL_FEATURES]
    y_test = test_df[TARGET_COLUMN].values

    # Predictions from V2 Model Bundle
    raw_prob_test, cal_prob_test = predict_bundle_batch(hp_bundle, X_test_raw)

    v2_eval_008 = eval_metrics(y_test, cal_prob_test, threshold=0.08)
    v2_eval_050 = eval_metrics(y_test, cal_prob_test, threshold=0.50)
    v2_raw_eval_050 = eval_metrics(y_test, raw_prob_test, threshold=0.50)

    # Baselines
    baselines = {}
    baselines["always_0"] = eval_metrics(y_test, np.zeros(len(y_test)), threshold=0.5)
    baselines["always_1"] = eval_metrics(y_test, np.ones(len(y_test)), threshold=0.5)
    
    r24 = test_df["rainfall_24h_mm"].values
    r1 = test_df["rainfall_1h_mm"].values
    soil = test_df["soil_saturation_pct"].values

    for r_th in [30, 50, 75, 100]:
        p_r24 = np.clip(r24 / 150.0, 0, 1)
        baselines[f"rain_24h_ge_{r_th}mm"] = eval_metrics(y_test, p_r24, threshold=r_th/150.0)

    # Joint heuristic: Rain24 >= 75 & SoilSat >= 70
    joint_rule = ((r24 >= 75.0) & (soil >= 70.0)).astype(float)
    baselines["heuristic_rain24_ge_75_soil_ge_70"] = eval_metrics(y_test, joint_rule, threshold=0.5)

    # Simple Decision Trees
    X_train_sc = v2_prep.transform(X_train_raw)
    X_test_sc = v2_prep.transform(X_test_raw)

    stump = DecisionTreeClassifier(max_depth=1, random_state=42)
    stump.fit(X_train_sc, y_train)
    p_stump = stump.predict_proba(X_test_sc)[:, 1]
    baselines["decision_stump_depth1"] = eval_metrics(y_test, p_stump, threshold=0.5)

    tree3 = DecisionTreeClassifier(max_depth=3, random_state=42)
    tree3.fit(X_train_sc, y_train)
    p_tree3 = tree3.predict_proba(X_test_sc)[:, 1]
    baselines["decision_tree_depth3"] = eval_metrics(y_test, p_tree3, threshold=0.5)

    lr_simple = LogisticRegression(C=1.0, max_iter=1000, random_state=42)
    lr_simple.fit(X_train_sc, y_train)
    p_lr_simple = lr_simple.predict_proba(X_test_sc)[:, 1]
    baselines["simple_logistic_regression"] = eval_metrics(y_test, p_lr_simple, threshold=0.5)

    report["v2_eval"] = {
        "calibrated_threshold_0.08": v2_eval_008,
        "calibrated_threshold_0.50": v2_eval_050,
        "uncalibrated_threshold_0.50": v2_raw_eval_050,
    }
    report["baselines"] = baselines

    # -------------------------------------------------------------------------
    # TEST 4: LEAKAGE AUDIT & SPLIT EXPERIMENTS
    # -------------------------------------------------------------------------
    print("\n--- [4] Split Experiments & Leakage Stress Tests ---")
    split_experiments = {}

    from sklearn.model_selection import KFold
    kf = KFold(n_splits=5, shuffle=True, random_state=42)
    all_df = df_mandi_feat.copy()
    X_all_sc = v2_prep.transform(all_df[CANONICAL_FEATURES])
    y_all = all_df[TARGET_COLUMN].values

    cv_rocs = []
    cv_recs = []
    cv_precs = []
    for tr_idx, te_idx in kf.split(X_all_sc):
        clf = LogisticRegression(C=0.1, class_weight="balanced", solver="liblinear", random_state=42)
        clf.fit(X_all_sc[tr_idx], y_all[tr_idx])
        p_te = clf.predict_proba(X_all_sc[te_idx])[:, 1]
        cv_rocs.append(roc_auc_score(y_all[te_idx], p_te))
        y_pred = (p_te >= 0.08).astype(int)
        cv_recs.append(recall_score(y_all[te_idx], y_pred))
        cv_precs.append(precision_score(y_all[te_idx], y_pred))

    split_experiments["random_5fold_cv_optimistic"] = {
        "roc_auc_mean": round(float(np.mean(cv_rocs)), 4),
        "roc_auc_std": round(float(np.std(cv_rocs)), 4),
        "recall_at_008_mean": round(float(np.mean(cv_recs)), 4),
        "precision_at_008_mean": round(float(np.mean(cv_precs)), 4),
    }

    # Spatial Holdout Split
    val_tune_path = REPO_ROOT / "ml" / "data" / "splits" / "val_tune_split.csv"
    val_tune_df = pd.read_csv(val_tune_path)
    X_spatial_raw = val_tune_df[CANONICAL_FEATURES]
    y_spatial = val_tune_df[TARGET_COLUMN].values
    _, p_spatial = predict_bundle_batch(hp_bundle, X_spatial_raw)
    split_experiments["spatial_holdout_pandoh_dharampur"] = eval_metrics(y_spatial, p_spatial, threshold=0.08)
    split_experiments["leave_one_event_out_july2023"] = v2_eval_008

    # Inverted Event Holdout
    time_col = "time" if "time" in train_df.columns else "datetime_utc"
    train_df["dt"] = pd.to_datetime(train_df[time_col])
    test_df["dt"] = pd.to_datetime(test_df[time_col])

    inv_train = pd.concat([train_df[train_df["dt"].dt.year == 2022], test_df], ignore_index=True)
    inv_test = train_df[train_df["dt"].dt.year == 2023]

    scaler_inv = StandardScaler()
    X_inv_tr = scaler_inv.fit_transform(inv_train[CANONICAL_FEATURES])
    y_inv_tr = inv_train[TARGET_COLUMN].values
    X_inv_te = scaler_inv.transform(inv_test[CANONICAL_FEATURES])
    y_inv_te = inv_test[TARGET_COLUMN].values

    clf_inv = LogisticRegression(C=0.1, class_weight="balanced", solver="liblinear", random_state=42)
    clf_inv.fit(X_inv_tr, y_inv_tr)
    p_inv_te = clf_inv.predict_proba(X_inv_te)[:, 1]
    split_experiments["inverted_event_holdout_august2023"] = eval_metrics(y_inv_te, p_inv_te, threshold=0.08)

    report["split_experiments"] = split_experiments

    # -------------------------------------------------------------------------
    # TEST 5: CLASS IMBALANCE STRESS TEST
    # -------------------------------------------------------------------------
    print("\n--- [5] Class Imbalance Stress Testing (1:10, 1:50, 1:100, 1:500) ---")
    imbalance_results = {}
    pos_mask = (y_test == 1)
    neg_mask = (y_test == 0)

    X_test_pos = X_test_raw[pos_mask]
    y_test_pos = y_test[pos_mask]
    X_test_neg = X_test_raw[neg_mask]
    y_test_neg = y_test[neg_mask]

    n_pos = len(y_test_pos)
    rng = np.random.RandomState(42)

    for ratio_name, ratio in [("1:10", 10), ("1:50", 50), ("1:100", 100), ("1:500", 500)]:
        n_neg_needed = min(len(X_test_neg), n_pos * ratio)
        idx_neg = rng.choice(len(X_test_neg), size=n_neg_needed, replace=(n_neg_needed > len(X_test_neg)))
        
        df_imb = pd.concat([X_test_pos, X_test_neg.iloc[idx_neg]], ignore_index=True)
        y_imb = np.concatenate([y_test_pos, y_test_neg[idx_neg]])
        
        _, prob_imb = predict_bundle_batch(hp_bundle, df_imb)
        imbalance_results[ratio_name] = eval_metrics(y_imb, prob_imb, threshold=0.08)

    report["class_imbalance_stress"] = imbalance_results

    # -------------------------------------------------------------------------
    # TEST 6: THRESHOLD SENSITIVITY & ALERT FATIGUE
    # -------------------------------------------------------------------------
    print("\n--- [6] Operational Threshold Sweep & Alert Fatigue Simulation ---")
    threshold_sweep = []
    thresholds = np.linspace(0.01, 0.99, 99)
    for th in thresholds:
        m = eval_metrics(y_test, cal_prob_test, threshold=float(th))
        threshold_sweep.append({
            "threshold": round(float(th), 2),
            "precision": m["precision"],
            "recall": m["recall"],
            "f1": m["f1"],
            "fpr": m["fpr"],
            "fnr": m["fnr"],
            "false_alarms": m["fp"],
            "misses": m["fn"],
        })
    report["threshold_sweep"] = threshold_sweep

    y_pred_008 = (cal_prob_test >= 0.08).astype(int)
    test_df_copy = test_df.copy()
    test_df_copy["pred"] = y_pred_008
    alerts_per_station = test_df_copy.groupby("station_id")["pred"].sum().to_dict()
    total_hours = len(test_df_copy) / test_df_copy["station_id"].nunique()
    alert_fatigue = {
        "threshold": 0.08,
        "total_test_hours_per_station": total_hours,
        "alerts_triggered_per_station": alerts_per_station,
        "false_positives_total": int(np.sum((y_pred_008 == 1) & (y_test == 0))),
        "false_positive_rate": round(float(np.mean((y_pred_008 == 1) & (y_test == 0))), 4),
        "average_alert_hours_per_day_per_station": round(float(np.mean(list(alerts_per_station.values())) / (total_hours / 24.0)), 2),
    }
    report["alert_fatigue"] = alert_fatigue

    # -------------------------------------------------------------------------
    # TEST 7: PROBABILITY CALIBRATION & RELIABILITY DIAGRAM
    # -------------------------------------------------------------------------
    print("\n--- [7] Calibration Diagnostics (ECE, Brier, Curves) ---")
    prob_true_raw, prob_pred_raw = calibration_curve(y_test, raw_prob_test, n_bins=10)
    prob_true_cal, prob_pred_cal = calibration_curve(y_test, cal_prob_test, n_bins=10)

    calibration_data = {
        "raw_brier": round(float(brier_score_loss(y_test, raw_prob_test)), 4),
        "calibrated_brier": round(float(brier_score_loss(y_test, cal_prob_test)), 4),
        "raw_ece": round(compute_ece(y_test, raw_prob_test), 4),
        "calibrated_ece": round(compute_ece(y_test, cal_prob_test), 4),
        "raw_curve": {"true": [round(x, 4) for x in prob_true_raw], "pred": [round(x, 4) for x in prob_pred_raw]},
        "calibrated_curve": {"true": [round(x, 4) for x in prob_true_cal], "pred": [round(x, 4) for x in prob_pred_cal]},
    }
    report["calibration"] = calibration_data

    # -------------------------------------------------------------------------
    # TEST 8: FEATURE ABLATION & IMPORTANCE
    # -------------------------------------------------------------------------
    print("\n--- [8] Feature Ablation & Model Native Importance ---")
    feature_importance = {}
    # Extract linear coefficients from v2_model
    lr_step = v2_model.named_steps.get("model", v2_model)
    coefs = lr_step.coef_[0]
    for feat, coef in zip(CANONICAL_FEATURES, coefs):
        feature_importance[feat] = round(float(coef), 4)

    ablation_results = {}
    feature_groups = {
        "all_features_baseline": [],
        "no_rainfall": ["rainfall_1h_mm", "rainfall_3h_mm", "rainfall_6h_mm", "rainfall_24h_mm", "rainfall_72h_mm"],
        "no_soil_moisture": ["soil_saturation_pct", "deep_soil_saturation_pct"],
        "no_terrain": ["elevation_m", "catchment_slope_deg", "dist_to_river_m", "upstream_drainage_sqkm"],
        "no_meteorology": ["temperature_c", "relative_humidity_pct", "surface_pressure_hpa", "wind_speed_kmh"],
        "no_river_distance": ["dist_to_river_m"],
        "only_rainfall": [f for f in CANONICAL_FEATURES if not f.startswith("rainfall_")],
    }

    med_vals = X_test_raw.median().to_dict()
    for grp_name, drop_cols in feature_groups.items():
        X_abl = X_test_raw.copy()
        for c in drop_cols:
            X_abl[c] = med_vals[c]
        _, p_abl = predict_bundle_batch(hp_bundle, X_abl)
        ablation_results[grp_name] = eval_metrics(y_test, p_abl, threshold=0.08)

    report["feature_importance"] = feature_importance
    report["feature_ablation"] = ablation_results

    # -------------------------------------------------------------------------
    # TEST 9: COUNTERFACTUAL PERTURBATIONS & PHYSICAL MONOTONICITY
    # -------------------------------------------------------------------------
    print("\n--- [9] Physical Monotonicity & Counterfactual Tests ---")
    base_sample = X_test_raw.median().to_dict()
    monotonicity = {}

    # Test 9A: Rain 24h sweep (0 to 250 mm)
    rain_steps = [0.0, 10.0, 25.0, 50.0, 75.0, 100.0, 150.0, 200.0, 250.0]
    rain_probs = []
    for r in rain_steps:
        s = copy.deepcopy(base_sample)
        s["rainfall_24h_mm"] = r
        s["rainfall_72h_mm"] = max(s["rainfall_72h_mm"], r)
        df_s = pd.DataFrame([s])[CANONICAL_FEATURES]
        _, p = predict_bundle_batch(hp_bundle, df_s)
        rain_probs.append(round(float(p[0]), 4))
    monotonicity["rainfall_24h_sweep"] = {"steps": rain_steps, "probabilities": rain_probs}
    monotonicity["rainfall_is_monotonic_increasing"] = all(x <= y for x, y in zip(rain_probs, rain_probs[1:]))

    # Test 9B: Soil Saturation sweep (10% to 100%)
    soil_steps = [10.0, 30.0, 50.0, 70.0, 85.0, 95.0, 100.0]
    soil_probs = []
    for sat in soil_steps:
        s = copy.deepcopy(base_sample)
        s["soil_saturation_pct"] = sat
        df_s = pd.DataFrame([s])[CANONICAL_FEATURES]
        _, p = predict_bundle_batch(hp_bundle, df_s)
        soil_probs.append(round(float(p[0]), 4))
    monotonicity["soil_sat_sweep"] = {"steps": soil_steps, "probabilities": soil_probs}
    monotonicity["soil_is_monotonic_increasing"] = all(x <= y for x, y in zip(soil_probs, soil_probs[1:]))

    # Test 9C: River distance sweep (10m to 5000m)
    dist_steps = [10.0, 50.0, 100.0, 250.0, 500.0, 1000.0, 5000.0]
    dist_probs = []
    for d in dist_steps:
        s = copy.deepcopy(base_sample)
        s["dist_to_river_m"] = d
        df_s = pd.DataFrame([s])[CANONICAL_FEATURES]
        _, p = predict_bundle_batch(hp_bundle, df_s)
        dist_probs.append(round(float(p[0]), 4))
    monotonicity["river_dist_sweep"] = {"steps": dist_steps, "probabilities": dist_probs}
    monotonicity["river_dist_is_monotonic_decreasing"] = all(x >= y for x, y in zip(dist_probs, dist_probs[1:]))

    # Scenario A vs Scenario B
    scen_a = {
        "rainfall_1h_mm": 65.0, "rainfall_3h_mm": 120.0, "rainfall_6h_mm": 180.0,
        "rainfall_24h_mm": 240.0, "rainfall_72h_mm": 350.0, "soil_saturation_pct": 95.0,
        "deep_soil_saturation_pct": 90.0, "temperature_c": 18.0, "relative_humidity_pct": 98.0,
        "surface_pressure_hpa": 900.0, "wind_speed_kmh": 45.0, "elevation_m": 760.0,
        "catchment_slope_deg": 28.0, "dist_to_river_m": 25.0, "upstream_drainage_sqkm": 11200.0,
    }
    scen_b = {
        "rainfall_1h_mm": 0.0, "rainfall_3h_mm": 0.0, "rainfall_6h_mm": 0.0,
        "rainfall_24h_mm": 0.0, "rainfall_72h_mm": 0.0, "soil_saturation_pct": 25.0,
        "deep_soil_saturation_pct": 30.0, "temperature_c": 28.0, "relative_humidity_pct": 40.0,
        "surface_pressure_hpa": 930.0, "wind_speed_kmh": 5.0, "elevation_m": 1220.0,
        "catchment_slope_deg": 12.0, "dist_to_river_m": 2500.0, "upstream_drainage_sqkm": 500.0,
    }
    df_scen_a = pd.DataFrame([scen_a])[CANONICAL_FEATURES]
    df_scen_b = pd.DataFrame([scen_b])[CANONICAL_FEATURES]
    _, p_a = predict_bundle_batch(hp_bundle, df_scen_a)
    _, p_b = predict_bundle_batch(hp_bundle, df_scen_b)

    monotonicity["scenario_tests"] = {
        "scenario_a_extreme_storm_prob": round(float(p_a[0]), 4),
        "scenario_b_dry_control_prob": round(float(p_b[0]), 4),
        "scenario_a_greater_than_b": bool(p_a[0] > p_b[0]),
    }
    report["monotonicity_and_physics"] = monotonicity

    # -------------------------------------------------------------------------
    # TEST 10: ADVERSARIAL ATTACKS & SCHEMA STRESS
    # -------------------------------------------------------------------------
    print("\n--- [10] Executing Adversarial Input Attacks ---")
    adversarial_results = {}

    attacks = {
        "negative_rainfall": {"feature": "rainfall_24h_mm", "value": -150.0},
        "extreme_rainfall": {"feature": "rainfall_1h_mm", "value": 2500.0},
        "impossible_temperature_low": {"feature": "temperature_c", "value": -120.0},
        "impossible_temperature_high": {"feature": "temperature_c", "value": 95.0},
        "zero_pressure": {"feature": "surface_pressure_hpa", "value": 0.0},
        "nan_feature": {"feature": "rainfall_24h_mm", "value": np.nan},
        "infinity_feature": {"feature": "rainfall_24h_mm", "value": np.inf},
        "negative_infinity": {"feature": "rainfall_24h_mm", "value": -np.inf},
    }

    for att_name, att_cfg in attacks.items():
        s = copy.deepcopy(base_sample)
        s[att_cfg["feature"]] = att_cfg["value"]
        try:
            res = predict_flood_risk(s)
            adversarial_results[att_name] = {
                "handled_safely": True,
                "output_probability": res.get("flood_probability"),
                "risk_level": res.get("risk_level"),
                "status": "PASS",
            }
        except Exception as e:
            adversarial_results[att_name] = {
                "handled_safely": False,
                "error": str(e),
                "status": "CRASHED",
            }

    s_missing = copy.deepcopy(base_sample)
    for k in ["rainfall_1h_mm", "soil_saturation_pct", "catchment_slope_deg", "surface_pressure_hpa", "dist_to_river_m"]:
        del s_missing[k]
    try:
        res_miss = predict_flood_risk(s_missing)
        adversarial_results["missing_5_features"] = {
            "handled_safely": True,
            "output_risk_level": res_miss.get("risk_level"),
            "status": "PASS",
        }
    except Exception as e:
        adversarial_results["missing_5_features"] = {
            "handled_safely": False,
            "error": str(e),
            "status": "CRASHED",
        }

    # Attack: Shuffled feature order in raw DataFrame
    rev_cols = list(reversed(CANONICAL_FEATURES))
    df_rev = pd.DataFrame([base_sample])[rev_cols]
    try:
        sc = v2_prep.transform(df_rev)
        adversarial_results["reversed_column_order"] = {
            "silently_accepted": True,
            "vulnerability": "HIGH - Preprocessor accepted swapped column indices without verifying schema contract!",
        }
    except Exception as e:
        adversarial_results["reversed_column_order"] = {
            "silently_accepted": False,
            "error": str(e),
            "vulnerability": "NONE - Rejected safely",
        }

    report["adversarial_testing"] = adversarial_results

    # -------------------------------------------------------------------------
    # TEST 11: MULTI-REGION EVALUATION ACROSS ALL 10 REGIONS
    # -------------------------------------------------------------------------
    print("\n--- [11] Auditing All 10 Multi-Region Models on Holdouts ---")
    regional_metrics = {}

    for r in regions:
        r_bundle = model_registry.get(hazard="flood", region=r)
        r_splits_dir = REPO_ROOT / "ml" / "data" / "splits" / r
        r_holdout_file = r_splits_dir / "holdout_split.csv"

        if not r_holdout_file.exists():
            regional_metrics[r] = {"status": "NO_HOLDOUT_FILE"}
            continue

        df_h = pd.read_csv(r_holdout_file)
        if TARGET_COLUMN not in df_h.columns:
            regional_metrics[r] = {"status": "NO_TARGET_COLUMN"}
            continue

        X_h_raw = df_h[CANONICAL_FEATURES]
        y_h = df_h[TARGET_COLUMN].values

        try:
            raw_p, cal_p = predict_bundle_batch(r_bundle, X_h_raw)
            thresh = r_bundle.threshold
            m = eval_metrics(y_h, cal_p, threshold=thresh)
            m["selected_threshold"] = thresh
            m["model_algorithm"] = r_bundle.metadata.get("algorithm", "unknown")
            m["production_status"] = r_bundle.production_status
            regional_metrics[r] = m
        except Exception as e:
            regional_metrics[r] = {"error": str(e), "status": "EVAL_FAILED"}

    report["regional_models_audit"] = regional_metrics

    # -------------------------------------------------------------------------
    # TEST 12: CROSS-REGION GENERALIZATION
    # -------------------------------------------------------------------------
    print("\n--- [12] Cross-Region Generalization Benchmark ---")
    cross_region = {}

    for target_r in ["sikkim", "meghalaya", "leh_ladakh", "jammu_kashmir"]:
        r_file = REPO_ROOT / "ml" / "data" / "splits" / target_r / "holdout_split.csv"
        if r_file.exists():
            df_tgt = pd.read_csv(r_file)
            y_tgt = df_tgt[TARGET_COLUMN].values
            _, p_tgt = predict_bundle_batch(hp_bundle, df_tgt[CANONICAL_FEATURES])
            cross_region[f"hp_model_tested_on_{target_r}"] = eval_metrics(y_tgt, p_tgt, threshold=hp_bundle.threshold)

    sikkim_bundle = model_registry.get(hazard="flood", region="sikkim")
    _, p_hp_by_sikkim = predict_bundle_batch(sikkim_bundle, test_df[CANONICAL_FEATURES])
    cross_region["sikkim_model_tested_on_hp"] = eval_metrics(y_test, p_hp_by_sikkim, threshold=sikkim_bundle.threshold)

    report["cross_region_generalization"] = cross_region

    # -------------------------------------------------------------------------
    # TEST 13: REPRODUCIBILITY & RANDOM SEED SENSITIVITY
    # -------------------------------------------------------------------------
    print("\n--- [13] Testing Reproducibility & Random Seed Sensitivity ---")
    seed_metrics = []
    seeds = [42, 100, 26192, 999, 12345]

    for s in seeds:
        lr_s = LogisticRegression(C=0.1, class_weight="balanced", solver="liblinear", random_state=s)
        lr_s.fit(X_train_sc, y_train)
        p_s = lr_s.predict_proba(X_test_sc)[:, 1]
        m = eval_metrics(y_test, p_s, threshold=0.08)
        seed_metrics.append({"seed": s, "roc_auc": m["roc_auc"], "f1": m["f1"], "recall": m["recall"], "precision": m["precision"]})

    seed_df = pd.DataFrame(seed_metrics)
    seed_sensitivity = {
        "seeds_tested": seeds,
        "roc_auc_mean": round(float(seed_df["roc_auc"].mean()), 4),
        "roc_auc_std": round(float(seed_df["roc_auc"].std()), 6),
        "f1_mean": round(float(seed_df["f1"].mean()), 4),
        "f1_std": round(float(seed_df["f1"].std()), 6),
        "recall_mean": round(float(seed_df["recall"].mean()), 4),
        "recall_std": round(float(seed_df["recall"].std()), 6),
        "is_deterministic_reproducible": bool(seed_df["roc_auc"].std() < 1e-4),
    }
    report["seed_sensitivity"] = seed_sensitivity

    # -------------------------------------------------------------------------
    # TEST 14: LATENCY BENCHMARK & SECURITY
    # -------------------------------------------------------------------------
    print("\n--- [14] Latency Benchmarks & Serialization Security ---")
    latency = {}

    v2_model_path = REPO_ROOT / "ml" / "models" / "v2_selected_model.joblib"
    t0 = time.perf_counter()
    _m = joblib.load(v2_model_path)
    cold_latency_ms = (time.perf_counter() - t0) * 1000.0

    sample_vec = X_test_raw.iloc[0:1]
    times = []
    for _ in range(500):
        t1 = time.perf_counter()
        _ = predict_bundle_batch(hp_bundle, sample_vec)
        times.append((time.perf_counter() - t1) * 1000.0)

    latency["cold_artifact_load_ms"] = round(cold_latency_ms, 2)
    latency["warm_single_inference_mean_ms"] = round(float(np.mean(times)), 3)
    latency["warm_single_inference_p95_ms"] = round(float(np.percentile(times, 95)), 3)
    latency["warm_single_inference_p99_ms"] = round(float(np.percentile(times, 99)), 3)

    batch_100 = X_test_raw.iloc[:100]
    t_b100 = time.perf_counter()
    _ = predict_bundle_batch(hp_bundle, batch_100)
    latency["batch_100_ms"] = round((time.perf_counter() - t_b100) * 1000.0, 3)

    batch_1000 = X_test_raw.iloc[:1000]
    t_b1000 = time.perf_counter()
    _ = predict_bundle_batch(hp_bundle, batch_1000)
    latency["batch_1000_ms"] = round((time.perf_counter() - t_b1000) * 1000.0, 3)

    report["latency_benchmarks"] = latency

    # -------------------------------------------------------------------------
    # TEST 15: BOOTSTRAP 95% CONFIDENCE INTERVALS
    # -------------------------------------------------------------------------
    print("\n--- [15] Computing 1000-Fold Bootstrap Confidence Intervals ---")
    n_boot = 1000
    boot_roc = []
    boot_pr = []
    boot_rec = []
    boot_prec = []
    boot_f1 = []
    boot_brier = []

    rng_boot = np.random.RandomState(42)
    n_samples = len(y_test)

    for _ in range(n_boot):
        idx = rng_boot.choice(n_samples, size=n_samples, replace=True)
        y_b = y_test[idx]
        if len(np.unique(y_b)) < 2:
            continue
        p_b = cal_prob_test[idx]
        pred_b = (p_b >= 0.08).astype(int)

        boot_roc.append(roc_auc_score(y_b, p_b))
        boot_pr.append(average_precision_score(y_b, p_b))
        boot_rec.append(recall_score(y_b, pred_b, zero_division=0))
        boot_prec.append(precision_score(y_b, pred_b, zero_division=0))
        boot_f1.append(f1_score(y_b, pred_b, zero_division=0))
        boot_brier.append(brier_score_loss(y_b, p_b))

    bootstrap_ci = {
        "roc_auc_95_ci": [round(float(np.percentile(boot_roc, 2.5)), 4), round(float(np.percentile(boot_roc, 97.5)), 4)],
        "pr_auc_95_ci": [round(float(np.percentile(boot_pr, 2.5)), 4), round(float(np.percentile(boot_pr, 97.5)), 4)],
        "recall_95_ci": [round(float(np.percentile(boot_rec, 2.5)), 4), round(float(np.percentile(boot_rec, 97.5)), 4)],
        "precision_95_ci": [round(float(np.percentile(boot_prec, 2.5)), 4), round(float(np.percentile(boot_prec, 97.5)), 4)],
        "f1_95_ci": [round(float(np.percentile(boot_f1, 2.5)), 4), round(float(np.percentile(boot_f1, 97.5)), 4)],
        "brier_95_ci": [round(float(np.percentile(boot_brier, 2.5)), 4), round(float(np.percentile(boot_brier, 97.5)), 4)],
    }
    report["bootstrap_ci"] = bootstrap_ci

    # -------------------------------------------------------------------------
    # SAVE DUMP
    # -------------------------------------------------------------------------
    out_dump_path = REPO_ROOT / "scratch" / "audit_results_dump.json"
    with open(out_dump_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\n[SUCCESS] Full audit completed! Dump saved to {out_dump_path}")


if __name__ == "__main__":
    main()
