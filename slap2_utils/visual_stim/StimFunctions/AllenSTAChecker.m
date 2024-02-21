function  [time, sType] = AllenSTAChecker(win, winRect, blackidx, whiteidx, sizes, daq)
    % Get the size of the on screen window
    [screenXpixels, screenYpixels] = Screen('WindowSize', win);
    
    % Get the centre coordinate of the window
    [xCenter, yCenter] = RectCenter(winRect);
    
    % Make a base Rect of 200 by 200 pixels

    % Window is ~1800 x 1200
    lengthgrid = floor(900/sizes);
    widthgrid = floor(600/sizes)
    dim = sizes;
    baseRect = [0 0 dim dim];
    
    % Make the coordinates for our grid of squares
    [xPos, yPos] = meshgrid((-1*lengthgrid):1:(lengthgrid), (-1*widthgrid):1:(widthgrid));

    
    
    % Calculate the number of squares and reshape the matrices of coordinates
    % into a vector
    [s1, s2] = size(xPos);
    numSquares = s1 * s2;
    xPos = reshape(xPos, 1, numSquares);
    yPos = reshape(yPos, 1, numSquares);
    
    % Scale the grid spacing to the size of our squares and centre
    xPosPlot = xPos .* dim + screenXpixels * 0.50;
    yPosPlot = yPos .* dim + yCenter;

    %Adjust Probability Here


    % Set up background as default
    
    for i = 1: numSquares
        r(i) = 0.5;  
    end

    % Set up nonrandom
    r(blackidx) = 1;  
    r(whiteidx) = 1;
 

    % Make our rectangle coordinates
    randPixel = nan(3, 3);
    for i = 1:numSquares
        randPixel(:, i) = r(i)*255;
    end


    % Make our rectangle coordinates
    Rects = nan(4, 3);
    for i = 1:numSquares
        Rects(:, i) = CenterRectOnPointd(baseRect, xPosPlot(i), yPosPlot(i));
    end



    time = clock;
    write(daq, 3);
    pause(.001);
    write(daq, 0);
    Screen('FillRect', win, randPixel, Rects);
    pause(1);
    % Flip to the screen
    Screen('Flip', win);


    pause(1);


    Screen('Flip', win);
    write(daq, 3);
    pause(.001);
    write(daq, 0);
    sType = 'alllenRandSTA';
end

