from datetime import datetime, timezone
from zoneinfo import ZoneInfo


def get_msk_time(timestamp: float) -> datetime:
    dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
    dt_msk = dt.astimezone(ZoneInfo("Europe/Moscow"))
    return dt_msk
