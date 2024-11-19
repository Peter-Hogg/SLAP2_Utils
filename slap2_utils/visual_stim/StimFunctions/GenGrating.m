function [startTime, sType] = GenGrating(win, angle, cyclespersecond, freq, gratingsize, internalRotation, daq, presentation_time)
% Display an animated grating, using the new Screen('DrawTexture') command.
% This demo demonstrates fast drawing of such a grating via use of procedural
% texture mapping. It only works on hardware with support for the GLSL
% shading language, vertex- and fragmentshaders. The demo ends if you press
% any key on the keyboard.
%
% Optional Parameters:
% 'angle' = Rotation angle of grating in degrees.
% 'internalRotation' = Shall the rectangular image patch be rotated
% (default), or the grating within the rectangular patch?
% gratingsize = Size of 2D grating patch in pixels.
% freq = Frequency of sine grating in cycles per pixel.
% cyclespersecond = Drift speed in cycles per second.


% Make sure this is running on OpenGL Psychtoolbox:
AssertOpenGL;
screenid = max(Screen('Screens'));
white = WhiteIndex(screenid);
black = BlackIndex(screenid);
% Initial stimulus parameters for the grating patch:

if nargin < 5 || isempty(internalRotation)
    internalRotation = 0;
end

if internalRotation
    rotateMode = kPsychUseTextureMatrixForRotation;
else
    rotateMode = [];
end

if nargin < 4 || isempty(gratingsize)
    gratingsize = 1200;
end

% res is the total size of the patch in x- and y- direction, i.e., the
% width and height of the mathematical support:
res = [gratingsize gratingsize];

if nargin < 3 || isempty(freq)
    % Frequency of the grating in cycles per pixel: Here 0.01 cycles per pixel:
    freq = 1/360;
end

if nargin < 2 || isempty(cyclespersecond)
    cyclespersecond = 1;
end

if nargin < 1 || isempty(angle)
    % Tilt angle of the grating:
    angle = 0;
end

% Amplitude of the grating in units of absolute display intensity range: A
% setting of 0.5 means that the grating will extend over a range from -0.5
% up to 0.5, i.e., it will cover a total range of 1.0 == 100% of the total
% displayable range. As we select a background color and offset for the
% grating of 0.5 (== 50% nominal intensity == a nice neutral gray), this
% will extend the sinewaves values from 0 = total black in the minima of
% the sine wave up to 1 = maximum white in the maxima. Amplitudes of more
% than 0.5 don't make sense, as parts of the grating would lie outside the
% displayable range for your computers displays:
amplitude = 0.5;


% Make sure the GLSL shading language is supported:
AssertGLSL;

% Retrieve video redraw interval for later control of our animation timing:
ifi = Screen('GetFlipInterval', win );

% Phase is the phase shift in degrees (0-360 etc.)applied to the sine grating:
phase = 0;

% Compute increment of phase shift per redraw:
phaseincrement = (cyclespersecond * 360) * ifi;

% Build a procedural sine grating texture for a grating with a support of
% res(1) x res(2) pixels and a RGB color offset of 0.5 -- a 50% gray.
gratingtex = CreateProceduralSineGrating(win, res(1), res(2), [0.0 0.0 1 0]);

% Wait for release of all keys on keyboard, then sync us to retrace:
vbl = Screen('Flip', win);


startTime = datetime;
endTime = (datetime - startTime);
write(daq, 3);
pause(.001);
write(daq, 0);
while endTime < duration([0,0,presentation_time]);

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
Screen('Fillrect', win, [0, 0, 128]);
Screen('Flip', win);

sType = 'GenGrating';





end


