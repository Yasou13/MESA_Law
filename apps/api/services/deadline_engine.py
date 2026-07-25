"""Deadline Engine — computes legal deadlines from parsed documents and legal rules under Turkish Law (HMK/İİK)."""
import datetime
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from apps.api.models.deadline import DeadlineRule, PotentialDeadline, ApprovedDeadline

logger = logging.getLogger("api.services.deadline_engine")

class DeadlineEngine:
    # Statutory fixed holidays (month, day) in Turkey
    FIXED_HOLIDAYS = {
        (1, 1),   # Yılbaşı
        (4, 23),  # Ulusal Egemenlik ve Çocuk Bayramı
        (5, 1),   # Emek ve Dayanışma Günü
        (5, 19),  # Atatürk'ü Anma, Gençlik ve Spor Bayramı
        (7, 15),  # Demokrasi ve Milli Birlik Günü
        (8, 30),  # Zafer Bayramı
        (10, 29), # Cumhuriyet Bayramı
    }

    # Dynamic religious holidays (year -> set of (month, day))
    RELIGIOUS_HOLIDAYS = {
        2025: {(3, 30), (3, 31), (4, 1), (6, 6), (6, 7), (6, 8), (6, 9)},
        2026: {(3, 20), (3, 21), (3, 22), (5, 27), (5, 28), (5, 29), (5, 30)},
        2027: {(3, 9), (3, 10), (3, 11), (5, 16), (5, 17), (5, 18), (5, 19)},
    }

    @classmethod
    def is_adli_tatil(cls, dt: datetime.date) -> bool:
        """
        Turkish Judicial Recess (Adli Tatil): July 20 to August 31 (inclusive).
        HMK Art. 102.
        """
        if dt.month == 7 and dt.day >= 20:
            return True
        if dt.month == 8:
            return True
        return False

    @classmethod
    def is_turkish_statutory_holiday(cls, dt: datetime.date) -> bool:
        """Checks national statutory and religious holidays in Turkey."""
        if (dt.month, dt.day) in cls.FIXED_HOLIDAYS:
            return True
        year_holidays = cls.RELIGIOUS_HOLIDAYS.get(dt.year, set())
        if (dt.month, dt.day) in year_holidays:
            return True
        return False

    @classmethod
    def is_business_day(cls, dt: datetime.date, subject_to_adli_tatil: bool = True) -> bool:
        """Returns True if the date is an official working day under the specified jurisdiction rules."""
        if dt.weekday() >= 5:  # Saturday=5, Sunday=6
            return False
        if cls.is_turkish_statutory_holiday(dt):
            return False
        if subject_to_adli_tatil and cls.is_adli_tatil(dt):
            return False
        return True

    @classmethod
    def calculate_date(
        cls,
        trigger_date: datetime.date,
        offset_days: int,
        business_days_only: bool = False,
        subject_to_adli_tatil: bool = True,
        jurisdiction: str = "TR_HMK"
    ) -> datetime.date:
        """
        Calculates due date applying Turkish legal calendar rules, holiday roll-over, and HMK Art. 104 Adli Tatil extension.
        """
        # Certain procedures (İİK execution, urgent labor/criminal) do not stop during Adli Tatil
        if jurisdiction in ("TR_IIK", "TR_CRIMINAL_URGENT", "TR_LABOR_URGENT"):
            subject_to_adli_tatil = False

        current = trigger_date
        
        if business_days_only:
            days_added = 0
            step = 1 if offset_days >= 0 else -1
            target_days = abs(offset_days)
            
            while days_added < target_days:
                current += datetime.timedelta(days=step)
                if cls.is_business_day(current, subject_to_adli_tatil=subject_to_adli_tatil):
                    days_added += 1
        else:
            current += datetime.timedelta(days=offset_days)

        # HMK Art. 104 Rule: If deadline ends within Adli Tatil, it is automatically extended to September 7 (inclusive)
        if subject_to_adli_tatil and cls.is_adli_tatil(current):
            logger.info(f"Deadline {current} falls within Adli Tatil. Applying HMK Art. 104 extension to September 7.")
            current = datetime.date(current.year, 9, 7)

        # General Roll-over Rule: If end date falls on a weekend or statutory holiday, roll forward to next business day
        while not cls.is_business_day(current, subject_to_adli_tatil=subject_to_adli_tatil):
            current += datetime.timedelta(days=1)

        return current

    @classmethod
    async def evaluate_rules_for_event(
        cls,
        session: AsyncSession,
        tenant_id: str,
        matter_id: str,
        trigger_event: str,
        trigger_date: datetime.date,
        jurisdiction: str = "TR_HMK"
    ) -> list[PotentialDeadline]:
        logger.info(f"Evaluating deadline rules for event '{trigger_event}' on matter '{matter_id}' (Jurisdiction: {jurisdiction})")
        result = await session.execute(
            select(DeadlineRule).where(
                DeadlineRule.tenant_id == tenant_id,
                DeadlineRule.trigger_event == trigger_event
            )
        )
        rules = result.scalars().all()
        
        potential_deadlines = []
        for rule in rules:
            calc_date = cls.calculate_date(
                trigger_date,
                rule.offset_days,
                business_days_only=False,
                subject_to_adli_tatil=(jurisdiction == "TR_HMK"),
                jurisdiction=jurisdiction
            )
            pd = PotentialDeadline(
                tenant_id=tenant_id,
                matter_id=matter_id,
                rule_id=rule.id,
                calculated_date=calc_date,
                description=f"Auto-calculated from {rule.rule_name} (v1.0 - {jurisdiction}): {rule.offset_days} days after {trigger_event}. Rule Version: 2025.1",
                status="pending_approval"
            )
            session.add(pd)
            potential_deadlines.append(pd)
            
        if potential_deadlines:
            await session.commit()
            logger.info(f"Generated {len(potential_deadlines)} potential deadlines for matter '{matter_id}'")
            
        return potential_deadlines

    @classmethod
    async def submit_for_review(cls, session: AsyncSession, potential_deadline_id: str, tenant_id: str, reviewer_notes: str = "") -> PotentialDeadline | None:
        """Stage 1: Submit a potential deadline for lawyer review."""
        pd = await session.get(PotentialDeadline, potential_deadline_id)
        if not pd or pd.tenant_id != tenant_id:
            return None
        pd.status = "under_review"
        if reviewer_notes:
            pd.description = f"{pd.description} [Review Notes: {reviewer_notes}]"
        await session.commit()
        await session.refresh(pd)
        return pd

    @classmethod
    async def approve_deadline(cls, session: AsyncSession, potential_deadline_id: str, tenant_id: str, lawyer_id: str) -> ApprovedDeadline | None:
        """Stage 2: Approve potential deadline and convert to ApprovedDeadline."""
        pd = await session.get(PotentialDeadline, potential_deadline_id)
        if not pd or pd.tenant_id != tenant_id or pd.status == "rejected":
            return None
        pd.status = "approved"
        
        approved = ApprovedDeadline(
            tenant_id=tenant_id,
            matter_id=pd.matter_id,
            potential_deadline_id=pd.id,
            due_date=pd.calculated_date,
            description=f"{pd.description} [Approved by Lawyer {lawyer_id}]",
            is_completed=False
        )
        session.add(approved)
        await session.commit()
        await session.refresh(approved)
        return approved

    @classmethod
    async def reject_deadline(cls, session: AsyncSession, potential_deadline_id: str, tenant_id: str, reason: str) -> PotentialDeadline | None:
        """Stage 2 Alt: Reject potential deadline."""
        pd = await session.get(PotentialDeadline, potential_deadline_id)
        if not pd or pd.tenant_id != tenant_id:
            return None
        pd.status = "rejected"
        pd.description = f"{pd.description} [Rejected: {reason}]"
        await session.commit()
        await session.refresh(pd)
        return pd

deadline_engine = DeadlineEngine()


