import datetime as dt
import os

import numpy as np
import pytest

import slap2_utils.datafile as datafile_module
from slap2_utils.datafile import DataFile
from slap2_utils.utils.line_header import LINE_HEADER_MAGIC


@pytest.fixture
def datafile():
    test_dir = os.path.dirname(__file__)
    return DataFile(os.path.join(test_dir, "testFile.dat"))


def test_get_line_header_reads_real_fixture(datafile):
    header = datafile.getLineHeader(1, 1)

    assert datafile.metaData.fpgaTimeReference == dt.datetime(
        2023, 12, 20, 13, 57, 50, 29553
    )
    assert header["lineSizeBytes"] == np.uint32(40)
    assert header["magicNumber"] == np.uint32(LINE_HEADER_MAGIC)
    assert header["lineNumber"] == np.uint32(0)
    assert header["acqNumber"] == np.uint32(1)
    assert header["xOffset_pix"] == 0
    assert header["yOffset_pix"] == 0
    assert header["timestamp"] == np.uint64(807_174_241_522)
    assert header["zOffset_um"] == np.float32(0)
    assert header["timestamp_s"] == pytest.approx(0.0)
    assert header["timestamp_date"] == dt.datetime(
        2023, 12, 20, 15, 5, 5, 900760
    )
    assert header["timestamp_date"].tzinfo is None


def test_get_line_header_matlab_parity_across_lines_and_example_scan(datafile):
    headers = datafile.getLineHeader([1, 2, 100], [1, 1, 10])
    assert headers[0]["timestamp_date"] == dt.datetime(
        2023, 12, 20, 15, 5, 5, 900760
    )
    assert headers[1]["timestamp_date"] == dt.datetime(
        2023, 12, 20, 15, 5, 5, 900856
    )

    # Elapsed absolute time between lines matches relative timestamp_s to microsecond precision
    elapsed_abs = (
        headers[2]["timestamp_date"] - headers[0]["timestamp_date"]
    ).total_seconds()
    elapsed_rel = headers[2]["timestamp_s"] - headers[0]["timestamp_s"]
    assert elapsed_abs == pytest.approx(elapsed_rel, abs=1e-6)

    # Parity check on second real SLAP2 fixture (3DExampleScan.dat + 3DExampleScan.meta)
    repo_root = os.path.dirname(os.path.dirname(__file__))
    example_dat = os.path.join(
        repo_root, "slap2_utils", "examples", "3DExampleScan.dat"
    )
    if os.path.isfile(example_dat):
        example_df = DataFile(example_dat)
        assert example_df.metaData.fpgaTimeReference == dt.datetime(
            2023, 12, 20, 13, 57, 50, 34155
        )
        ex_header = example_df.getLineHeader(1, 1)
        assert ex_header["timestamp_s"] == pytest.approx(0.0)
        assert ex_header["timestamp_date"] == dt.datetime(
            2023, 12, 20, 15, 8, 38, 930005
        )


def test_get_line_header_handles_missing_fpga_time_reference(datafile, monkeypatch):
    monkeypatch.setattr(datafile.metaData, "fpgaTimeReference", None)
    header = datafile.getLineHeader(2, 1)

    assert header["timestamp_date"] is None
    assert header["timestamp_s"] == pytest.approx(9.6295e-05)


def test_get_line_header_batches_and_broadcasts_cycle(datafile):
    headers = datafile.getLineHeader([1, 2], 1)

    assert isinstance(headers, list)
    assert [header["lineNumber"] for header in headers] == [0, 1]
    assert [header["timestamp"] for header in headers] == sorted(
        header["timestamp"] for header in headers
    )
    assert [header["timestamp_date"] for header in headers] == sorted(
        header["timestamp_date"] for header in headers
    )


def test_get_line_header_preserves_request_order(datafile):
    headers = datafile.getLineHeader([2, 1], [2, 1])

    assert headers[0]["lineNumber"] == np.uint32(1)
    assert headers[0]["acqNumber"] == np.uint32(1)
    assert headers[1]["lineNumber"] == np.uint32(0)
    assert headers[1]["acqNumber"] == np.uint32(1)


def test_get_line_header_empty_request(datafile):
    assert datafile.getLineHeader([], []) == []


@pytest.mark.parametrize(
    "line_indices,cycle_indices,message",
    [
        ([0], [1], "positive integers"),
        ([1], [0], "positive integers"),
        ([303], [1], "linesPerCycle"),
        ([1], [345], "numCycles"),
        ([1, 2], [1, 2, 3], "match"),
        ([1.5], [1], "integers"),
    ],
)
def test_get_line_header_rejects_invalid_indices(
        datafile, line_indices, cycle_indices, message):
    with pytest.raises(ValueError, match=message):
        datafile.getLineHeader(line_indices, cycle_indices)


def test_datafile_records_first_line_timestamp(datafile):
    assert datafile.firstLineTimestamp == np.uint64(807_174_241_522)


def test_datafile_with_no_complete_cycles_skips_first_line_header(monkeypatch):
    datafile = DataFile.__new__(DataFile)
    datafile.MAGIC_NUMBER = np.uint32(LINE_HEADER_MAGIC)
    datafile.rawData = np.zeros(6, dtype=np.int16)
    datafile.rawData.view(np.uint32)[0] = LINE_HEADER_MAGIC
    datafile.rawData.view(np.uint32)[1] = 2
    datafile.rawData.view(np.uint32)[2] = 40
    datafile.firstLineTimestamp = None

    header = {
        "firstCycleOffsetBytes": 8,
        "lineHeaderSizeBytes": 40,
        "bytesPerCycle": 40,
        "linesPerCycle": 1,
    }
    monkeypatch.setattr(
        datafile_module,
        "load_file_header_v2",
        lambda _datafile, _raw_data: (header, 0),
    )

    datafile.load_file_header()

    assert datafile.numCycles == 0
    assert datafile.firstLineTimestamp is None
