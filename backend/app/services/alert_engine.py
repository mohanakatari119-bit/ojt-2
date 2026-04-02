"""Evaluate active alert rules against a newly ingested RequestLog."""
import operator as op
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert
from app.models.alert_event import AlertEvent
from app.models.request_log import RequestLog

OPS = {
    ">=": op.ge,
    "<=": op.le,
    "==": op.eq,
    "!=": op.ne,
    ">": op.gt,
    "<": op.lt,
}


def _get_field_value(log: RequestLog, field: str):
    return getattr(log, field, None)


async def evaluate_alerts(db: AsyncSession, log: RequestLog) -> None:
    result = await db.execute(
        select(Alert).where(Alert.service_id == log.service_id, Alert.is_active == True)
    )
    alerts = result.scalars().all()

    for alert in alerts:
        fn = OPS.get(alert.condition_operator)
        if fn is None:
            continue

        actual = _get_field_value(log, alert.condition_field)
        if actual is None:
            # For error field: treat non-None as truthy match for == / !=
            if alert.condition_field == "error":
                actual_bool = False
                try:
                    threshold = alert.condition_value.lower() in ("true", "1", "yes")
                    triggered = fn(actual_bool, threshold)
                except Exception:
                    continue
            else:
                continue
        else:
            try:
                # Coerce threshold to the same type as actual
                if isinstance(actual, float):
                    threshold = float(alert.condition_value)
                elif isinstance(actual, int):
                    threshold = int(alert.condition_value)
                else:
                    threshold = alert.condition_value
                triggered = fn(actual, threshold)
            except (ValueError, TypeError):
                continue

        if triggered:
            event = AlertEvent(
                alert_id=alert.id,
                log_id=log.id,
                message=(
                    f"Alert '{alert.name}' triggered: "
                    f"{alert.condition_field} {alert.condition_operator} {alert.condition_value} "
                    f"(actual={actual})"
                ),
            )
            db.add(event)

    await db.commit()
