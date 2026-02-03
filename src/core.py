from src.database import Database
from datetime import datetime, timedelta, time as dtime
from contextlib import contextmanager


def midnight_range_for_yesterday():
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday = today - timedelta(days=1)
    return int(yesterday.timestamp()), int(today.timestamp())
