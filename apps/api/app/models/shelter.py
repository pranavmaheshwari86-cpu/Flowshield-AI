import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, JSON
from ..database import Base


class Shelter(Base):
    __tablename__ = "shelters"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(150), nullable=False, index=True)
    type = Column(String(60), nullable=False)  # Educational Complex, Stadium, Community Center, Hospital, etc.

    # Geographic Hierarchy
    state = Column(String(100), nullable=False, default="Uttarakhand", index=True)
    district = Column(String(100), nullable=False, default="Rudraprayag", index=True)
    subdistrict_block = Column(String(100), nullable=True)
    village_town = Column(String(100), nullable=True)
    address = Column(String(255), nullable=True)

    # Capacity & Occupancy (Nullable if not officially published)
    capacity = Column(Integer, nullable=True)
    total_capacity = Column(Integer, nullable=True)  # Backwards compatibility alias
    current_occupancy = Column(Integer, nullable=True)

    # Operational Status
    status = Column(String(20), nullable=False, default="AVAILABLE")  # AVAILABLE, NEAR_CAPACITY, FULL, CLOSED
    operational_status = Column(String(30), nullable=False, default="OPERATIONAL")  # OPERATIONAL, STANDBY, INACTIVE

    # Facility Readiness & Amenities
    has_medical = Column(Boolean, nullable=False, default=True)
    medical_facility = Column(Boolean, nullable=False, default=True)
    has_power_backup = Column(Boolean, nullable=False, default=True)
    generator_available = Column(Boolean, nullable=False, default=True)
    water_available = Column(Boolean, nullable=False, default=True)
    food_available = Column(Boolean, nullable=False, default=True)
    toilets_available = Column(Boolean, nullable=False, default=True)
    electricity_available = Column(Boolean, nullable=False, default=True)
    communication_available = Column(Boolean, nullable=False, default=True)
    wheelchair_accessible = Column(Boolean, nullable=False, default=False)
    pet_friendly_if_known = Column(Boolean, nullable=True)
    is_24x7 = Column(Boolean, nullable=False, default=True)

    # Authority & Contacts
    managing_authority = Column(String(150), nullable=True)
    contact_person = Column(String(100), nullable=True)
    contact_phone = Column(String(30), nullable=True)

    # Spatial Coordinates (WGS84)
    latitude = Column(Float, nullable=False, index=True)
    longitude = Column(Float, nullable=False, index=True)
    geometry = Column(JSON, nullable=True)  # GeoJSON Point

    # Source Provenance & Verification
    source_name = Column(String(150), nullable=True)  # USDMA DDMP, HPSDMA DDMP, OpenStreetMap, etc.
    source_url = Column(String(500), nullable=True)
    source_type = Column(String(50), nullable=True)  # OFFICIAL_DDMP, STATE_DMA, OSM_VERIFIED, HUMANITARIAN
    source_last_verified = Column(String(50), nullable=True)
    data_last_updated = Column(DateTime, nullable=True, default=lambda: datetime.now(timezone.utc))
    verification_status = Column(String(30), nullable=False, default="VERIFIED", index=True)  # VERIFIED, PARTIALLY_VERIFIED, UNVERIFIED, STALE, INACTIVE
    confidence_score = Column(Integer, nullable=False, default=85)  # 0 to 100

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    @property
    def effective_capacity(self):
        return self.capacity if self.capacity is not None else self.total_capacity

    @property
    def available_capacity(self):
        cap = self.effective_capacity
        if cap is None:
            return None
        occ = self.current_occupancy if self.current_occupancy is not None else 0
        return max(0, cap - occ)

    @property
    def occupancy_percentage(self):
        cap = self.effective_capacity
        if cap is None or cap == 0:
            return None
        occ = self.current_occupancy if self.current_occupancy is not None else 0
        return round((occ / cap) * 100.0, 1)
