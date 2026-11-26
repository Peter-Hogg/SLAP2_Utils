import datetime as dt
import struct
from zoneinfo import ZoneInfo

import numpy as np
import pytest

from slap2_utils.utils.line_header import (
    LINE_HEADER_MAGIC,
    decodeLineHeaderAbsoluteTimestamp,
    parseLineHeader,
)
from slap2_utils.utils.matlab_datetime import MatlabDatetime


def make_header(size=40, magic=LINE_HEADER_MAGIC, timestamp=807_174_241_722):
    base = struct.pack(
        "<IIIIIhhQ",
        128,
        magic,
        17,
        23,
        0b01111011,
        -12,
        34,
        timestamp,
    )
    if size >= 40:
        known_fields = base + struct.pack("<ff", 12.5, -3.25)
        return known_fields + bytes(size - len(known_fields))
    return base[:size]


def test_parse_40_byte_line_header():
    ref_dt = dt.datetime(2023, 12, 20, 13, 57, 50)
    header = parseLineHeader(
        make_header(),
        fpgaSystemClock_Hz=200_000_000,
        referenceTimestamp=807_174_241_522,
        fpgaTimeReference=ref_dt,
    )

    assert header["lineSizeBytes"] == np.uint32(128)
    assert header["magicNumber"] == np.uint32(LINE_HEADER_MAGIC)
    assert header["lineNumber"] == np.uint32(17)
    assert header["acqNumber"] == np.uint32(23)
    assert header["rawFlags"] == np.uint32(0b01111011)
    assert header["xOffset_pix"] == -12
    assert header["yOffset_pix"] == 34
    assert header["timestamp"] == np.uint64(807_174_241_722)
    assert header["zOffset_um"] == np.float32(12.5)
    assert header["zFeedback_um"] == np.float32(-3.25)
    assert header["timestamp_s"] == pytest.approx(1e-6)
    assert header["timestamp_date"] == dt.datetime(2023, 12, 20, 15, 5, 5, 871209)
    assert header["timestamp_date"].tzinfo is None
    assert header["flags"] == {
        "startOfAcq": True,
        "endOfAcq": True,
        "startOfCycle": True,
        "endOfCylce": True,
        "dmdSyncPin": True,
        "syncPending": True,
    }


def test_parse_32_byte_line_header_defaults_optional_z_fields():
    header = parseLineHeader(make_header(size=32))

    assert header["zOffset_um"] == np.float32(0)
    assert np.isnan(header["zFeedback_um"])
    assert np.isnan(header["timestamp_s"])
    assert header["timestamp_date"] is None


def test_parse_48_byte_line_header_ignores_extension_bytes():
    header = parseLineHeader(make_header(size=48))

    assert header["lineNumber"] == np.uint32(17)
    assert header["zOffset_um"] == np.float32(12.5)
    assert header["zFeedback_um"] == np.float32(-3.25)
    assert header["timestamp_date"] is None


def test_timestamp_date_missing_and_nat_references_return_none():
    raw = make_header()
    header_none = parseLineHeader(
        raw,
        fpgaSystemClock_Hz=200_000_000,
        referenceTimestamp=807_174_241_522,
        fpgaTimeReference=None,
    )
    assert header_none["timestamp_date"] is None
    assert header_none["timestamp_s"] == pytest.approx(1e-6)

    header_nat = parseLineHeader(
        raw,
        fpgaSystemClock_Hz=200_000_000,
        referenceTimestamp=807_174_241_522,
        fpgaTimeReference=np.datetime64("NaT"),
    )
    assert header_nat["timestamp_date"] is None
    assert header_nat["timestamp_s"] == pytest.approx(1e-6)


def test_timestamp_date_preserves_timezone_and_dst_physical_elapsed_time():
    tz = ZoneInfo("America/New_York")
    # 2024-03-10 01:59:59 EST (-05:00) -> +2 seconds crosses DST spring-forward to 03:00:01 EDT (-04:00)
    ref_aware = dt.datetime(2024, 3, 10, 1, 59, 59, tzinfo=tz)
    header = parseLineHeader(
        make_header(timestamp=400_000_000),
        fpgaSystemClock_Hz=200_000_000,
        referenceTimestamp=200_000_000,
        fpgaTimeReference=ref_aware,
    )

    assert header["timestamp_s"] == pytest.approx(1.0)
    assert header["timestamp_date"] == dt.datetime(2024, 3, 10, 3, 0, 1, tzinfo=tz)
    assert header["timestamp_date"].utcoffset() == dt.timedelta(hours=-4)


def test_timestamp_date_matlab_datetime_avoids_double_rounding_drift():
    ref = MatlabDatetime.from_epoch_milliseconds(
        1703080670029.5525, 6.476303218505564e-05
    )
    out = decodeLineHeaderAbsoluteTimestamp(
        807_174_241_522,
        fpgaSystemClock_Hz=200_000_000,
        fpgaTimeReference=ref,
    )
    assert out == dt.datetime(2023, 12, 20, 15, 5, 5, 900760)


@pytest.mark.parametrize("bad_clock", [None, 0, -100, np.nan, np.inf])
def test_timestamp_date_invalid_clock_returns_none(bad_clock):
    ref_dt = dt.datetime(2023, 12, 20, 13, 57, 50)
    assert decodeLineHeaderAbsoluteTimestamp(1000, bad_clock, ref_dt) is None


def test_timestamp_date_rejects_invalid_reference_type():
    with pytest.raises(TypeError, match="datetime.datetime or None"):
        decodeLineHeaderAbsoluteTimestamp(
            1000, fpgaSystemClock_Hz=200_000_000, fpgaTimeReference="2023-12-20"
        )


@pytest.mark.parametrize("size", [0, 31, 33, 39])
def test_parse_line_header_rejects_unsupported_lengths(size):
    with pytest.raises(ValueError, match="exactly 32 or at least 40 bytes"):
        parseLineHeader(bytes(size))


def test_parse_line_header_rejects_wrong_magic_number():
    with pytest.raises(ValueError, match="magic number"):
        parseLineHeader(make_header(magic=1))
