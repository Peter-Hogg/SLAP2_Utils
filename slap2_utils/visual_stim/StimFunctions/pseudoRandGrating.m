function [time, sType, stimAngle, speed] = pseudoRandGrating(win, r, daq)
    speed=2;
    % original:
    % angles = [0, 45, 90, 135, 180, 225, 270, 315];
    % stimAngle = angles(randperm(length(angles)))
    stimAngle = r;
    time = clock;
    for stim = 1:length(stimAngle)
        GenGrating(win, stimAngle(stim), 2, .0034, 1920, 1280, daq);
        % rand pause?
        x = randi([6,12]);
        pause(x)
    end

    sType = 'pseudoRandGrating';
        

end