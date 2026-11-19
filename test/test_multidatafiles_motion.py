import numpy as np
import pytest

from slap2_utils.multidatafiles import MultiDataFiles


class FakeDataFile:
    def __init__(self, name, num_cycles, first_timestamp, file_number):
        self.datFileName = name
        self.numCycles = num_cycles
        self.firstLineTimestamp = np.uint64(first_timestamp)
        self.file_number = file_number

    def getLineHeader(self, line_indices, cycle_indices):
        line_indices = np.asarray(line_indices).ravel()
        cycle_indices = np.asarray(cycle_indices).ravel()
        headers = [
            {
                "lineNumber": np.uint32(line - 1),
                "acqNumber": np.uint32(cycle),
                "xOffset_pix": self.file_number * 100 + int(line),
                "yOffset_pix": self.file_number * -100 - int(cycle),
                "zOffset_um": np.float32(self.file_number + cycle / 10),
            }
            for line, cycle in zip(line_indices, cycle_indices)
        ]
        return headers[0] if len(headers) == 1 else headers


def make_multifile():
    multifile = MultiDataFiles.__new__(MultiDataFiles)
    multifile.header = {"linesPerCycle": 3, "bytesPerCycle": 100}
    multifile.lineHeaderIdxs = np.array([11, 31, 51])
    multifile.lineDataStartIdxs = [31, 51, 71]
    multifile.lineDataNumElements = [10, 10, 10]
    multifile.hDataFiles = [
        FakeDataFile("later.dat", 1, 200, 2),
        FakeDataFile("earlier.dat", 2, 100, 1),
    ]
    multifile.numCycles = 3
    multifile.totalNumLines = 9
    return multifile


def test_multidatafiles_sorts_by_first_line_timestamp():
    multifile = make_multifile()

    multifile._sort_files_in_place()

    assert [datafile.datFileName for datafile in multifile.hDataFiles] == [
        "earlier.dat", "later.dat"
    ]


def test_multidatafiles_get_line_header_routes_and_preserves_order():
    multifile = make_multifile()
    multifile._sort_files_in_place()

    headers = multifile.getLineHeader([2, 1, 3], [3, 1, 2])

    assert [header["xOffset_pix"] for header in headers] == [202, 101, 103]
    assert [header["acqNumber"] for header in headers] == [1, 1, 2]


def test_multidatafiles_get_line_header_scalar():
    multifile = make_multifile()
    multifile._sort_files_in_place()

    header = multifile.getLineHeader(2, 3)

    assert isinstance(header, dict)
    assert header["xOffset_pix"] == 202


def test_multidatafiles_get_line_header_global_line_indices():
    multifile = make_multifile()
    multifile._sort_files_in_place()

    headers = multifile.getLineHeader([8, 1, 6])

    assert [header["xOffset_pix"] for header in headers] == [202, 101, 103]
    assert [header["acqNumber"] for header in headers] == [1, 1, 2]


@pytest.mark.parametrize(
    "line_indices,cycle_indices",
    [
        ([1.5], [1]),
        ([1], [1.5]),
        ([np.nan], [1]),
        ([1], [np.inf]),
        (["one"], [1]),
    ],
)
def test_multidatafiles_get_line_header_rejects_noninteger_indices(
        line_indices, cycle_indices):
    multifile = make_multifile()

    with pytest.raises(ValueError, match="finite integers"):
        multifile.getLineHeader(line_indices, cycle_indices)


def test_multidatafiles_get_line_header_accepts_integer_valued_floats():
    multifile = make_multifile()
    multifile._sort_files_in_place()

    header = multifile.getLineHeader(2.0, 3.0)

    assert header["xOffset_pix"] == 202


def test_multidatafiles_discovers_real_cycle_files_including_relative_path(
    tmp_path, monkeypatch
):
    import os
    import shutil

    test_dir = os.path.dirname(__file__)
    shutil.copyfile(
        os.path.join(test_dir, "testFile.meta"), tmp_path / "rec.meta"
    )
    shutil.copyfile(
        os.path.join(test_dir, "testFile.dat"), tmp_path / "rec-CYCLE1.dat"
    )
    shutil.copyfile(
        os.path.join(test_dir, "testFile.dat"), tmp_path / "rec-CYCLE2.dat"
    )

    monkeypatch.chdir(tmp_path)
    multifile = MultiDataFiles("rec-CYCLE1.dat")

    assert len(multifile.hDataFiles) == 2
    assert multifile.numCycles == 688
    h1 = multifile.getLineHeader(1, 1)
    h_second_file = multifile.getLineHeader(1, 345)
    assert h1["timestamp_date"] is not None
    assert h1["timestamp_date"] == h_second_file["timestamp_date"]
