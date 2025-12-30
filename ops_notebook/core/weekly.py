from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Tuple


@dataclass
class WeekWindow:
    start: datetime
    end: datetime   # exclusive


def current_week_window_local(now: datetime | None = None) -> WeekWindow:
    """
    Week definition: Monday 00:00 (local) to next Monday 00:00 (local).
    """
    if now is None:
        now = datetime.now().astimezone()
    else:
        if now.tzinfo is None:
            now = now.astimezone()
    
    # Monday=0 ... Sunday=6
    weekday = now.weekday()
    start = (now - timedelta(days=weekday)).replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=7)
    return WeekWindow(start=start, end=end)


def parse_iso_maybe(ts: str | None) -> datetime | None:
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts)
    except Exception:
        return None