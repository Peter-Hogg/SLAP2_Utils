"""Decode MATLAB ``datetime`` objects stored in HDF5 (MAT v7.3 / ``.meta``) files."""

import datetime as _dt
from decimal import Decimal, ROUND_HALF_EVEN, localcontext
import math
import re
import struct
from typing import Any, Dict, List, Optional, Tuple
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import h5py
import numpy as np


MCOS_MAGIC = 0xDD000000  # 3707764736

# Cumulative TAI-UTC leap-second table (UTC instant in ms since 1970-01-01 -> leap seconds added since 1972)
# Used only when MATLAB datetime TimeZone == 'UTCLeapSeconds'.
_LEAP_SECOND_EPOCHS_UTC_MS: Tuple[Tuple[int, int], ...] = (
    (78796800000, 1),     # 1972-07-01
    (94694400000, 2),     # 1973-01-01
    (126230400000, 3),    # 1974-01-01
    (157766400000, 4),    # 1975-01-01
    (189302400000, 5),    # 1976-01-01
    (220924800000, 6),    # 1977-01-01
    (252460800000, 7),    # 1978-01-01
    (283996800000, 8),    # 1979-01-01
    (315532800000, 9),    # 1980-01-01
    (362793600000, 10),   # 1981-07-01
    (394329600000, 11),   # 1982-07-01
    (425865600000, 12),   # 1983-07-01
    (489024000000, 13),   # 1985-07-01
    (567993600000, 14),   # 1988-01-01
    (631152000000, 15),   # 1990-01-01
    (662688000000, 16),   # 1991-01-01
    (709948800000, 17),   # 1992-07-01
    (741484800000, 18),   # 1993-07-01
    (773020800000, 19),   # 1994-07-01
    (820454400000, 20),   # 1996-01-01
    (867715200000, 21),   # 1997-07-01
    (915148800000, 22),   # 1999-01-01
    (1136073600000, 23),  # 2006-01-01
    (1230768000000, 24),  # 2009-01-01
    (1341100800000, 25),  # 2012-07-01
    (1435708800000, 26),  # 2015-07-01
    (1483228800000, 27),  # 2017-01-01
)

_FIXED_OFFSET_RE = re.compile(
    r"^(?:UTC)?([+-])(\d{1,2})(?::?(\d{2}))?$", re.IGNORECASE
)


def _rebuild_matlab_datetime(
    year: int,
    month: int,
    day: int,
    hour: int,
    minute: int,
    second: int,
    microsecond: int,
    tzinfo: Optional[_dt.tzinfo],
    fold: int,
    epoch_ms_str: str,
) -> "MatlabDatetime":
    instance = MatlabDatetime.__new__(
        MatlabDatetime,
        year,
        month,
        day,
        hour,
        minute,
        second,
        microsecond,
        tzinfo=tzinfo,
        fold=fold,
    )
    instance._epoch_ms = Decimal(epoch_ms_str)
    return instance


class MatlabDatetime(_dt.datetime):
    """A ``datetime.datetime`` subclass retaining MATLAB's sub-microsecond epoch milliseconds.

    Behaves identically to ``datetime.datetime`` while preserving the full
    double-double millisecond value stored by MATLAB so that adding FPGA clock
    ticks via ``add_fpga_ticks`` avoids double-rounding drift relative to
    MATLAB's ``(fpgaTimeReference + secondsint) + secondsfrac``.
    """

    __slots__ = ("_epoch_ms",)

    @classmethod
    def from_epoch_milliseconds(
        cls,
        real_ms: float,
        imag_ms: float = 0.0,
        tz_str: str = "",
    ) -> Optional["MatlabDatetime"]:
        """Construct a ``MatlabDatetime`` from MATLAB ``data`` milliseconds and ``tz``."""
        if not (math.isfinite(real_ms) and math.isfinite(imag_ms)):
            return None

        with localcontext() as ctx:
            ctx.prec = 50
            epoch_ms = Decimal.from_float(float(real_ms)) + Decimal.from_float(float(imag_ms))
            tz_clean = tz_str.strip()
            if tz_clean == "UTCLeapSeconds":
                leap_s = 0
                for threshold_ms, count in _LEAP_SECOND_EPOCHS_UTC_MS:
                    if epoch_ms >= Decimal(threshold_ms + count * 1000):
                        leap_s = count
                    else:
                        break
                epoch_ms = epoch_ms - Decimal(leap_s * 1000)
                tzinfo: Optional[_dt.tzinfo] = _dt.timezone.utc
            else:
                tzinfo = parse_matlab_timezone(tz_clean)

            epoch_us = int(
                (epoch_ms * Decimal(1000)).to_integral_value(rounding=ROUND_HALF_EVEN)
            )

        if tzinfo is None:
            base = _dt.datetime(1970, 1, 1) + _dt.timedelta(microseconds=epoch_us)
        else:
            utc_dt = _dt.datetime(1970, 1, 1, tzinfo=_dt.timezone.utc) + _dt.timedelta(
                microseconds=epoch_us
            )
            base = utc_dt if tzinfo == _dt.timezone.utc else utc_dt.astimezone(tzinfo)

        obj = cls.__new__(
            cls,
            base.year,
            base.month,
            base.day,
            base.hour,
            base.minute,
            base.second,
            base.microsecond,
            tzinfo=base.tzinfo,
            fold=base.fold,
        )
        obj._epoch_ms = epoch_ms
        return obj

    def add_fpga_ticks(self, ticks: int, clock_hz: float) -> _dt.datetime:
        """Add ``ticks / clock_hz`` seconds with full sub-microsecond precision."""
        with localcontext() as ctx:
            ctx.prec = 50
            clock_dec = (
                Decimal(int(clock_hz))
                if float(clock_hz).is_integer()
                else Decimal.from_float(float(clock_hz))
            )
            delta_us = (Decimal(int(ticks)) * Decimal(1_000_000)) / clock_dec
            total_us = int(
                (self._epoch_ms * Decimal(1000) + delta_us).to_integral_value(
                    rounding=ROUND_HALF_EVEN
                )
            )

        if self.tzinfo is None:
            return _dt.datetime(1970, 1, 1) + _dt.timedelta(microseconds=total_us)

        utc_dt = _dt.datetime(1970, 1, 1, tzinfo=_dt.timezone.utc) + _dt.timedelta(
            microseconds=total_us
        )
        return utc_dt if self.tzinfo == _dt.timezone.utc else utc_dt.astimezone(self.tzinfo)

    def __reduce__(self):
        return (
            _rebuild_matlab_datetime,
            (
                self.year,
                self.month,
                self.day,
                self.hour,
                self.minute,
                self.second,
                self.microsecond,
                self.tzinfo,
                self.fold,
                str(getattr(self, "_epoch_ms", Decimal(0))),
            ),
        )

    def __reduce_ex__(self, protocol):
        return self.__reduce__()


def parse_matlab_timezone(tz_str: str) -> Optional[_dt.tzinfo]:
    """Convert a MATLAB ``datetime.TimeZone`` string into a Python ``tzinfo`` object.

    Unzoned MATLAB datetimes (``tz_str == ""``) map to ``None`` (naive
    ``datetime.datetime``). Zoned MATLAB datetimes map to
    ``datetime.timezone.utc``, fixed-offset ``datetime.timezone``, or
    ``zoneinfo.ZoneInfo``.
    """
    tz = tz_str.strip()
    if not tz:
        return None

    if tz.upper() in ("UTC", "Z", "ETC/UTC", "GMT", "ETC/GMT"):
        return _dt.timezone.utc

    match = _FIXED_OFFSET_RE.match(tz)
    if match:
        sign = 1 if match.group(1) == "+" else -1
        hours = int(match.group(2))
        minutes = int(match.group(3) or "0")
        if hours > 23 or minutes > 59 or (hours == 23 and minutes > 59):
            raise ValueError(f"Invalid UTC offset in MATLAB timezone: {tz_str!r}")
        offset = _dt.timedelta(hours=hours, minutes=minutes) * sign
        return _dt.timezone(offset)

    try:
        return ZoneInfo(tz)
    except (ZoneInfoNotFoundError, KeyError, ValueError) as exc:
        raise ValueError(f"Unsupported MATLAB timezone: {tz_str!r}") from exc


def _decode_attr_str(val: Any) -> str:
    if isinstance(val, bytes):
        return val.decode("utf-8", errors="replace")
    if isinstance(val, np.ndarray) and val.size == 1:
        item = val.reshape(-1)[0]
        if isinstance(item, bytes):
            return item.decode("utf-8", errors="replace")
        return str(item)
    return str(val) if val is not None else ""


def _decode_hdf5_char(ds: h5py.Dataset) -> str:
    if ds.attrs.get("MATLAB_empty") == 1:
        return ""
    arr = ds[()]
    if isinstance(arr, bytes):
        return arr.decode("utf-8", errors="replace")
    if isinstance(arr, str):
        return arr
    arr = np.asarray(arr)
    if arr.size == 0:
        return ""
    if arr.dtype.kind in ("u", "i"):
        return "".join(chr(int(c)) for c in arr.ravel(order="F") if int(c) != 0)
    if arr.dtype.kind == "S":
        return b"".join(arr.ravel(order="F")).decode("utf-8", errors="replace")
    if arr.dtype.kind == "U":
        return "".join(arr.ravel(order="F"))
    raise ValueError(f"Unsupported HDF5 char dataset dtype: {arr.dtype}")


def _extract_epoch_ms_pair(raw_data: Any) -> Optional[Tuple[float, float]]:
    """Extract ``(real_ms, imag_ms)`` from a MATLAB ``datetime.data`` array/dataset."""
    if isinstance(raw_data, h5py.Dataset):
        if raw_data.attrs.get("MATLAB_empty") == 1:
            return None
        arr = raw_data[()]
    else:
        arr = raw_data

    arr = np.asarray(arr)
    if arr.size == 0:
        return None
    if arr.size != 1:
        raise ValueError(
            f"Expected scalar MATLAB datetime data array, got shape {arr.shape}"
        )

    elem = arr.reshape(-1)[0]
    if arr.dtype.names and "real" in arr.dtype.names:
        real_ms = float(elem["real"])
        imag_ms = float(elem["imag"]) if "imag" in arr.dtype.names else 0.0
        return real_ms, imag_ms
    if np.iscomplexobj(arr):
        return float(np.real(elem)), float(np.imag(elem))
    if arr.dtype.kind in ("f", "i", "u"):
        return float(elem), 0.0

    raise ValueError(f"Unsupported MATLAB datetime data dtype: {arr.dtype}")


def _parse_property_blocks(
    segment_bytes: bytes,
    strings: List[str],
    mcos_refs: np.ndarray,
    hdf_file: h5py.File,
) -> List[Dict[str, Any]]:
    """Parse MCOS Segment 1 or Segment 3 property blocks (1-based block index; block 0 is empty)."""
    blocks: List[Dict[str, Any]] = [{}]
    if len(segment_bytes) <= 8:
        return blocks

    pos = 8  # First 8 bytes are reserved sentinel block 0
    limit = len(segment_bytes)
    while pos + 4 <= limit:
        (n_props,) = struct.unpack_from("<I", segment_bytes, pos)
        block_size = 4 + 12 * n_props
        aligned_size = (block_size + 7) & ~7
        if pos + block_size > limit:
            raise ValueError("Truncated MCOS property block in FileWrapper__")

        props: Dict[str, Any] = {}
        entry_pos = pos + 4
        for _ in range(n_props):
            name_idx, field_type, raw_val = struct.unpack_from("<3I", segment_bytes, entry_pos)
            entry_pos += 12
            if name_idx < 1 or name_idx > len(strings):
                raise ValueError(f"MCOS property name index {name_idx} out of range")
            prop_name = strings[name_idx - 1]

            if field_type == 0:
                props[prop_name] = strings[raw_val - 1] if 1 <= raw_val <= len(strings) else ""
            elif field_type == 1:
                heap_idx = 2 + raw_val
                if heap_idx >= len(mcos_refs):
                    raise ValueError(f"MCOS heap index {heap_idx} exceeds MCOS reference table")
                props[prop_name] = hdf_file[mcos_refs[heap_idx]]
            elif field_type == 2:
                props[prop_name] = raw_val
            else:
                props[prop_name] = raw_val

        blocks.append(props)
        pos += aligned_size

    return blocks


def _decode_mcos_datetime(
    hdf_file: h5py.File,
    raw_u32: np.ndarray,
) -> Optional[MatlabDatetime]:
    """Decode a MATLAB MCOS ``datetime`` dataset from ``/#subsystem#/MCOS``."""
    vec = np.asarray(raw_u32, dtype=np.uint32).ravel()
    if vec.size < 5 or int(vec[0]) != MCOS_MAGIC:
        raise ValueError("Invalid MCOS object header for MATLAB datetime")

    ndims = int(vec[1])
    if ndims < 1 or vec.size < 2 + ndims + 1:
        raise ValueError("Malformed dimensions in MCOS datetime header")

    dims = [int(x) for x in vec[2:2 + ndims]]
    count = math.prod(dims)
    expected_len = 2 + ndims + count + 1
    if vec.size != expected_len:
        raise ValueError(
            f"Unexpected MCOS datetime header length {vec.size} (expected {expected_len})"
        )

    if count == 0:
        return None
    if count != 1:
        raise ValueError(
            f"Expected scalar MATLAB datetime, got array dimensions {tuple(dims)}"
        )

    object_id = int(vec[2 + ndims])
    class_id = int(vec[-1])

    if "#subsystem#" not in hdf_file or "MCOS" not in hdf_file["#subsystem#"]:
        raise ValueError("Missing /#subsystem#/MCOS table required to decode MATLAB datetime")

    mcos_refs = hdf_file["#subsystem#"]["MCOS"][()].ravel()
    if mcos_refs.size < 2:
        raise ValueError("Incomplete /#subsystem#/MCOS reference array")

    fw_bytes = hdf_file[mcos_refs[0]][()].tobytes()
    if len(fw_bytes) < 32:
        raise ValueError("Truncated MCOS FileWrapper__ stream")

    version, num_strings = struct.unpack_from("<2I", fw_bytes, 0)
    if version == 2:
        num_offsets = 6
        header_bytes = 32
    elif version >= 3:
        num_offsets = 8
        header_bytes = 40
    else:
        raise ValueError(f"Unsupported MCOS FileWrapper__ version: {version}")

    if len(fw_bytes) < header_bytes:
        raise ValueError("Truncated MCOS FileWrapper__ segment header")

    offsets = struct.unpack_from(f"<{num_offsets}I", fw_bytes, 8)
    if (
        offsets[0] < header_bytes
        or any(offsets[i] > offsets[i + 1] for i in range(len(offsets) - 1))
        or offsets[-1] > len(fw_bytes)
    ):
        raise ValueError("Invalid segment offsets in MCOS FileWrapper__")

    raw_strings = fw_bytes[header_bytes:offsets[0]].split(b"\x00")
    if len(raw_strings) < num_strings:
        raise ValueError("Truncated string table in MCOS FileWrapper__")
    strings = [s.decode("utf-8", errors="replace") for s in raw_strings[:num_strings]]

    # Segment 0: Class table (16 bytes per entry; index 0 is empty sentinel)
    seg0 = fw_bytes[offsets[0]:offsets[1]]
    if len(seg0) % 16 != 0:
        raise ValueError("Corrupt MCOS class table")
    num_class_entries = len(seg0) // 16
    if class_id < 1 or class_id >= num_class_entries:
        raise ValueError(f"MCOS class_id {class_id} out of range")

    pkg_str_idx, cls_str_idx, _, _ = struct.unpack_from("<4I", seg0, class_id * 16)
    pkg_name = strings[pkg_str_idx - 1] if pkg_str_idx else ""
    cls_name = strings[cls_str_idx - 1] if cls_str_idx else ""
    if pkg_name != "" or cls_name != "datetime":
        raise ValueError(
            f"Expected MATLAB class 'datetime', got '{pkg_name + '.' if pkg_name else ''}{cls_name}'"
        )

    merged_props: Dict[str, Any] = {}

    # Load class-level default properties from MCOS[-1][class_id] when present
    last_target = hdf_file[mcos_refs[-1]]
    if (
        isinstance(last_target, h5py.Dataset)
        and _decode_attr_str(last_target.attrs.get("MATLAB_class")) == "cell"
    ):
        defaults_refs = last_target[()].ravel()
        if class_id < defaults_refs.size:
            class_defaults = hdf_file[defaults_refs[class_id]]
            if isinstance(class_defaults, h5py.Group):
                for prop_key in class_defaults.keys():
                    merged_props[prop_key] = class_defaults[prop_key]

    # Overlay instance properties from Segment 1 (saveobj) and Segment 3 (normal)
    if object_id > 0:
        seg2 = fw_bytes[offsets[2]:offsets[3]]
        if len(seg2) % 24 != 0 or object_id >= len(seg2) // 24:
            raise ValueError(f"MCOS object_id {object_id} out of range")

        obj_cls_id, _, _, saveobj_prop_id, normal_prop_id, _ = struct.unpack_from(
            "<6I", seg2, object_id * 24
        )
        if obj_cls_id != class_id:
            raise ValueError(
                f"MCOS object class mismatch ({obj_cls_id} != {class_id})"
            )

        if saveobj_prop_id > 0:
            seg1_blocks = _parse_property_blocks(
                fw_bytes[offsets[1]:offsets[2]], strings, mcos_refs, hdf_file
            )
            if saveobj_prop_id >= len(seg1_blocks):
                raise ValueError(f"MCOS saveobj property block {saveobj_prop_id} out of range")
            merged_props.update(seg1_blocks[saveobj_prop_id])

        if normal_prop_id > 0:
            seg3_blocks = _parse_property_blocks(
                fw_bytes[offsets[3]:offsets[4]], strings, mcos_refs, hdf_file
            )
            if normal_prop_id >= len(seg3_blocks):
                raise ValueError(f"MCOS property block {normal_prop_id} out of range")
            merged_props.update(seg3_blocks[normal_prop_id])

    return _props_to_matlab_datetime(merged_props)


def _props_to_matlab_datetime(props: Dict[str, Any]) -> Optional[MatlabDatetime]:
    if "data" not in props:
        raise ValueError("Decoded MATLAB datetime object is missing 'data' property")

    ms_pair = _extract_epoch_ms_pair(props["data"])
    if ms_pair is None:
        return None

    tz_val = props.get("tz", "")
    if isinstance(tz_val, h5py.Dataset):
        tz_str = _decode_hdf5_char(tz_val)
    elif isinstance(tz_val, bytes):
        tz_str = tz_val.decode("utf-8", errors="replace")
    elif isinstance(tz_val, str):
        tz_str = tz_val
    else:
        tz_str = ""

    return MatlabDatetime.from_epoch_milliseconds(ms_pair[0], ms_pair[1], tz_str=tz_str)


def decode_matlab_datetime(
    hdf_file: h5py.File,
    obj: Any,
) -> Optional[MatlabDatetime]:
    """Decode a MATLAB ``datetime`` dataset or group from an open HDF5 ``.meta`` file.

    Parameters
    ----------
    hdf_file : h5py.File
        Open HDF5 file handle containing the dataset/group (and ``/#subsystem#/MCOS``
        when MCOS object encoding is used).
    obj : h5py.Dataset or h5py.Group
        Dataset or group representing the MATLAB ``datetime`` value.

    Returns
    -------
    MatlabDatetime or None
        A ``datetime.datetime`` instance (naive when the MATLAB ``datetime``
        is unzoned, or timezone-aware when ``TimeZone`` is set), or ``None`` for
        empty MATLAB ``datetime`` arrays and ``NaT``.
    """
    if obj is None:
        return None

    if isinstance(obj, h5py.Group):
        if "data" in obj:
            props: Dict[str, Any] = {k: obj[k] for k in obj.keys()}
            return _props_to_matlab_datetime(props)
        raise ValueError(f"Unsupported HDF5 group structure for MATLAB datetime: {list(obj.keys())}")

    if not isinstance(obj, h5py.Dataset):
        raise TypeError(f"Expected h5py.Dataset or h5py.Group, got {type(obj).__name__}")

    if obj.attrs.get("MATLAB_empty") == 1:
        return None

    matlab_class = _decode_attr_str(obj.attrs.get("MATLAB_class"))
    arr = obj[()]

    if matlab_class == "char" or (isinstance(arr, (bytes, str))) or (
        isinstance(arr, np.ndarray) and arr.dtype.kind in ("S", "U")
    ):
        text = _decode_hdf5_char(obj).strip()
        if not text or text.lower() == "nat":
            return None
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        parsed = _dt.datetime.fromisoformat(text)
        epoch_ref = (
            _dt.datetime(1970, 1, 1)
            if parsed.tzinfo is None
            else _dt.datetime(1970, 1, 1, tzinfo=_dt.timezone.utc)
        )
        target = parsed if parsed.tzinfo is None else parsed.astimezone(_dt.timezone.utc)
        delta = target - epoch_ref
        ms = (
            Decimal(delta.days * 86_400_000 + delta.seconds * 1_000)
            + Decimal(delta.microseconds) / Decimal(1000)
        )
        out = MatlabDatetime.__new__(
            MatlabDatetime,
            parsed.year,
            parsed.month,
            parsed.day,
            parsed.hour,
            parsed.minute,
            parsed.second,
            parsed.microsecond,
            tzinfo=parsed.tzinfo,
            fold=parsed.fold,
        )
        out._epoch_ms = ms
        return out

    arr_np = np.asarray(arr)
    if arr_np.size == 0:
        return None

    if (
        matlab_class == "datetime"
        or obj.attrs.get("MATLAB_object_decode") == 3
        or (arr_np.dtype == np.uint32 and arr_np.size >= 5 and int(arr_np.ravel()[0]) == MCOS_MAGIC)
    ):
        if arr_np.dtype.kind == "u":
            return _decode_mcos_datetime(hdf_file, arr_np)

    raise ValueError(
        f"Unsupported HDF5 representation for MATLAB datetime "
        f"(MATLAB_class={matlab_class!r}, dtype={arr_np.dtype}, shape={arr_np.shape})"
    )
