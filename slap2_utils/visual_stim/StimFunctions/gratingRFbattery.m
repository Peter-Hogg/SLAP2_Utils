function gratingRFbattery(win, winRect, daq)
    pause(10)

    angles = [0, 45, 90, 135,  180, 225,  270, 360];
    
    % random shuffles
    stimAngle = angles(randperm(length(angles)));

    randomSquare = [];
    for stim = 1:length(angles)
        GenGrating(win, stimAngle(stim), .5, .00152,  1920, 1280,  daq);
        pause(2)
        [r] = AllenSTACheckerFast(win, winRect, 3, 200,  daq);
        randomSquare = [randomSquare, r];
        pause(2)
    end
    currentTime =  datetime('now', 'Format', 'yyyy-MM-dd-HH-mm-ss')
    gratingName = ['C:\Users\haasl\Documents\SLAP2_Utils\slap2_utils\visual_stim\StimFunctions\stimLogs\Grating_', char(currentTime),'.csv']
    allenSTAName = ['C:\Users\haasl\Documents\SLAP2_Utils\slap2_utils\visual_stim\StimFunctions\stimLogs\AllenSTAChecker_', char(currentTime),'.csv']

    writecell(randomSquare, allenSTAName)
    writematrix(stimAngle, gratingName)
    sca;
end