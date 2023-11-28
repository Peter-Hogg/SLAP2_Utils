function [startTime, sType] = SquareGrating(win, angle, cyclespersecond, freq, gratingsize, internalRotation, daq)
% Display an animated grating, using the new Screen('DrawTexture') command.
% This demo demonstrates fast drawing of such a grating via use of procedural
% texture mapping. It only works on hardware with support for the GLSL
% shading language, vertex- and fragmentshaders. The demo ends if you press
% any key on the keyboard.
%


[gratingid, gratingrect] = CreateProceduralSquareWaveGrating(win, 100, 400, [0,0,1,0])

startTime = datetime;
endTime = (datetime - startTime);
write(daq, 3);
pause(.001);
write(daq, 0);
while endTime < duration([0,0,5]);

    % Update some grating animation parameters:
    
    % Increment phase by 1 degree:
    phase = phase + phaseincrement;
    
    % Draw the grating, centered on the screen, with given rotation 'angle',
    % sine grating 'phase' shift and amplitude, rotating via set
    % 'rotateMode'. Note that we pad the last argument with a 4th
    % component, which is 0. This is required, as this argument must be a
    % vector with a number of components that is an integral multiple of 4,
    % i.e. in our case it must have 4 components:
    Screen('DrawTexture', win, gratingtex, [], [], angle, [], [], [], [], rotateMode, [phase, freq, amplitude, 0]);

    % Show it at next retrace:
    vbl = Screen('Flip', win, vbl + 0.5 * ifi);
    endTime = (datetime - startTime);
    end

write(daq, 3);
pause(.001);
write(daq, 0);       
% Leave Stim Screen Blank
Screen('Fillrect', win, [0, 0, 255]);
Screen('Flip', win);

sType = 'GenGrating';





end