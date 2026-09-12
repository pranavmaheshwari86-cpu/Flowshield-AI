# QUARANTINED DATASET REPOSITORY — NOT VALID TRAINING DATA

**STATUS:** QUARANTINED — NOT VALID TRAINING DATA
**AUDIT DATE:** September 12, 2026
**AUDIT STANDARD:** Flowshield Ultimate Scientific Model Rebuild (§5)

### Reason for Quarantine:
Synthetic/generated meteorological and hydrological observations detected. Files in this directory were generated via numpy pseudo-random climatology functions (np.random.RandomState) in ml/pipeline/dataset_builder.py rather than empirical observation or physical reanalysis.

### Governing Policy:
1. Retained strictly for provenance, forensic auditing, and scientific reproducibility.
2. STRICTLY PROHIBITED from being accessed, loaded, or utilized by any production ML training, tuning, or inference pipeline.
3. Any regional model candidate trained on data from this directory is automatically disqualified from production certification.

### Quarantined Regions:
1. Arunachal Pradesh (runachal_pradesh)
2. Jammu & Kashmir (jammu_kashmir)
3. Leh & Ladakh (leh_ladakh)
4. Manipur (manipur)
5. Meghalaya (meghalaya)
6. Mizoram (mizoram)
7. Nagaland (
agaland)
8. Sikkim (sikkim)
9. Tripura (	ripura)
