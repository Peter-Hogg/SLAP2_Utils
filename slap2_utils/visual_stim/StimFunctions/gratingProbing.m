function [time, sType, stimAngle, speed] = gratingProbing(win, daq)
    speed=2;
    % original:
    sizes = [.0034, .03];
    angles = [0,  90,  180,  270];
    speeds = [0.5 1, 5];

    % random shuffles
    stimSizes = sizes(randperm(length(sizes)))
    stimAngle = angles(randperm(length(angles)))
    stimSpeed = speeds(randperm(length(speeds)))
    
    for stim = 1:length(angles)
        for size = 1:length(stimSizes) 
            for speed = 1:length(stimSpeed)
                GenGrating(win, stimAngle(stim), stimSpeed(speed), stimSizes(size), 1920, 1280, daq);
                pause(1.5)
                
            end
        end
    end

    sType = 'grating';
        

end