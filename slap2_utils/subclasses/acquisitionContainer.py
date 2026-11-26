import h5py
import numpy as np
from .slapROI import slapROI


class AcquisitionContainer():
    """
        A class used to load a SLAP2 binary metadatafile for data processing. This is also an attribute for the datafile object

        Attributes
        ----------
        AcquisitionPlan : dict
            A dictionary containing acquisition/parse plan metadata.
        DmdPatternSequence : list
            A list containing information related to the patterning of the sequences.
        ParsePlan : dict
            A dictionary that contains various instances related to how region of interest is parsed through.
        ROIs : list
            A list that contains information related to the region of interests.
        ScannerParameters : dict
            A dictionary that stores information related to the scanned parameter (not implemented yet, consider removing).
        constructor : str
            A string that describes how the plan is constructed.
        newFormat : bool
            Whether the metadata file uses the group-based AcquisitionPlan layout without a separate ParsePlan group.

        Descriptions for methods:
        --------------------------

        Methods
        ----------
        __init__() :
            Fill the fields mentioned above.

        Return
        -------
            Self with populated fields.
    """

    def __init__(self, metadatafile):
        self.AcquisitionPlan = {}
        self.DmdPatternSequence = None
        self.ParsePlan = {}
        self.ROIs = []
        self.ScannerParameters = ''
        self.constructor = ''
        self.newFormat = False

        acqParsePlan = {}
        with h5py.File(metadatafile, 'r') as hdf_file:
            ac_group = hdf_file['AcquisitionContainer']
            acq_plan_obj = ac_group['AcquisitionPlan']
            has_parse_plan_group = (
                'ParsePlan' in ac_group and isinstance(ac_group['ParsePlan'], h5py.Group)
            )

            if isinstance(acq_plan_obj, h5py.Group) and not has_parse_plan_group:
                self.newFormat = True
                self.DmdPatternSequence = ac_group['DmdPatternSequence'][:]

                self.AcquisitionPlan = {}
                self.AcquisitionPlan['constructor'] = ''.join(
                    chr(int(x[0])) for x in acq_plan_obj['constructor'][:]
                )
                self.AcquisitionPlan['fovSize'] = acq_plan_obj['fovSize'][:].squeeze()

                _refs = [ref[0] for ref in acq_plan_obj['superPixelIDs'][:]]
                self.AcquisitionPlan['superPixelIDs'] = [
                    hdf_file[_ref][:].flatten()
                    if len(hdf_file[_ref].shape) == 2
                    else np.zeros((0, 0), dtype=np.uint32)
                    for _ref in _refs
                ]

                _refs = [ref[0] for ref in acq_plan_obj['activeZs'][:]]
                self.AcquisitionPlan['activeZs'] = [
                    hdf_file[_ref][:].flatten()
                    if len(hdf_file[_ref].shape) == 2
                    else np.zeros((0, 0), dtype=np.uint32)
                    for _ref in _refs
                ]

                if 'pixelDilationX' in acq_plan_obj and 'pixelDilationY' in acq_plan_obj:
                    self.AcquisitionPlan['pixelDilationX'] = acq_plan_obj['pixelDilationX'][:]
                    _refs = [ref[0] for ref in acq_plan_obj['pixelDilationY'][:]]
                    self.AcquisitionPlan['pixelDilationY'] = [
                        hdf_file[_ref][:].flatten()
                        if len(hdf_file[_ref].shape) == 2
                        else np.zeros((0, 0), dtype=np.uint32)
                        for _ref in _refs
                    ]
                elif 'pixelDilationXYs' in acq_plan_obj:
                    self.AcquisitionPlan['pixelDilationXYs'] = acq_plan_obj['pixelDilationXYs'][:].T

                self.AcquisitionPlan['isSimpleRaster'] = acq_plan_obj['isSimpleRaster'][:].squeeze()
                self.AcquisitionPlan['rasterOffsetXY'] = acq_plan_obj['rasterOffsetXY'][:].squeeze()
                self.AcquisitionPlan['rasterSizeXY'] = acq_plan_obj['rasterSizeXY'][:].squeeze()
                self.AcquisitionPlan['zTrajectory'] = acq_plan_obj['zTrajectory'][:].squeeze()

                _refs = [ref[0] for ref in acq_plan_obj['rasterROIMasks'][:]]
                self.AcquisitionPlan['rasterROIMasks'] = [hdf_file[_ref][:].T for _ref in _refs]

                _refs = [ref[0] for ref in acq_plan_obj['blockROIMasks'][:]]
                self.AcquisitionPlan['blockROIMasks'] = [hdf_file[_ref][:].T for _ref in _refs]

                _refs = [ref[0] for ref in acq_plan_obj['pixelReplacementMaps'][:]]
                self.AcquisitionPlan['pixelReplacementMaps'] = [hdf_file[_ref][:] for _ref in _refs]

                for i in range(ac_group['ROIs']['rois'][:].shape[0]):
                    roi_ref = ac_group['ROIs']['rois'][i][0]
                    self.ROIs.append(slapROI(hdf_file, roi_ref))

                self.ParsePlan = self.AcquisitionPlan
            else:
                self.DmdPatternSequence = ac_group['DmdPatternSequence'][:]

                for i in range(ac_group['ROIs']['rois'][:].shape[0]):
                    roi_ref = ac_group['ROIs']['rois'][i][0]
                    self.ROIs.append(slapROI(hdf_file, roi_ref))

                for _key in ac_group['ParsePlan'].keys():
                    try:
                        self.AcquisitionPlan[_key] = ac_group['ParsePlan'][_key][:]
                    except Exception:
                        if _key == 'acqParsePlan':
                            _data = {}
                            for _subkey in ac_group['ParsePlan']['acqParsePlan'].keys():
                                _data[_subkey] = []
                                for _ref in list(ac_group['ParsePlan']['acqParsePlan'][_subkey][:]):
                                    _data[_subkey].append(hdf_file[_ref[0]][:])
                                acqParsePlan[_key] = _data

                _refs = [ref[0] for ref in ac_group['ParsePlan']['pixelReplacementMaps'][:]]
                self.AcquisitionPlan['pixelReplacementMaps'] = [hdf_file[_ref][:] for _ref in _refs]
                self.AcquisitionPlan['acqParsePlan'] = acqParsePlan['acqParsePlan']

                # Create a reference to AcquisitionPlan so ParsePlan points to the same object
                self.ParsePlan = self.AcquisitionPlan
