# File: reminder_repeat.py
from datetime import datetime
from dateutil.relativedelta import relativedelta

def adjust_initial_slots(slots: list[datetime], rpt_type: str, interval: int, now: datetime) -> list[datetime]:
    """Сдвигает прошлые слоты на следующий период повторения."""
    adjusted = []
    for dt in slots:
        if dt <= now:
            delta_args = {
                'daily':   {'days': interval},
                'weekly':  {'weeks': interval},
                'monthly': {'months': interval},
                'yearly':  {'years': interval},
                'days':    {'days': interval},
            }[rpt_type]
            dt = dt + relativedelta(**delta_args)
        adjusted.append(dt)
    return adjusted
