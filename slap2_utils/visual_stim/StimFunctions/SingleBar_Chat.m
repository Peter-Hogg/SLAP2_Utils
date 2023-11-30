screens = Screen('Screens');
screenNumber = max(screens);
white = WhiteIndex(screenNumber);
black = BlackIndex(screenNumber);
[window, windowRect] = PsychImaging('OpenWindow', screenNumber, black);
[xCenter, yCenter] = RectCenter(windowRect);

% Set parameters for the moving bar
barWidth = 100;
barHeight = 20;
barColor = [255 0 0];  % Red color
barSpeed = 4;  % Speed of the moving bar in pixels per frame
angleDegrees = 45;  % Angle of movement (in degrees)

% Calculate movement increments (x and y) based on the angle
angleRadians = deg2rad(angleDegrees);
deltaX = cos(angleRadians) * barSpeed;
deltaY = sin(angleRadians) * barSpeed;

% Initial position of the bar
barStartX = xCenter - barWidth / 2;
barStartY = yCenter - barHeight / 2;
barRect = [0 0 barWidth barHeight];
barPosition = CenterRectOnPointd(barRect, barStartX, barStartY);

% Run the animation loop
while ~KbCheck
    % Move the bar
    barPosition = OffsetRect(barPosition, deltaX, deltaY);
    
    % Check if the bar goes off the screen, wrap it around if needed
    if barPosition(1) > windowRect(3)
        barPosition = CenterRectOnPointd(barRect, barStartX, barStartY);
    end
    
    % Draw the bar at its new position
    Screen('FillRect', window, barColor, barPosition);
    Screen('Flip', window);
end

% Close Psychtoolbox
sca;
