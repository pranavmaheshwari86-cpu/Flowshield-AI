import json

with open('scratch/audit_results_dump.json') as f:
    d = json.load(f)

print("=== V2 EVALUATION ON HOLDOUT ===")
for k, v in d['v2_eval'].items():
    print(f"{k}: AUC={v.get('roc_auc')}, PR={v.get('pr_auc')}, Rec={v.get('recall')}, Prec={v.get('precision')}, F1={v.get('f1')}, Brier={v.get('brier_score')}, ECE={v.get('ece')}, FNR={v.get('fnr')}, FPR={v.get('fpr')}")

print("\n=== INDEPENDENT BASELINES ===")
for k, v in d['baselines'].items():
    print(f"{k:32}: AUC={str(v.get('roc_auc')):6} | PR={str(v.get('pr_auc')):6} | Rec={str(v.get('recall')):6} | Prec={str(v.get('precision')):6} | F1={str(v.get('f1')):6} | Brier={str(v.get('brier_score')):6}")

print("\n=== SPLIT & LEAKAGE EXPERIMENTS ===")
for k, v in d['split_experiments'].items():
    print(f"{k:35}: {v}")

print("\n=== CLASS IMBALANCE STRESS ===")
for k, v in d['class_imbalance_stress'].items():
    print(f"{k:10}: Prevalence={v.get('prevalence')} | PR-AUC={v.get('pr_auc')} | Precision={v.get('precision')} | Recall={v.get('recall')} | F1={v.get('f1')} | FalseAlarms={v.get('fp')}")

print("\n=== ALERT FATIGUE ===")
print(d['alert_fatigue'])

print("\n=== FEATURE IMPORTANCE (LOG-ODDS COEFFICIENTS) ===")
for feat, coef in sorted(d['feature_importance'].items(), key=lambda x: abs(x[1]), reverse=True):
    print(f"{feat:30}: {coef}")

print("\n=== FEATURE ABLATION ===")
for k, v in d['feature_ablation'].items():
    print(f"{k:25}: Rec={v.get('recall')} | Prec={v.get('precision')} | F1={v.get('f1')} | ROC={v.get('roc_auc')} | PR={v.get('pr_auc')}")

print("\n=== MONOTONICITY & PHYSICAL SCENARIOS ===")
print("Rainfall monotonic:", d['monotonicity_and_physics']['rainfall_is_monotonic_increasing'])
print("Rainfall sweep:", d['monotonicity_and_physics']['rainfall_24h_sweep'])
print("Soil sat monotonic:", d['monotonicity_and_physics']['soil_is_monotonic_increasing'])
print("Soil sweep:", d['monotonicity_and_physics']['soil_sat_sweep'])
print("River dist monotonic:", d['monotonicity_and_physics']['river_dist_is_monotonic_decreasing'])
print("River dist sweep:", d['monotonicity_and_physics']['river_dist_sweep'])
print("Scenario tests:", d['monotonicity_and_physics']['scenario_tests'])

print("\n=== ADVERSARIAL TESTING ===")
for k, v in d['adversarial_testing'].items():
    print(f"{k:30}: {v}")

print("\n=== REGIONAL MODELS AUDIT (ALL 10) ===")
for r, m in d['regional_models_audit'].items():
    print(f"{r:20} | Status: {m.get('production_status', 'N/A'):18} | Algo: {m.get('model_algorithm', 'N/A'):15} | Thresh: {str(m.get('selected_threshold')):6} | AUC: {str(m.get('roc_auc')):6} | PR: {str(m.get('pr_auc')):6} | Rec: {str(m.get('recall')):6} | Prec: {str(m.get('precision')):6} | F1: {str(m.get('f1')):6}")

print("\n=== CROSS-REGION GENERALIZATION ===")
for k, v in d['cross_region_generalization'].items():
    print(f"{k:30}: AUC={str(v.get('roc_auc')):6} | Rec={str(v.get('recall')):6} | Prec={str(v.get('precision')):6} | F1={str(v.get('f1')):6}")

print("\n=== BOOTSTRAP 95% CONFIDENCE INTERVALS ===")
for k, v in d['bootstrap_ci'].items():
    print(f"{k:20}: {v}")

print("\n=== SEED SENSITIVITY ===")
print(d['seed_sensitivity'])

print("\n=== LATENCY BENCHMARKS ===")
print(d['latency_benchmarks'])
