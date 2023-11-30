import h5py
import numpy as np
from scipy import signal


def returnStimTime(stimFile, distance=250, hz=5000):
    # stimlog is a hf file containing TTL traces from the SLAP2 datarecorder
    # TTL trace is sampled at 5000 hz
    # Returns stop and start of visual stim in seconds
    stimLog = h5py.File(stimFile, 'r')
    TTL_Trace = stimLog['TTL'][:]
    peaks, _ = signal.find_peaks(np.diff(TTL_Trace), height=2.5, distance=distance)
    start = [peaks[i]*(1/hz) for i in range(0, len(peaks), 2)]
    stop = [peaks[i]*(1/hz) for i in range(1, len(peaks), 2)]
    return start, stop
