function pseudoRandGrating(win, daq)
    angles = [0, 45, 90, 135, 180, 225, 270, 315];
    stimAngle = angles(randperm(length(angles)))
    for stim = 1:length(stimAngle)
        GenGrating(win, stimAngle(stim), 2, .0034, 1200, 1200, daq);
        x = randi([6,12])
        pause(x)
    end
        

end