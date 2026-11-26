"""Parse binary line headers from SLAP2 data files."""

import datetime as _dt
from decimal import Decimal, ROUND_HALF_EVEN, localcontext
import struct

import numpy as np

from .matlab_datetime import MatlabDatetime


LINE_HEADER_MAGIC = 322379495
_BASE_HEADER = struct.Struct("<IIIIIhhQ")
_Z_FIELDS = struct.Struct("<ff")


def decodeLineHeaderFlags(rawFlags):
    """Decode the flag bitfield stored in a SLAP2 line header."""
    rawFlags = int(rawFlags)
    return {
        "startOfAcq": bool(rawFlags & (1 << 0)),
        "endOfAcq": bool(rawFlags & (1 << 1)),
        "startOfCycle": bool(rawFlags & (1 << 3)),
        "endOfCylce": bool(rawFlags & (1 << 4)),
        "dmdSyncPin": bool(rawFlags & (1 << 5)),
        "syncPending": bool(rawFlags & (1 << 6)),
    }


def decodeLineHeaderTimestamp(timestamp, fpgaSystemClock_Hz=None,
                              referenceTimestamp=None):
    """Convert an FPGA timestamp to seconds relative to a reference tick."""
    if fpgaSystemClock_Hz is None or referenceTimestamp is None:
        return np.nan

    clockHz = float(fpgaSystemClock_Hz)
    if not np.isfinite(clockHz) or clockHz <= 0:
        return np.nan

    return (int(timestamp) - int(referenceTimestamp)) / clockHz


def decodeLineHeaderAbsoluteTimestamp(timestamp, fpgaSystemClock_Hz=None,
                                      fpgaTimeReference=None):
    """Convert an FPGA timestamp to an absolute ``datetime.datetime``.

    Computes the MATLAB-equivalent relationship::

        timestamp_date = fpgaTimeReference + timestamp / fpgaSystemClock_Hz

    Parameters
    ----------
    timestamp : int
        Raw 64-bit FPGA clock tick recorded in the line header.
    fpgaSystemClock_Hz : float, optional
        FPGA clock rate in Hz.
    fpgaTimeReference : datetime.datetime, np.datetime64, or None, optional
        Decoded FPGA time reference (tick 0). Naive ``datetime.datetime``
        inputs produce naive outputs; timezone-aware inputs produce
        timezone-aware outputs in the same timezone (adding elapsed physical
        time in UTC before converting to the target timezone). ``None`` and
        ``np.datetime64('NaT')`` return ``None``.

    Returns
    -------
    datetime.datetime or None
        Absolute line timestamp, or ``None`` when ``fpgaTimeReference`` is
        missing/``NaT`` or ``fpgaSystemClock_Hz`` is missing or non-positive.
    """
    if fpgaTimeReference is None:
        return None
    if isinstance(fpgaTimeReference, np.datetime64):
        if np.isnat(fpgaTimeReference):
            return None
        raise TypeError(
            "fpgaTimeReference must be a datetime.datetime or None"
        )
    if not isinstance(fpgaTimeReference, _dt.datetime):
        raise TypeError(
            f"fpgaTimeReference must be a datetime.datetime or None, got {type(fpgaTimeReference).__name__}"
        )

    if fpgaSystemClock_Hz is None:
        return None
    clockHz = float(fpgaSystemClock_Hz)
    if not np.isfinite(clockHz) or clockHz <= 0:
        return None

    if isinstance(fpgaTimeReference, MatlabDatetime):
        return fpgaTimeReference.add_fpga_ticks(int(timestamp), clockHz)

    with localcontext() as ctx:
        ctx.prec = 50
        clock_dec = (
            Decimal(int(clockHz))
            if clockHz.is_integer()
            else Decimal.from_float(clockHz)
        )
        delta_us = int(
            ((Decimal(int(timestamp)) * Decimal(1_000_000)) / clock_dec).to_integral_value(
                rounding=ROUND_HALF_EVEN
            )
        )

    delta = _dt.timedelta(microseconds=delta_us)
    if fpgaTimeReference.tzinfo is None:
        return fpgaTimeReference + delta

    utc_dt = fpgaTimeReference.astimezone(_dt.timezone.utc) + delta
    if fpgaTimeReference.tzinfo == _dt.timezone.utc:
        return utc_dt
    return utc_dt.astimezone(fpgaTimeReference.tzinfo)


def parseLineHeader(data, fpgaSystemClock_Hz=None, referenceTimestamp=None,
                    fpgaTimeReference=None):
    """Parse a SLAP2 line header, ignoring bytes after the known fields.

    Parameters
    ----------
    data : bytes-like
        Complete binary line header in little-endian byte order.
    fpgaSystemClock_Hz : float, optional
        FPGA clock rate used to derive ``timestamp_s`` and ``timestamp_date``.
    referenceTimestamp : int, optional
        FPGA tick used as zero for ``timestamp_s``.
    fpgaTimeReference : datetime.datetime or None, optional
        Decoded MATLAB ``fpgaTimeReference`` (FPGA tick 0) used to compute
        ``timestamp_date``. When ``None`` or ``NaT``, ``timestamp_date`` is
        ``None``.

    Returns
    -------
    dict
        Parsed fields using the MATLAB reader's public field names, including
        relative ``timestamp_s`` and absolute ``timestamp_date``.
    """
    raw = memoryview(data).cast("B")
    if len(raw) != 32 and len(raw) < 40:
        raise ValueError(
            "SLAP2 line headers must contain exactly 32 or at least 40 bytes"
        )

    (lineSizeBytes, magicNumber, lineNumber, acqNumber, rawFlags,
     xOffset_pix, yOffset_pix, timestamp) = _BASE_HEADER.unpack_from(raw)

    if magicNumber != LINE_HEADER_MAGIC:
        raise ValueError(
            "SLAP2 line-header magic number does not match the expected value"
        )

    if len(raw) >= 40:
        zOffset_um, zFeedback_um = _Z_FIELDS.unpack_from(raw, 32)
    else:
        zOffset_um = 0.0
        zFeedback_um = np.nan

    timestamp_s = decodeLineHeaderTimestamp(
        timestamp,
        fpgaSystemClock_Hz=fpgaSystemClock_Hz,
        referenceTimestamp=referenceTimestamp,
    )
    timestamp_date = decodeLineHeaderAbsoluteTimestamp(
        timestamp,
        fpgaSystemClock_Hz=fpgaSystemClock_Hz,
        fpgaTimeReference=fpgaTimeReference,
    )

    return {
        "lineSizeBytes": np.uint32(lineSizeBytes),
        "magicNumber": np.uint32(magicNumber),
        "lineNumber": np.uint32(lineNumber),
        "acqNumber": np.uint32(acqNumber),
        "rawFlags": np.uint32(rawFlags),
        "xOffset_pix": int(xOffset_pix),
        "yOffset_pix": int(yOffset_pix),
        "timestamp": np.uint64(timestamp),
        "zOffset_um": np.float32(zOffset_um),
        "zFeedback_um": np.float32(zFeedback_um),
        "flags": decodeLineHeaderFlags(rawFlags),
        "timestamp_s": timestamp_s,
        "timestamp_date": timestamp_date,
    }
