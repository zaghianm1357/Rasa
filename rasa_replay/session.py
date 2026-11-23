from datetime import datetime, time
from zoneinfo import ZoneInfo

SESSION_TZ = ZoneInfo("Asia/Tehran")
SESSION_START = time(7, 0)
SESSION_END = time(23, 0)

def is_inside_session(timestamp: datetime) -> bool:
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise ValueError("Session check requires timezone-aware datetime")
    local = timestamp.astimezone(SESSION_TZ).timetz().replace(tzinfo=None)
    return SESSION_START <= local < SESSION_END
