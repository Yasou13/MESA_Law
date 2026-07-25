import pytest
from datetime import date
from pydantic import ValidationError
from apps.api.schemas.legal_package import (
    SourceManifest,
    LegislationItem,
    CourtDecisionItem,
    GoldenLegalPackage
)

def test_valid_golden_package():
    manifest = SourceManifest(
        package_id="PKG-2026-01",
        publisher="MESA Law",
        release_date=date.today(),
        license="PRIVATE",
        package_hash="some-valid-hash-1234"
    )
    
    leg = LegislationItem(
        id="leg-1",
        title="Türk Borçlar Kanunu",
        legislation_type="KANUN",
        law_number="6098",
        enactment_date=date(2011, 1, 11),
        valid_from=date(2012, 7, 1),
        content="Madde 1..."
    )
    
    decision = CourtDecisionItem(
        id="dec-1",
        court="YARGITAY",
        chamber="9. Hukuk Dairesi",
        esas_no="2021/123",
        karar_no="2021/456",
        decision_date=date(2021, 5, 10),
        anonymization_status="ANONYMIZED",
        content="Karar özeti..."
    )
    
    pkg = GoldenLegalPackage(
        manifest=manifest,
        legislation=[leg],
        court_decisions=[decision]
    )
    
    assert pkg.manifest.package_id == "PKG-2026-01"
    assert len(pkg.legislation) == 1
    assert len(pkg.court_decisions) == 1

def test_invalid_anonymization_status():
    with pytest.raises(ValidationError) as exc:
        CourtDecisionItem(
            id="dec-2",
            court="YARGITAY",
            esas_no="1",
            karar_no="2",
            decision_date=date(2021, 5, 10),
            anonymization_status="INVALID_STATUS",
            content="test"
        )
    assert "must be ANONYMIZED, RAW, or PENDING" in str(exc.value)

def test_public_license_requires_anonymization():
    manifest = SourceManifest(
        package_id="PKG-2026-02",
        publisher="MESA Law",
        release_date=date.today(),
        license="PUBLIC",
        package_hash="valid-hash"
    )
    
    decision = CourtDecisionItem(
        id="dec-3",
        court="YARGITAY",
        esas_no="1",
        karar_no="2",
        decision_date=date(2021, 5, 10),
        anonymization_status="RAW",
        content="test with personal data"
    )
    
    with pytest.raises(ValidationError) as exc:
        GoldenLegalPackage(
            manifest=manifest,
            court_decisions=[decision]
        )
    assert "must be ANONYMIZED for PUBLIC license" in str(exc.value)

def test_invalid_package_hash():
    manifest = SourceManifest(
        package_id="PKG-2026-03",
        publisher="MESA Law",
        release_date=date.today(),
        license="PRIVATE",
        package_hash="FORCE_INVALID_HASH"
    )
    
    with pytest.raises(ValidationError) as exc:
        GoldenLegalPackage(
            manifest=manifest,
            court_decisions=[]
        )
    assert "Package hash validation failed" in str(exc.value)
