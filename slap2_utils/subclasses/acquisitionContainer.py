import h5py
from .slapROI import slapROI

class  AcquisitionContainer():
    def __init__(self, metadatafile):
        self.AcquisitionPlan = None
        self.DmdPatternSequence = None
        self.ParsePlan = {}
        self.ROIs = []
        self.ScannerParameters = ''
        self.constructor = ''


        acqParsePlan = {}
        with h5py.File(metadatafile, 'r') as hdf_file:
            # Read the contents of the HDF5 file into the metaData dictionary

            self.AcquisitionPlan = hdf_file['AcquisitionContainer']['AcquisitionPlan'][:]
            self.DmdPatternSequence = hdf_file['AcquisitionContainer']['DmdPatternSequence'][:]

            for i in range(hdf_file['AcquisitionContainer']['ROIs']['rois'][:].shape[0]):
                roi_ref = hdf_file['AcquisitionContainer']['ROIs']['rois'][i][0]
                self.ROIs.append(slapROI(hdf_file, roi_ref))
                
                
            for _key in hdf_file['AcquisitionContainer']['ParsePlan'].keys():
                try:
                    self.ParsePlan[_key] = hdf_file['AcquisitionContainer']['ParsePlan'][_key][:]
                except:
                    if _key == 'acqParsePlan':
                        _data = {}
                        for _subkey in hdf_file['AcquisitionContainer']['ParsePlan']['acqParsePlan'].keys():
                            _data[_subkey] = []
                            for _ref in (list(hdf_file['AcquisitionContainer']['ParsePlan']['acqParsePlan'][_subkey][:])):
                                _data[_subkey].append(hdf_file[_ref[0]][:])
                            acqParsePlan[_key] = _data

            
            _ref = hdf_file['AcquisitionContainer']['ParsePlan']['pixelReplacementMaps'][:][0][0]
            print(len(hdf_file['AcquisitionContainer']['ParsePlan']['pixelReplacementMaps'][:]))
            _refs = []
            for index in range(len(hdf_file['AcquisitionContainer']['ParsePlan']['pixelReplacementMaps'][:])):
                _refs.append(hdf_file['AcquisitionContainer']['ParsePlan']['pixelReplacementMaps'][:][index][0])
            self.ParsePlan['pixelReplacementMaps'] = [hdf_file[_ref][:] for _ref in _refs]
            self.ParsePlan['acqParsePlan'] = acqParsePlan['acqParsePlan']
