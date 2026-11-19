# Subclasses of the primary SLAP2 Datafile
import h5py
import numpy as np
from .slapROI import slapROI
from .acquisitionContainer import AcquisitionContainer
from ..utils.matlab_datetime import decode_matlab_datetime


class MetaData():
    """
        A class used to load a SLAP2 binary metadatafile for data processing. This is also an attribute for the datafile object

        Attributes
        ----------
        metadatafile : str
            The name of the metadata file.
        AcquisitionContainer : ``AcquisitionContainer``
            An instance of the AcquisitionContainer class that contain information related to the acquisition.
        acqDurationCycles : float
            The cycle duration for this acquisition path.
        acqDuration_s : float
            The total time (in seconds) for the whole acquisition.
        acquisitionPathIdx : int
            The number that represent the path that the acquisition takes place (either 1 or 2).
        acquisitionPathName : str
            The string that reiterates which path the acquisition takes place (e.g. 'Path1' or 'Path2').
        aomActive : int
            Binary number that represents whether AOM is active (0 = false, 1 = yes).
        aomVoltage : float
            The voltage in AOM (in float).
        aomPowerFractionTarget : float or None
            Target AOM power fraction when recorded in metadata.
        channelsSave : int or np.ndarray
            Channel(s) saved during the acquisition.
        dmdPixelsPerColumn : int
            The number of pixels along the column of the DMD.
        dmdPixelsPerRow : int
            The number of pixels along the row of the DMD.
        enableStack : int
            Flag representing stack configuration.
        fpgaTimeReference : datetime.datetime or None
            Decoded MATLAB ``datetime`` corresponding to FPGA tick 0. Naive
            ``datetime.datetime`` when the MATLAB value is unzoned, timezone-aware
            when ``TimeZone`` is set in MATLAB, or ``None`` when missing, empty,
            or ``NaT``.
        linePeriod_s : float
            The time it takes to conduct 1 line (1/linePeriod_s gives the line rate for the microscope).
        machineConfiguration : list of dict
            Parsed device configurations from the microscope setup.
        remoteFocusPosition_um : float
            Remote focus position in micrometers.
        samplesPerLine : int
            Number of samples per line.
    """

    def __init__(self, metadatafile):
        self.metadatafile = metadatafile
        self.AcquisitionContainer = None
        self.acqDurationCycles = ''
        self.acqDuration_s = ''
        self.acquisitionPathIdx = ''
        self.acquisitionPathName = ''
        self.aomActive = ''
        self.aomVoltage = ''
        self.aomPowerFractionTarget = None
        self.channelsSave = ''
        self.dmdPixelsPerColumn = ''
        self.dmdPixelsPerRow = ''
        self.enableStack = ''
        self.fpgaTimeReference = None
        self.linePeriod_s = ''
        self.machineConfiguration = []
        self.remoteFocusPosition_um = ''
        self.samplesPerLine = ''

        def group_to_dict(hdf5_group, rfs):
            output = {}
            for key in hdf5_group.keys():
                item = hdf5_group[key]
                if isinstance(item, h5py.Group):
                    output[key] = group_to_dict(item, rfs)
                else:
                    arr = item[:]
                    squeezed = arr.squeeze()
                    if (
                        isinstance(arr, np.ndarray)
                        and squeezed.ndim > 0
                        and squeezed.size > 0
                        and isinstance(squeezed.flat[0], h5py.Reference)
                    ):
                        output[key] = [rfs[ref][:].squeeze() for ref in squeezed.ravel()]
                    else:
                        output[key] = squeezed
            return output

        with h5py.File(metadatafile, 'r') as hdf_file:
            raw_acq_cycles = None

            for _key in hdf_file.keys():
                if _key in ('#refs#', '#subsystem#', 'AcquisitionContainer'):
                    continue

                if _key == 'acquisitionPathName':
                    ds = hdf_file['acquisitionPathName']
                    if ds.attrs.get('MATLAB_empty') == 1:
                        self.acquisitionPathName = ''
                    else:
                        self.acquisitionPathName = ''.join(
                            chr(int(x)) for x in ds[:].ravel()
                        )
                elif _key == 'machineConfiguration':
                    mc_obj = hdf_file[_key]
                    if isinstance(mc_obj, h5py.Group) and 'instanceName' in mc_obj:
                        num_devices = mc_obj['instanceName'].shape[1]
                        refs = hdf_file['#refs#']
                        for i in range(num_devices):
                            device_config_dict = {}
                            for prop in ('instanceName', 'instanceClass'):
                                prop_ds = refs[mc_obj[prop][0, i]]
                                if prop_ds.attrs.get('MATLAB_empty') == 1:
                                    device_config_dict[prop] = ''
                                else:
                                    device_config_dict[prop] = ''.join(
                                        chr(int(x)) for x in prop_ds[:].flatten()
                                    )

                            try:
                                cfg_target = refs[mc_obj['configuration'][0, i]]
                                if isinstance(cfg_target, h5py.Group):
                                    device_config_dict['configuration'] = group_to_dict(cfg_target, refs)
                                else:
                                    device_config_dict['configuration'] = None
                            except Exception:
                                device_config_dict['configuration'] = None
                            self.machineConfiguration.append(device_config_dict)
                elif _key == 'acqDurationCycles':
                    raw_acq_cycles = hdf_file[_key][:]
                elif (
                    _key == 'fpgaTimeReference'
                    or hdf_file[_key].attrs.get('MATLAB_class') in (b'datetime', 'datetime')
                ):
                    setattr(self, _key, decode_matlab_datetime(hdf_file, hdf_file[_key]))
                else:
                    obj = hdf_file[_key]
                    if isinstance(obj, h5py.Dataset):
                        arr = obj[:]
                        if arr.size == 1:
                            setattr(self, _key, arr.reshape(-1)[0])
                        else:
                            setattr(self, _key, arr.squeeze())

            if raw_acq_cycles is not None and raw_acq_cycles.size > 0:
                flat_cycles = raw_acq_cycles.ravel()
                try:
                    path_idx = int(self.acquisitionPathIdx)
                except (TypeError, ValueError):
                    path_idx = 1
                if 1 <= path_idx <= flat_cycles.size:
                    self.acqDurationCycles = flat_cycles[path_idx - 1]
                else:
                    self.acqDurationCycles = flat_cycles[0]

            self.AcquisitionContainer = AcquisitionContainer(self.metadatafile)
