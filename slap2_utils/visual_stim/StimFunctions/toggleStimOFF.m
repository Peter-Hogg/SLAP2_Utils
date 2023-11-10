function  toggleStimOFF(win, daq)

    screenid = max(Screen('Screens'));
    black = BlackIndex(screenid);
    Screen('Fillrect', win, black);
    
    
    Screen('Flip', win) ;

end

