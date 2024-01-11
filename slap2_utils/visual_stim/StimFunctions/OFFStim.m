function [time, sType, stimData] = OFFStim(win, daq)
% Full Field Off Simulus - 50 ms 
screenid = max(Screen('Screens'));

white = WhiteIndex(screenid);
black = BlackIndex(screenid);
colorFill = [0,0,255];
Screen('Fillrect', win, black);
time = clock;
write(daq, 3);
pause(.001);
write(daq, 0);
Screen('Flip', win) ;

pause(.050);
Screen('Fillrect', win, colorFill);
Screen('Flip', win);
write(daq, 3);
pause(.001);
write(daq, 0);
sType = 'OFF';
stimData = 0;
end

