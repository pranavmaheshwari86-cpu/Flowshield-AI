"""
scripts/ingest_and_validate_evacuation_data.py
Flowshield — Evacuation Shelter Data Ingestion & Automated Validation Runner
Executes:
1. Model coverage synchronization
2. Official DDMP & OSM shelter ingestion
3. Geographic bounding box coordinate validation
4. Deduplication
5. Confidence scoring audit
"""

import sys
import os
import json

# Ensure project root in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from apps.api.app.database import SessionLocal
from apps.api.app.services.shelter_ingestion_service import shelter_ingestion_service


def main():
    print("==========================================================")
    print("FLOWSHIELD EVACUATION SHELTER INGESTION & AUDIT PIPELINE")
    print("==========================================================")
    db = SessionLocal()
    try:
        report = shelter_ingestion_service.run_ingestion_and_validation(db)
        print("\nPipeline Execution Report:")
        print(json.dumps(report, indent=2))
        print("\nAudit Summary:")
        print(f"Total Candidate Records: {report['total_candidates']}")
        print(f"Valid Records Ingested:  {report['valid_records']}")
        print(f"Invalid Records:         {report['invalid_records']}")
        print(f"Duplicates Merged:       {report['duplicates_merged']}")
        print(f"States Covered:          {', '.join(report['states_covered'])}")
        print(f"Districts Covered:       {len(report['districts_covered'])} districts")
        print(f"High Confidence (>=85):  {report['confidence_tiers']['HIGH (>=85)']}")
        print(f"Medium Confidence:       {report['confidence_tiers']['MEDIUM (70-84)']}")
        print("==========================================================")
    finally:
        db.close()


if __name__ == "__main__":
    main()
