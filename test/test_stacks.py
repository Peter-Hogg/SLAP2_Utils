import numpy as np
import tifffile
import json
import pytest
import zarr
import dask.array as da
from unittest import mock
import slap2_utils.functions.imagestacks as imagestacks

@pytest.fixture
def fake_tif_stack_zarr(tmp_path):
    numZs = 49
    framesPerZ = 130
    height, width = 100, 100
    total_frames = numZs * framesPerZ
    shape = (total_frames, height, width)

    # Simulated TIFF image data
    array = np.random.randint(0, 255, size=shape, dtype=np.uint8)

    # Save to Zarr memory store
    store = zarr.MemoryStore()
    zarr.save_array(store, array, chunks=(framesPerZ, height, width))
    
    # Simulated SLAP2 metadata
    meta = {
        "SLAP2TifFileVersion": 1,
        "numChannels": 1,
        "numFramesPerSlice": framesPerZ,
        "numZs": numZs,
        "zsAbsolute": list(range(201, 201 + numZs)),
        "shape": list(shape),
    }

    # Save dummy TIFF path
    tif_path = tmp_path / "mock_stack.tif"
    tif_path.write_bytes(b"fake")

    return tif_path, json.dumps(meta), store

def test_averageStack_cpu_zarr(monkeypatch, fake_tif_stack_zarr):
    tif_path, meta_json, zarr_store = fake_tif_stack_zarr

    # Patch tifffile APIs
    monkeypatch.setattr(tifffile, "tiffcomment", lambda path: meta_json)
    monkeypatch.setattr(tifffile, "imread", lambda path, aszarr=None: zarr_store)

    # Run CPU stack averaging
    imagestacks.averageStack(str(tif_path))

    avg_path = tif_path.parent / f"averageCPU_{tif_path.name}"
    assert avg_path.exists()
