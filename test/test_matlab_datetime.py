import datetime as dt
import os
import pickle
import shutil
import struct
from zoneinfo import ZoneInfo

import h5py
import numpy as np
import pytest

from slap2_utils.subclasses.metadata import MetaData
from slap2_utils.utils.matlab_datetime import (
    MCOS_MAGIC,
    MatlabDatetime,
    decode_matlab_datetime,
    parse_matlab_timezone,
)


def _align8(buf: bytes) -> bytes:
    rem = len(buf) % 8
    return buf if rem == 0 else buf + b"\x00" * (8 - rem)


def _write_synthetic_mcos_datetime_hdf5(
    path: str,
    *,
    real_ms: float,
    imag_ms: float = 0.0,
    complex_data: bool = True,
    tz_in_defaults: str = "",
    tz_in_instance_str: str = "",
    tz_in_instance_heap: str = "",
    mcos_version: int = 4,
    use_saveobj_segment: bool = False,
    dims=(1, 1),
):
    """Build a minimal MAT-v7.3 HDF5 file encoding a MATLAB MCOS datetime."""
    strings = ["data", "datetime", "fmt", "tz"]
    if tz_in_instance_str:
        strings.append(tz_in_instance_str)

    str_blob = _align8(b"\x00".join(s.encode("utf-8") for s in strings) + b"\x00")

    # Segment 0: sentinel + class 1 ('', 'datetime')
    seg0 = struct.pack("<4I", 0, 0, 0, 0) + struct.pack("<4I", 0, 2, 0, 0)

    # Property entries: ('data', field_type=1, heap_idx=0) + optional tz
    props = [(1, 1, 0)]
    if tz_in_instance_str:
        props.append((4, 0, 5))
    elif tz_in_instance_heap:
        props.append((4, 1, 1))

    prop_block = struct.pack("<I", len(props))
    for p in props:
        prop_block += struct.pack("<3I", *p)
    prop_block = _align8(prop_block)
    prop_segment = b"\x00" * 8 + prop_block

    if use_saveobj_segment:
        seg1 = prop_segment
        seg3 = b"\x00" * 8
        saveobj_id, normal_id = 1, 0
    else:
        seg1 = b""
        seg3 = prop_segment
        saveobj_id, normal_id = 0, 1

    count = int(np.prod(dims))
    if count > 0:
        seg2 = struct.pack("<6I", 0, 0, 0, 0, 0, 0) + struct.pack(
            "<6I", 1, 0, 0, saveobj_id, normal_id, 1
        )
    else:
        seg2 = struct.pack("<6I", 0, 0, 0, 0, 0, 0)
    seg4 = b"\x00" * 8

    header_len = 32 if mcos_version == 2 else 40
    off0 = header_len + len(str_blob)
    off1 = off0 + len(seg0)
    off2 = off1 + len(seg1)
    off3 = off2 + len(seg2)
    off4 = off3 + len(seg3)
    off5 = off4 + len(seg4)

    if mcos_version == 2:
        header = struct.pack(
            "<8I", mcos_version, len(strings), off0, off1, off2, off3, off4, off5
        )
        fw_bytes = header + str_blob + seg0 + seg1 + seg2 + seg3 + seg4
    else:
        seg6 = b"\x00" * 8
        off6 = off5
        off7 = off6 + len(seg6)
        header = struct.pack(
            "<10I",
            mcos_version,
            len(strings),
            off0,
            off1,
            off2,
            off3,
            off4,
            off5,
            off6,
            off7,
        )
        fw_bytes = header + str_blob + seg0 + seg1 + seg2 + seg3 + seg4 + seg6

    with h5py.File(path, "w") as f:
        refs = f.create_group("#refs#")
        sub = f.create_group("#subsystem#")

        fw_ds = refs.create_dataset(
            "fw", data=np.frombuffer(fw_bytes, dtype=np.uint8).reshape(1, -1)
        )
        empty_ds = refs.create_dataset("empty", data=np.array([0, 0], dtype=np.uint64))
        empty_ds.attrs["MATLAB_empty"] = 1

        if complex_data:
            dt_complex = np.dtype([("real", "<f8"), ("imag", "<f8")])
            data_arr = np.array([[(real_ms, imag_ms)]], dtype=dt_complex)
        else:
            data_arr = np.array([[real_ms]], dtype=np.float64)
        data_ds = refs.create_dataset("data0", data=data_arr)

        heap_refs = [fw_ds.ref, empty_ds.ref, data_ds.ref]

        if tz_in_instance_heap:
            tz_u16 = np.array(
                [[ord(c)] for c in tz_in_instance_heap], dtype=np.uint16
            )
            tz_heap_ds = refs.create_dataset("tz_heap", data=tz_u16)
            tz_heap_ds.attrs["MATLAB_class"] = b"char"
            heap_refs.append(tz_heap_ds.ref)

        # Class defaults cell array at MCOS[-1]
        def0 = refs.create_dataset("def0", data=np.array([1, 0], dtype=np.uint64))
        def0.attrs["MATLAB_class"] = b"struct"
        def0.attrs["MATLAB_empty"] = 1

        def1 = refs.create_group("def1")
        def1.attrs["MATLAB_class"] = b"struct"
        fmt_ds = def1.create_dataset("fmt", data=np.array([0, 0], dtype=np.uint64))
        fmt_ds.attrs["MATLAB_class"] = b"char"
        fmt_ds.attrs["MATLAB_empty"] = 1
        if tz_in_defaults:
            tz_u16 = np.array([[ord(c)] for c in tz_in_defaults], dtype=np.uint16)
            tz_ds = def1.create_dataset("tz", data=tz_u16)
            tz_ds.attrs["MATLAB_class"] = b"char"
        else:
            tz_ds = def1.create_dataset("tz", data=np.array([0, 0], dtype=np.uint64))
            tz_ds.attrs["MATLAB_class"] = b"char"
            tz_ds.attrs["MATLAB_empty"] = 1

        defaults_cell = refs.create_dataset(
            "defaults_cell",
            data=np.array([[def0.ref, def1.ref]], dtype=h5py.ref_dtype),
        )
        defaults_cell.attrs["MATLAB_class"] = b"cell"
        heap_refs.append(defaults_cell.ref)

        sub.create_dataset(
            "MCOS", data=np.array([heap_refs], dtype=h5py.ref_dtype)
        )

        obj_ids = [1] * count
        header_vec = np.array(
            [[MCOS_MAGIC, len(dims), *dims, *obj_ids, 1]], dtype=np.uint32
        )
        ref_ds = f.create_dataset("fpgaTimeReference", data=header_vec)
        ref_ds.attrs["MATLAB_class"] = b"datetime"
        ref_ds.attrs["MATLAB_object_decode"] = 3


def test_real_metadata_fixtures_decode_fpga_time_reference():
    test_dir = os.path.dirname(__file__)
    repo_root = os.path.dirname(test_dir)

    meta1 = MetaData(os.path.join(test_dir, "testFile.meta"))
    assert isinstance(meta1.fpgaTimeReference, dt.datetime)
    assert meta1.fpgaTimeReference == dt.datetime(2023, 12, 20, 13, 57, 50, 29553)
    assert meta1.fpgaTimeReference.tzinfo is None

    example_meta = os.path.join(
        repo_root, "slap2_utils", "examples", "3DExampleScan.meta"
    )
    meta2 = MetaData(example_meta)
    assert isinstance(meta2.fpgaTimeReference, dt.datetime)
    assert meta2.fpgaTimeReference == dt.datetime(2023, 12, 20, 13, 57, 50, 34155)
    assert meta2.fpgaTimeReference.tzinfo is None


def test_metadata_missing_and_nat_fpga_time_reference(tmp_path):
    src_meta = os.path.join(os.path.dirname(__file__), "testFile.meta")

    # Case 1: fpgaTimeReference absent from .meta
    missing_meta = tmp_path / "missing_ref.meta"
    shutil.copyfile(src_meta, missing_meta)
    with h5py.File(missing_meta, "r+") as f:
        del f["fpgaTimeReference"]
    loaded_missing = MetaData(str(missing_meta))
    assert loaded_missing.fpgaTimeReference is None

    # Case 2: fpgaTimeReference is MATLAB NaT (NaN milliseconds in MCOS data)
    nat_meta = tmp_path / "nat_ref.meta"
    shutil.copyfile(src_meta, nat_meta)
    with h5py.File(nat_meta, "r+") as f:
        mcos = f["#subsystem#"]["MCOS"][()].ravel()
        dt_ds = f[mcos[2]]
        dt_ds[()] = np.array([[(np.nan, 0.0)]], dtype=dt_ds.dtype)
    loaded_nat = MetaData(str(nat_meta))
    assert loaded_nat.fpgaTimeReference is None


@pytest.mark.parametrize("mcos_version", [2, 3, 4])
def test_decode_mcos_versions_and_saveobj_layout(tmp_path, mcos_version):
    p = tmp_path / f"v{mcos_version}.meta"
    _write_synthetic_mcos_datetime_hdf5(
        str(p),
        real_ms=1700000000123.0,
        imag_ms=0.456,
        complex_data=(mcos_version != 2),
        mcos_version=mcos_version,
        use_saveobj_segment=(mcos_version == 3),
    )
    with h5py.File(p, "r") as f:
        decoded = decode_matlab_datetime(f, f["fpgaTimeReference"])

    expected_us = 123456 if mcos_version != 2 else 123000
    assert decoded == dt.datetime(2023, 11, 14, 22, 13, 20, expected_us)
    assert decoded.tzinfo is None


def test_decode_zoned_matlab_datetimes(tmp_path):
    # UTC via class defaults
    utc_file = tmp_path / "utc.meta"
    _write_synthetic_mcos_datetime_hdf5(
        str(utc_file), real_ms=1700000000000.0, tz_in_defaults="UTC"
    )
    with h5py.File(utc_file, "r") as f:
        dt_utc = decode_matlab_datetime(f, f["fpgaTimeReference"])
    assert dt_utc == dt.datetime(2023, 11, 14, 22, 13, 20, tzinfo=dt.timezone.utc)
    assert dt_utc.tzinfo == dt.timezone.utc

    # IANA timezone via inline MCOS string table (field_type == 0)
    ny_file = tmp_path / "ny_str.meta"
    _write_synthetic_mcos_datetime_hdf5(
        str(ny_file),
        real_ms=1700000000000.0,
        tz_in_instance_str="America/New_York",
    )
    with h5py.File(ny_file, "r") as f:
        dt_ny = decode_matlab_datetime(f, f["fpgaTimeReference"])
    assert dt_ny == dt.datetime(
        2023, 11, 14, 17, 13, 20, tzinfo=ZoneInfo("America/New_York")
    )
    assert dt_ny.utcoffset() == dt.timedelta(hours=-5)

    # Fixed offset via heap char dataset (field_type == 1)
    offset_file = tmp_path / "offset_heap.meta"
    _write_synthetic_mcos_datetime_hdf5(
        str(offset_file),
        real_ms=1700000000000.0,
        tz_in_instance_heap="+02:00",
    )
    with h5py.File(offset_file, "r") as f:
        dt_off = decode_matlab_datetime(f, f["fpgaTimeReference"])
    assert dt_off == dt.datetime(
        2023, 11, 15, 0, 13, 20, tzinfo=dt.timezone(dt.timedelta(hours=2))
    )

    # UTCLeapSeconds subtracts 27 leap seconds for post-2017 instants
    leap_file = tmp_path / "leap.meta"
    _write_synthetic_mcos_datetime_hdf5(
        str(leap_file),
        real_ms=1700000027000.0,
        tz_in_defaults="UTCLeapSeconds",
    )
    with h5py.File(leap_file, "r") as f:
        dt_leap = decode_matlab_datetime(f, f["fpgaTimeReference"])
    assert dt_leap == dt.datetime(2023, 11, 14, 22, 13, 20, tzinfo=dt.timezone.utc)


def test_decode_empty_and_corrupt_mcos_datetimes(tmp_path):
    empty_mcos = tmp_path / "empty_mcos.meta"
    _write_synthetic_mcos_datetime_hdf5(str(empty_mcos), real_ms=0.0, dims=(1, 0))
    with h5py.File(empty_mcos, "r") as f:
        assert decode_matlab_datetime(f, f["fpgaTimeReference"]) is None

    corrupt = tmp_path / "corrupt.meta"
    with h5py.File(corrupt, "w") as f:
        ds = f.create_dataset(
            "fpgaTimeReference",
            data=np.array([[123, 2, 1, 1, 1, 1]], dtype=np.uint32),
        )
        ds.attrs["MATLAB_class"] = b"datetime"
        ds.attrs["MATLAB_object_decode"] = 3
        with pytest.raises(ValueError, match="MCOS"):
            decode_matlab_datetime(f, f["fpgaTimeReference"])


def test_matlab_datetime_pickle_and_timezone_parser():
    val = MatlabDatetime.from_epoch_milliseconds(
        1703080670029.5525, 6.476303218505564e-05, tz_str="UTC"
    )
    restored = pickle.loads(pickle.dumps(val))
    assert restored == val
    assert restored.tzinfo == dt.timezone.utc
    assert restored.add_fpga_ticks(807_174_241_522, 200_000_000) == dt.datetime(
        2023, 12, 20, 15, 5, 5, 900760, tzinfo=dt.timezone.utc
    )

    assert parse_matlab_timezone("") is None
    assert parse_matlab_timezone("-0530") == dt.timezone(
        -dt.timedelta(hours=5, minutes=30)
    )
    with pytest.raises(ValueError, match="Unsupported"):
        parse_matlab_timezone("Mars/Olympus_Mons")
