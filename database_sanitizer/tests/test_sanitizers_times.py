import datetime

import mock

from database_sanitizer.sanitizers import times


class _FakeDateTime(datetime.datetime):
    @staticmethod
    def now():
        return datetime.datetime(2018, 1, 1, 12, 00, 00)


@mock.patch('random.randint', return_value=42005)
@mock.patch.object(datetime, 'datetime', _FakeDateTime)
def test_sanitize_random_past_timestamp(randint_mock):
    assert times.sanitize_random_past_timestamp('old') == (
        '2018-01-01T11:59:17.995000')
