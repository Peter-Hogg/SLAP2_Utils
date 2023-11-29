function [time, sType, stimSizes, stimProb] = CheckerProbing(win, daq)
    % original:
    sizes = [50, 100, 150];
    
    probability = [0.1 0.2, 0.5];

    % random shuffles
    stimSizes = sizes(randperm(length(sizes)));
    stimProb = probability(randperm(length(probability)));
    
    for size = 1:length(stimSizes) 
       for p = 1:length(stimProb)

           AllenSTAChecker(win, winRect, p, size, r, daq)
           pause(1.5)
                
       end
    end
    

    sType = 'grating';
        

end