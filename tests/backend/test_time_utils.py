from datetime import UTC, datetime

from secureoffice_backend.time_utils import format_moscow_datetime, iso_moscow


def test_moscow_datetime_format_uses_msk_offset():
    value = datetime(2026, 6, 21, 21, 10, 43, tzinfo=UTC)

    assert iso_moscow(value) == "2026-06-22T00:10:43+03:00"
    assert format_moscow_datetime(value) == "22.06.2026 00:10 МСК"
