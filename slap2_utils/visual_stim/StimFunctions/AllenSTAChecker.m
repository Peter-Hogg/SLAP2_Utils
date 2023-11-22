function  [time, sType, r] = AllenSTAChecker(win, winRect, r, daq)
    % Get the size of the on screen window
    [screenXpixels, screenYpixels] = Screen('WindowSize', win);
    
    % Get the centre coordinate of the window
    [xCenter, yCenter] = RectCenter(winRect);
    
    % Make a base Rect of 200 by 200 pixels
    dim = 100;
    baseRect = [0 0 dim dim];
    
    % Make the coordinates for our grid of squares
    [xPos, yPos] = meshgrid(-9:1:9, -6:1:6);

    
    
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
    prob=0.05;


    % Randomly choose which squares are black and white
    r=randi(2,numSquares,1)-1;
    for i = 1: numSquares
        if r(i)==1
            if prob>rand()
                if 0.5 >=rand()
                    r(i)=r(i)*1;
                else
                    r(i)=0;
                end
            else
                r(i)=0.5;
            end
        else 
            r(i)=0.5;
        end
       
    end

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


    pause(5);


    Screen('Flip', win);
    write(daq, 3);
    pause(.001);
    write(daq, 0);
    sType = 'alllenRandSTA';
end

