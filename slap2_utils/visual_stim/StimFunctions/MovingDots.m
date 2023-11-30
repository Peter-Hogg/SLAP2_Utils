function [startTime, sType] = MovingDots(win, angle, speed, freq, size, internalRotation, daq)
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
dots.nDots = freq;                % number of dots
dots.color = [255,255,255];      % color of the dots
dots.size = size;                   % size of dots (pixels)
dots.center = [0,0];           % center of the field of dots (x,y)
dots.apertureSize = [12,12];     % size of rectangular aperture [w,h] in degrees.

dots.x = (rand(1,dots.nDots)-.5)*dots.apertureSize(1) + dots.center(1);
dots.y = (rand(1,dots.nDots)-.5)*dots.apertureSize(2) + dots.center(2);

display.dist = 4840;  %cm
display.width = 1080; %cm



tmp = Screen('Resolution',0);
display.resolution = [tmp.width,tmp.height];


pixpos.x = angle2pix(display,dots.x);
pixpos.y = angle2pix(display,dots.y);
%
% This generates pixel positions, but they're centered at [0,0].  The last
% step for this conversion is to add in the offset for the center of the
% screen:
%

pixpos.x = pixpos.x + display.resolution(1)/2;
pixpos.y = pixpos.y + display.resolution(2)/2;


display.skipChecks=1;
    


dots.speed = speed;       %degrees/second
dots.duration = 5;    %seconds
dots.direction = angle;  %degrees (clockwise from straight up)


l = dots.center(1)-dots.apertureSize(1)/2;
r = dots.center(1)+dots.apertureSize(1)/2;
b = dots.center(2)-dots.apertureSize(2)/2;
t = dots.center(2)+dots.apertureSize(2)/2;


dots.x = (rand(1,dots.nDots)-.5)*dots.apertureSize(1) + dots.center(1);
dots.y = (rand(1,dots.nDots)-.5)*dots.apertureSize(2) + dots.center(2);

try
    display = OpenWindow(display);
    dx = dots.speed*sin(dots.direction*pi/180)/display.frameRate;
    dy = -dots.speed*cos(dots.direction*pi/180)/display.frameRate;
    nFrames = ceil(dots.duration * display.frameRate);

    for i=1:nFrames
        %convert from degrees to screen pixels
        pixpos.x = angle2pix(display,dots.x)+ display.resolution(1)/2;
        pixpos.y = angle2pix(display,dots.y)+ display.resolution(2)/2;

        Screen('DrawDots',display.windowPtr,[pixpos.x;pixpos.y], dots.size, dots.color,[0,0],1);
        %update the dot position
        dots.x = dots.x + dx;
        dots.y = dots.y + dy;

        %move the dots that are outside the aperture back one aperture
        %width.
        dots.x(dots.x<l) = dots.x(dots.x<l) + dots.apertureSize(1);
        dots.x(dots.x>r) = dots.x(dots.x>r) - dots.apertureSize(1);
        dots.y(dots.y<b) = dots.y(dots.y<b) + dots.apertureSize(2);
        dots.y(dots.y>t) = dots.y(dots.y>t) - dots.apertureSize(2);

        Screen('Flip',display.windowPtr);
    end
catch ME
    Screen('CloseAll');
    rethrow(ME)
end
Screen('CloseAll');
end


