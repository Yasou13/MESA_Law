"""Deadline Engine — computes legal deadlines from parsed documents and legal rules."""
import datetime
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from apps.api.models.deadline import DeadlineRule, PotentialDeadline

logger = logging.getLogger("api.services.deadline_engine")

class DeadlineEngine:
    @staticmethod
    def calculate_date(trigger_date: datetime.date, offset_days: int, business_days_only: bool = False) -> datetime.date:
        current = trigger_date
        if not business_days_only:
            return current + datetime.timedelta(days=offset_days)
            
        days_added = 0
        step = 1 if offset_days >= 0 else -1
        target_days = abs(offset_days)
        
        while days_added < target_days:
            current += datetime.timedelta(days=step)
            if current.weekday() < 5:  # Monday=0, Friday=4, Saturday=5, Sunday=6
                days_added += 1
        return current

    @classmethod
    async def evaluate_rules_for_event(
        cls,
        session: AsyncSession,
        tenant_id: str,
        matter_id: str,
        trigger_event: str,
        trigger_date: datetime.date
    ) -> list[PotentialDeadline]:
        logger.info(f"Evaluating deadline rules for event '{trigger_event}' on matter '{matter_id}'")
        result = await session.execute(
            select(DeadlineRule).where(
                DeadlineRule.tenant_id == tenant_id,
                DeadlineRule.trigger_event == trigger_event
            )
        )
        rules = result.scalars().all()
        
        potential_deadlines = []
        for rule in rules:
            calc_date = cls.calculate_date(trigger_date, rule.offset_days, business_days_only=True)
            pd = PotentialDeadline(
                tenant_id=tenant_id,
                matter_id=matter_id,
                rule_id=rule.id,
                calculated_date=calc_date,
                description=f"Auto-calculated from {rule.rule_name} ({rule.offset_days} business days after {trigger_event})",
                status="pending_approval"
            )
            session.add(pd)
            potential_deadlines.append(pd)
            
        if potential_deadlines:
            await session.commit()
            logger.info(f"Generated {len(potential_deadlines)} potential deadlines for matter '{matter_id}'")
            
        return potential_deadlines
        
deadline_engine = DeadlineEngine()

