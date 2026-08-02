import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from apps.api.models.deadline import ApprovedDeadline, DeadlineCandidate, DeadlineState
from apps.api.services.deadline_engine import DeadlineEngine


def test_is_adli_tatil():
    assert DeadlineEngine.is_adli_tatil(datetime.date(2026, 7, 19)) is False
    assert DeadlineEngine.is_adli_tatil(datetime.date(2026, 7, 20)) is True
    assert DeadlineEngine.is_adli_tatil(datetime.date(2026, 8, 15)) is True
    assert DeadlineEngine.is_adli_tatil(datetime.date(2026, 8, 31)) is True
    assert DeadlineEngine.is_adli_tatil(datetime.date(2026, 9, 1)) is False


def test_is_turkish_statutory_holiday():
    assert (
        DeadlineEngine.is_turkish_statutory_holiday(datetime.date(2026, 1, 1)) is True
    )
    assert (
        DeadlineEngine.is_turkish_statutory_holiday(datetime.date(2026, 4, 23)) is True
    )
    assert (
        DeadlineEngine.is_turkish_statutory_holiday(datetime.date(2026, 8, 30)) is True
    )
    # Ramazan Bayramı 2026: March 20-22
    assert (
        DeadlineEngine.is_turkish_statutory_holiday(datetime.date(2026, 3, 21)) is True
    )
    assert (
        DeadlineEngine.is_turkish_statutory_holiday(datetime.date(2026, 3, 25)) is False
    )


def test_calculate_date_adli_tatil_hmk_art_104():
    # A 10-day deadline triggered on July 15 under HMK ends on July 25 (inside Adli Tatil).
    # Under HMK Art. 104, it must extend to September 7!
    trigger = datetime.date(2026, 7, 15)
    calc = DeadlineEngine.calculate_date(
        trigger, 10, business_days_only=False, jurisdiction="TR_HMK"
    )
    assert calc == datetime.date(2026, 9, 7)


def test_calculate_date_iik_not_subject_to_adli_tatil():
    # A 10-day deadline triggered on July 15 under IIK ends on July 25 (Saturday).
    # Since IIK is not subject to Adli Tatil, it rolls over weekend to Monday July 27!
    trigger = datetime.date(2026, 7, 15)
    calc = DeadlineEngine.calculate_date(
        trigger, 10, business_days_only=False, jurisdiction="TR_IIK"
    )
    assert calc == datetime.date(2026, 7, 27)


def test_calculate_date_holiday_rollover():
    # August 28, 2026 is Friday. +2 days is Sunday August 30 (Zafer Bayramı).
    # Under non-Adli Tatil jurisdiction, Sunday + Zafer Bayramı rolls over to Monday August 31.
    trigger = datetime.date(2026, 8, 28)
    calc = DeadlineEngine.calculate_date(
        trigger, 2, business_days_only=False, jurisdiction="TR_IIK"
    )
    assert calc == datetime.date(2026, 8, 31)


@pytest.mark.asyncio
async def test_lawyer_review_stages():
    mock_session = AsyncMock()
    mock_session.add = MagicMock()
    pd = DeadlineCandidate(
        tenant_id="firm_1",
        matter_id="mat_1",
        rule_id="rule_1",
        calculated_date=datetime.date(2026, 9, 7),
        description="Auto-calculated deadline",
        status=DeadlineState.POTENTIAL_DEADLINE,
    )
    pd.id = "pd_100"

    mock_session.get.return_value = pd

    # Stage 1: Submit for review
    reviewed_pd = await DeadlineEngine.submit_for_review(
        mock_session, "pd_100", "firm_1", "Please check IIK rules"
    )
    assert reviewed_pd is not None
    assert reviewed_pd.status == DeadlineState.CALCULATED
    assert "Please check IIK rules" in reviewed_pd.description

    # Stage 2: Approve
    approved = await DeadlineEngine.approve_deadline(
        mock_session, "pd_100", "firm_1", "lawyer_yasin"
    )
    assert approved is not None
    assert pd.status == DeadlineState.ATTORNEY_VERIFIED
    assert isinstance(approved, ApprovedDeadline)
    assert approved.due_date == datetime.date(2026, 9, 7)
    assert "Approved by Lawyer lawyer_yasin" in approved.description
