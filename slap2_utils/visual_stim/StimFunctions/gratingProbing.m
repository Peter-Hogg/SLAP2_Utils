function gratingProbing(win, daq)
    % original:
    % 0.0052: 10 cycles across screen, 0.004167: 8 cycles 0.003125: 6 cycles, 0.002083: 4 cycles, 0.001042: 2 cycles
    sizes = [0.0052, 0.004167, 0.003125, 0.002083, 0.001042];
    angles = [180];
    durations = [1.5, 1, 0.5];
    speeds = [10, 8, 6, 4, 2]

    % random shuffles
    stimSizes = sizes(randperm(length(sizes)))
    stimAngle = angles(randperm(length(angles)))
    stimSpeed = speeds(randperm(length(speeds)))
    stimDuration = durations(randperm(length(durations)))
    randompauses = 8 + (12-8) * rand(length(sizes), length(angles), length(speeds), length(durations));
    stimPause = randompauses(:);
    
    [a, b, c, d] = ndgrid(stimAngle, stimSpeed, stimSizes, stimDuration);
    combinations = [a(:), b(:), c(:), d(:)];
    numRows = length(combinations);          
    randomizedIndices = randperm(numRows);    
    stimRand = combinations(randomizedIndices, :); 

    stimCombos = {'stim', 'angle', 'speed', 'size', 'duration', 'pause'};
    pauseindex = 1;
    for stim = 1:length(stimRand)
              %GenGrating(win, angle, cyclespersecond, freq, gratingsize, internalRotation, daq)
              GenGrating(win, stimRand(stim,1), stimRand(stim,2), stimRand(stim,3),  1920, 1280,  daq, stimRand(stim,4));
              pause(stimPause(pauseindex))
              pauseindex = pauseindex + 1

    end

    sType = 'grating';

    pauseindex = 1;

    for stim = 1:length(stimRand)
        newRow = {sType, stimRand(stim,1), stimRand(stim,2), stimRand(stim,3), stimRand(stim,4), stimPause(pauseindex) + 0.001};
        stimCombos = [stimCombos; newRow];
        pauseindex = pauseindex + 1;
    end

    currentTime = datetime('now', 'Format', 'yyyyMMdd_HHmmss');
    stimComboFilename =  sprintf('stimLogs/gratingCombos_%s.csv', currentTime)
    writecell(stimCombos, stimComboFilename)
end
