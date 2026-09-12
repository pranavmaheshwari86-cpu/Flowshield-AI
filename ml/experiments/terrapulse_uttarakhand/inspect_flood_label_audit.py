from pathlib import Path
import pandas as pd

# ============================================================
# TerraPulse SIH 2026
# Inspect Flood Label Mapping Audit
# ============================================================

PROJECT_DIR = Path(__file__).resolve().parent

AUDIT_FILE = (
    PROJECT_DIR
    / "05_Features"
    / "flood_label_audit_2020_2023.csv"
)

print("=" * 80)
print("TERRAPULSE — FLOOD LABEL AUDIT INSPECTION")
print("=" * 80)

# Load audit

if not AUDIT_FILE.exists():
    raise FileNotFoundError(
        f"Audit file not found:\n{AUDIT_FILE}"
    )

df = pd.read_csv(AUDIT_FILE)

print("\nTotal ML-period events:", len(df))


# Mapping summary

print("\nMAPPING SUMMARY")
print("-" * 50)

print(
    df["mapping_status"]
    .value_counts()
    .to_string()
)

# Show unmapped events

unmapped = df[
    df["mapping_status"] == "unmapped"
].copy()

print("\nUNMAPPED EVENTS")
print("=" * 80)

if unmapped.empty:

    print("✓ No unmapped events.")

else:
    print(
        unmapped[
            [
                "event_id",
                "event_start",
                "raw_districts",
                "mapped_districts",
                "unresolved_text",
                "mapping_status",
            ]
        ].to_string(index=False)
    )

# Show all mapped events

print("\nMAPPED EVENTS SUMMARY")
print("=" * 80)

mapped = df[
    df["mapping_status"] == "mapped"
].copy()

print(
    mapped[
        [
            "event_id",
            "event_start",
            "raw_districts",
            "mapped_districts",
        ]
    ].to_string(index=False)
)

print("\n" + "=" * 80)
print("AUDIT INSPECTION COMPLETE")
print("=" * 80)