from datetime import datetime
from dateutil.relativedelta import relativedelta

# Сдвигает прошлые слоты на следующий период повтора

def adjust_initial_slots(slots: list[datetime], rpt_type: str, interval: int, now: datetime) -> list[datetime]:
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