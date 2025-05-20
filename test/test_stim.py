import numpy as np
import h5py
import tempfile
import os
from slap2_utils.functions.stim import returnStimTime

def test_return_stim_time():
    # Simulate a TTL trace with rising edges at sample indices 100 and 600 (2.5V rise)
    ttl_trace = np.zeros(1000)
    ttl_trace[100:200] = 5
    ttl_trace[600:700] = 5

    # Write mock HDF5 to a temp file
    with tempfile.NamedTemporaryFile(suffix='.h5', delete=False) as tmp:
        with h5py.File(tmp.name, 'w') as f:
            f.create_dataset('TTL', data=ttl_trace)
        temp_path = tmp.name

    # Run the function
    start, stop = returnStimTime(temp_path, distance=250, hz=5000)

    # Cleanup temp file
    os.remove(temp_path)

    # Assert start/stop time pairs
    assert len(start) == 1
    assert len(stop) == 1
    np.testing.assert_allclose(start[0], 100 / 5000, rtol=1e-2)
    np.testing.assert_allclose(stop[0], 600 / 5000, rtol=1e-2)