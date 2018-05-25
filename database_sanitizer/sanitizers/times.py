import datetime
import random

TEN_YEARS_AS_SECONDS = 10 * 365 * 24 * 3600


def sanitize_random_past_timestamp(value):
    num = random.randint(0, TEN_YEARS_AS_SECONDS * 1000)
    delta = datetime.timedelta(seconds=(num / 1000.0))
    dt = datetime.datetime.now() - delta
    return dt.isoformat()
