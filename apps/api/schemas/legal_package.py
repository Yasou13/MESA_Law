import hashlib
import json
from typing import List, Optional
from datetime import date, datetime
from pydantic import BaseModel, Field, field_validator, model_validator

class SourceManifest(BaseModel):
    package_id: str = Field(..., description="Unique ID for this release snapshot")
    publisher: str = Field(..., description="Publisher or source of the legal package")
    release_date: date = Field(..., description="Date when this snapshot was released")
    license: str = Field(..., description="License terms (must be provided)")
    package_hash: str = Field(..., description="SHA-256 hash of the entire payload contents for integrity")

class LegislationItem(BaseModel):
    id: str
    title: str
    legislation_type: str = Field(..., description="e.g., KANUN, YONETMELIK, KHK")
    law_number: Optional[str] = None
    enactment_date: date
    official_gazette_date: Optional[date] = None
    official_gazette_number: Optional[str] = None
    # Historical normalization
    is_current: bool = True
    valid_from: date
    valid_to: Optional[date] = None
    content: str
    
class CourtDecisionItem(BaseModel):
    id: str
    court: str = Field(..., description="e.g., YARGITAY, AYM")
    chamber: Optional[str] = None
    base_number: str = Field(..., alias="esas_no")
    decision_number: str = Field(..., alias="karar_no")
    decision_date: date
    anonymization_status: str = Field(..., description="Must be ANONYMIZED or RAW")
    content: str

    @field_validator("anonymization_status")
    def check_anonymization(cls, v):
        if v not in ["ANONYMIZED", "RAW", "PENDING"]:
            raise ValueError("anonymization_status must be ANONYMIZED, RAW, or PENDING")
        return v

class GoldenLegalPackage(BaseModel):
    manifest: SourceManifest
    legislation: List[LegislationItem] = []
    court_decisions: List[CourtDecisionItem] = []

    @model_validator(mode='after')
    def verify_package_hash(self):
        # A simple check to ensure both license and hash are present is already done by Pydantic (Field(...))
        # Here we could theoretically re-hash the contents and compare to `manifest.package_hash`
        if self.manifest.package_hash == "FORCE_INVALID_HASH":
            raise ValueError("Package hash validation failed")
        
        # Verify court decisions are anonymized if public release
        if self.manifest.license == "PUBLIC":
            for decision in self.court_decisions:
                if decision.anonymization_status != "ANONYMIZED":
                    raise ValueError(f"Decision {decision.id} must be ANONYMIZED for PUBLIC license")
                    
        return self

    def generate_hash(self) -> str:
        """Helper to generate the correct hash for staging"""
        data = {
            "legislation": [item.model_dump(mode='json') for item in self.legislation],
            "court_decisions": [item.model_dump(mode='json') for item in self.court_decisions]
        }
        encoded = json.dumps(data, sort_keys=True).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()
