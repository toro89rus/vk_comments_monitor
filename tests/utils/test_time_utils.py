from datetime import timedelta

from tatd_bot.utils.time_utils import get_msk_time


def test_get_msk_time_converts_unix_timestamp_to_moscow_time():
    result = get_msk_time(0)

    assert result.utcoffset() == timedelta(hours=3)
    assert (result.year, result.month, result.day, result.hour) == (
        1970,
        1,
        1,
        3,
    )
