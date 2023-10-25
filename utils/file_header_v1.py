def load_file_header_v1(obj, rawUint32):
    # Format: data format:
    #             uint32_t magic_start         = MAGIC_NUMBER;
    #            uint32_t file_version        = 1;
    #             uint32_t firstCycleOffset    = 0;
    #            uint32_t lineHeaderSizeBytes = 0;
    #             uint32_t laserPathIdx        = 0;
    #             uint32_t bytesPerCycle       = 0;
    #            uint32_t linesPerCycle       = 0;
    #             uint32_t superPixelsPerCycle = 0;
    #             uint32_t dmdPixelsPerRow     = 0;
    #            uint32_t dmdPixelsPerColumn  = 0;
    #             uint32_t numChannels         = 0;
    #             uint32_t numSlices           = 0;
   #          uint32_t magic_end           = MAGIC_NUMBER;

    file_magic_number = rawUint32[0]
    assert file_magic_number == MAGIC_NUMBER, 'Data format error.'

    file_format_version = rawUint32[1]
    assert file_format_version == 1, 'Unknown format version'

    file_first_cycle_offset = rawUint32[2]

    file_header = rawUint32[:file_first_cycle_offset // 4]
    file_header = list(map(float, file_header))

    header = {
        'magic_start': file_header[0],
        'file_version': file_header[1],
        'firstCycleOffsetBytes': file_header[2],
        'lineHeaderSizeBytes': file_header[3],
        'laserPathIdx': file_header[4],
        'bytesPerCycle': file_header[5],
        'linesPerCycle': file_header[6],
        'superPixelsPerCycle': file_header[7],
        'dmdPixelsPerRow': file_header[8],
        'dmdPixelsPerColumn': file_header[9],
        'numChannels': file_header[10],
        'numSlices': file_header[11],
        'magic_end': file_header[12],
        'channelsInterleave': 1,  # Version 1 data is always interleaved
        'fpgaSystemClock_Hz': 200e6
    }

    assert header['magic_end'] == MAGIC_NUMBER, 'Data format error.'

    header_ = translate_num_channels(header)
    obj.header = header_

    file_size_bytes = len(obj.raw_data['Data']) * 4
    obj.numCycles = int((file_size_bytes - header['firstCycleOffsetBytes']) / header['bytesPerCycle'])
    obj.totalNumLines = obj.numCycles * header['linesPerCycle']
    obj.numChannels = float(header['numChannels'])


def translate_num_channels(header):
    header['channels'] = list(range(1, int(header['numChannels']) + 1))
    header['channelMask'] = sum(2 ** (channel - 1) for channel in header['channels'])
    return header
