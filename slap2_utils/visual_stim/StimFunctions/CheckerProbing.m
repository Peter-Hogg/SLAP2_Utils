function [time, sType, stimSizes, stimProb] = CheckerProbing(win, winRect, daq)
    % original:
    sizes = [50, 100, 150];
    
    probability = [0.01 0.02, 0.05];

    % random shuffles
    stimSizes = sizes(randperm(length(sizes)));
    stimProb = probability(randperm(length(probability)));
    for s = 1:length(stimSizes) 
       for p = 1:length(stimProb)

           AllenSTAChecker(win, winRect, stimProb(p), stimSizes(s), daq)
           pause(1.5)
                
       end
    end
    

    sType = 'grating';
        

end