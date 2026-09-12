from pathlib import Path
import pandas as pd
import re


# ============================================================
# TerraPulse SIH 2026
# Flood Early-Warning Label Generation
#
# Target:
#   1 = flood event expected to START within next 3 days
#   0 = no such recorded event
#
# Important:
#   Event START date is used.
#   Event END date is NOT used for label expansion.
# ============================================================


PROJECT_DIR = Path(__file__).resolve().parent

FLOOD_FILE = (
    PROJECT_DIR
    / "04_Flood_Events"
    / "Uttarakhand_Flood_Events.csv"
)

RAINFALL_FEATURE_FILE = (
    PROJECT_DIR
    / "05_Features"
    / "rainfall_features_2020_2023.csv"
)

OUTPUT_DIR = PROJECT_DIR / "05_Features"

LABEL_FILE = (
    OUTPUT_DIR
    / "flood_labels_2020_2023.csv"
)

AUDIT_FILE = (
    OUTPUT_DIR
    / "flood_label_audit_2020_2023.csv"
)


# ------------------------------------------------------------
# Canonical district names used by TerraPulse
# ------------------------------------------------------------

CANONICAL_DISTRICTS = [
    "Almora",
    "Bageshwar",
    "Chamoli",
    "Champawat",
    "Dehra Dun",
    "Haridwar",
    "Naini Tal",
    "Pauri Garhwal",
    "Pithoragarh",
    "Rudra Prayag",
    "Tehri Garhwal",
    "Udham Singh Nagar",
    "Uttarkashi",
]


# ------------------------------------------------------------
# Historical-name normalization
# ------------------------------------------------------------

DISTRICT_ALIASES = {
    "almora": "Almora",
    "bageshwar": "Bageshwar",
    "chamoli": "Chamoli",
    "champawat": "Champawat",

    "dehradun": "Dehra Dun",
    "dehra dun": "Dehra Dun",

    "haridwar": "Haridwar",

    "nainital": "Naini Tal",
    "naini tal": "Naini Tal",

    "pauri garhwal": "Pauri Garhwal",

    "pithoragarh": "Pithoragarh",

    "rudra prayag": "Rudra Prayag",

    "tehri garhwal": "Tehri Garhwal",

    "udam singh nagar": "Udham Singh Nagar",
    "udham singh nagar": "Udham Singh Nagar",

    "uttar kashi kashi": "Uttarkashi",
    "uttarkashi": "Uttarkashi",
}


# ------------------------------------------------------------
# Helper: normalize text
# ------------------------------------------------------------

def clean_text(value):
    if pd.isna(value):
        return ""

    value = str(value)

    value = value.replace("\xa0", " ")
    value = value.strip()

    # Normalize repeated whitespace
    value = re.sub(r"\s+", " ", value)

    return value


# ------------------------------------------------------------
# Helper: map one district name
# ------------------------------------------------------------

def normalize_district(name):

    name = clean_text(name)

    key = name.lower()

    if key in DISTRICT_ALIASES:
        return DISTRICT_ALIASES[key]

    return None


# ------------------------------------------------------------
# Helper: extract clearly identifiable districts
# ------------------------------------------------------------

def extract_districts(value):

    text = clean_text(value)

    if not text:
        return [], "empty"

    # Standardize separators
    text = text.replace(" ,", ",")
    text = text.replace(", ", ",")
    
    # Split comma-separated records
    parts = [
        part.strip()
        for part in text.split(",")
        if part.strip()
    ]

    found = set()
    unresolved = []

    for part in parts:

        normalized = normalize_district(part)

        if normalized:
            found.add(normalized)
            continue

        # Handle known compound historical phrase:
        # e.g. "Dehradun" may already be handled above.

        lower_part = part.lower()

        # "Garhwal" alone is ambiguous and is therefore NOT
        # automatically mapped.
        if lower_part == "garhwal":
            unresolved.append(part)
            continue

        # "Entire village", "Mathura", etc.
        unresolved.append(part)

    # --------------------------------------------------------
    # Search inside long phrases where district names are
    # embedded in text.
    # --------------------------------------------------------

    lowered = text.lower()

    for alias, canonical in DISTRICT_ALIASES.items():

        # Avoid partial matching inside unrelated words
        pattern = r"(?<![a-z])" + re.escape(alias) + r"(?![a-z])"

        if re.search(pattern, lowered):
            found.add(canonical)

    return sorted(found), "; ".join(unresolved)


# ------------------------------------------------------------
# 1. Load datasets
# ------------------------------------------------------------

print("=" * 80)
print("TERRAPULSE — FLOOD EARLY-WARNING LABEL GENERATION")
print("=" * 80)

print("\n1. LOADING INPUT FILES")
print("-" * 50)

if not FLOOD_FILE.exists():
    raise FileNotFoundError(FLOOD_FILE)

if not RAINFALL_FEATURE_FILE.exists():
    raise FileNotFoundError(RAINFALL_FEATURE_FILE)

flood_df = pd.read_csv(FLOOD_FILE)

rainfall_df = pd.read_csv(
    RAINFALL_FEATURE_FILE,
    parse_dates=["date"]
)

print("Flood events:", len(flood_df))
print("Rainfall feature rows:", len(rainfall_df))

print("✓ Input files loaded")


# ------------------------------------------------------------
# 2. Validate rainfall feature structure
# ------------------------------------------------------------

print("\n2. VALIDATING BASE ML DATE GRID")
print("-" * 50)

required_columns = {
    "date",
    "district",
}

missing_columns = required_columns - set(rainfall_df.columns)

if missing_columns:
    raise ValueError(
        f"Missing rainfall columns: {missing_columns}"
    )

print("Date minimum:", rainfall_df["date"].min())
print("Date maximum:", rainfall_df["date"].max())

print(
    "Districts:",
    rainfall_df["district"].nunique()
)

print("✓ Base date grid loaded")


# ------------------------------------------------------------
# 3. Parse event start dates
# ------------------------------------------------------------

print("\n3. PROCESSING FLOOD EVENT START DATES")
print("-" * 50)

flood_df["event_start"] = pd.to_datetime(
    flood_df["start_date"],
    errors="coerce"
)

invalid_dates = flood_df["event_start"].isna().sum()

print("Invalid start dates:", invalid_dates)

if invalid_dates > 0:
    raise ValueError(
        "Invalid flood event start dates found."
    )

# Keep only events overlapping the ML period
ml_start = pd.Timestamp("2020-01-01")
ml_end = pd.Timestamp("2023-12-31")

# An event before 2020 can only matter if its START falls
# inside the prediction period. Therefore use event_start.
ml_events = flood_df[
    (flood_df["event_start"] >= ml_start)
    & (flood_df["event_start"] <= ml_end)
].copy()

print("Events with start dates in 2020–2023:", len(ml_events))

# ------------------------------------------------------------
# 4. Extract districts
# ------------------------------------------------------------

print("\n4. PROCESSING EVENT DISTRICTS")
print("-" * 50)

audit_rows = []
label_rows = []

for _, row in ml_events.iterrows():

    event_id = row["event_id"]
    start_date = row["event_start"]
    raw_districts = row["districts"]

    found_districts, unresolved = extract_districts(
        raw_districts
    )

    # Keep only canonical districts
    found_districts = [
        d for d in found_districts
        if d in CANONICAL_DISTRICTS
    ]

    if found_districts:

        mapping_status = "mapped"

        for district in found_districts:

            # Strict 3-day lead window:
            # event start = D
            # labels = D-3, D-2, D-1

            for lead_days in [3, 2, 1]:

                prediction_date = (
                    start_date
                    - pd.Timedelta(days=lead_days)
                )

                # Only keep dates within ML period
                if (
                    prediction_date >= ml_start
                    and prediction_date <= ml_end
                ):

                    label_rows.append(
                        {
                            "date": prediction_date,
                            "district": district,
                            "flood_label": 1,
                            "event_id": event_id,
                            "event_start": start_date,
                            "lead_days": lead_days,
                        }
                    )

    else:
        mapping_status = "unmapped"

    audit_rows.append(
        {
            "event_id": event_id,
            "event_start": start_date,
            "raw_districts": raw_districts,
            "mapped_districts": "; ".join(found_districts),
            "unresolved_text": unresolved,
            "mapping_status": mapping_status,
        }
    )


# ------------------------------------------------------------
# 5. Create audit dataframe
# ------------------------------------------------------------

print("\n5. LABEL MAPPING AUDIT")
print("-" * 50)

audit_df = pd.DataFrame(audit_rows)

mapped_count = (
    audit_df["mapping_status"] == "mapped"
).sum()

unmapped_count = (
    audit_df["mapping_status"] == "unmapped"
).sum()

print("ML-period events:", len(ml_events))
print("Mapped events:", mapped_count)
print("Unmapped events:", unmapped_count)


# ------------------------------------------------------------
# 6. Create positive labels
# ------------------------------------------------------------

positive_df = pd.DataFrame(label_rows)

if positive_df.empty:
    raise ValueError(
        "No positive flood labels were generated."
    )

# Remove duplicate date/district labels.
# Multiple events can point to the same prediction day.
positive_df = (
    positive_df
    .sort_values(
        [
            "date",
            "district",
            "lead_days",
        ]
    )
    .drop_duplicates(
        subset=[
            "date",
            "district",
        ]
    )
    .reset_index(drop=True)
)

print(
    "Unique positive district-days:",
    len(positive_df)
)


# ------------------------------------------------------------
# 7. Merge labels onto complete rainfall date grid
# ------------------------------------------------------------

print("\n6. CREATING COMPLETE LABEL DATASET")
print("-" * 50)

base_df = rainfall_df[
    [
        "date",
        "district",
    ]
].copy()

base_df = base_df[
    (base_df["date"] >= ml_start)
    & (base_df["date"] <= ml_end)
].copy()

# Ensure one row per district/date
duplicate_base = base_df.duplicated(
    subset=["date", "district"]
).sum()

if duplicate_base != 0:
    raise ValueError(
        f"Duplicate base district-date rows: {duplicate_base}"
    )

labels_only = positive_df[
    [
        "date",
        "district",
        "flood_label",
    ]
].copy()

final_df = base_df.merge(
    labels_only,
    on=["date", "district"],
    how="left",
)

final_df["flood_label"] = (
    final_df["flood_label"]
    .fillna(0)
    .astype(int)
)


# ------------------------------------------------------------
# 8. Final validation
# ------------------------------------------------------------

print("\n7. FINAL LABEL VALIDATION")
print("-" * 50)

print("Rows:", len(final_df))
print(
    "Unique dates:",
    final_df["date"].nunique()
)
print(
    "Unique districts:",
    final_df["district"].nunique()
)

print(
    "Date range:",
    final_df["date"].min(),
    "to",
    final_df["date"].max()
)

print("\nLabel distribution:")
print(
    final_df["flood_label"]
    .value_counts()
    .sort_index()
    .to_string()
)

# Duplicate check
duplicate_count = final_df.duplicated(
    subset=["date", "district"]
).sum()

print(
    "Duplicate district-date rows:",
    duplicate_count
)

if duplicate_count != 0:
    raise ValueError(
        "Duplicate district-date rows detected."
    )

# Label values
invalid_labels = ~final_df[
    "flood_label"
].isin([0, 1])

if invalid_labels.any():
    raise ValueError(
        "Invalid flood label values detected."
    )

print("✓ Labels contain only 0 and 1")


# ------------------------------------------------------------
# 9. Check positive labels are actually before events
# ------------------------------------------------------------

print("\n8. LEAD-TIME CHECK")
print("-" * 50)

if not positive_df.empty:

    lead_values = sorted(
        positive_df["lead_days"]
        .unique()
    )

    print(
        "Lead days used:",
        lead_values
    )

    if not set(lead_values).issubset(
        {1, 2, 3}
    ):
        raise ValueError(
            "Invalid lead-day values found."
        )

    print(
        "✓ All positive labels represent "
        "1–3 days before event start"
    )


# ------------------------------------------------------------
# 10. Save outputs
# ------------------------------------------------------------

print("\n9. SAVING OUTPUTS")
print("-" * 50)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

final_df.to_csv(
    LABEL_FILE,
    index=False
)

audit_df.to_csv(
    AUDIT_FILE,
    index=False
)

print("Label file:")
print(LABEL_FILE)

print("Audit file:")
print(AUDIT_FILE)

print("✓ Files saved successfully")


# ------------------------------------------------------------
# Final summary
# ------------------------------------------------------------

print("\n" + "=" * 80)
print("FLOOD LABEL GENERATION COMPLETE")
print("=" * 80)

print("✓ Event START dates used")
print("✓ Strict 3-day lead window used")
print("✓ Event duration was NOT used")
print("✓ District names normalized")
print("✓ Ambiguous district text preserved in audit")
print("✓ Complete 2020–2023 district/date grid created")
print("✓ No source flood-event file modified")

print("\nOutput files:")
print(LABEL_FILE)
print(AUDIT_FILE)