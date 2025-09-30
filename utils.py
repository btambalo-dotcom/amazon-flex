
from datetime import datetime

def parse_dt(value: str) -> datetime | None:
    if not value:
        return None
    # Aceita 'YYYY-MM-DDTHH:MM' (input[type=datetime-local]) ou 'YYYY-MM-DD HH:MM'
    fmts = ['%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M']
    for f in fmts:
        try:
            return datetime.strptime(value, f)
        except ValueError:
            pass
    return None

def hours_between(start, end) -> float:
    if not start or not end:
        return 0.0
    delta = end - start
    return round(delta.total_seconds() / 3600.0, 2)
