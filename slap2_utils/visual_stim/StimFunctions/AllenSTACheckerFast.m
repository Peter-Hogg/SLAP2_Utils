function  [randSquare] = AllenSTACheckerFast(win, winRect, totalsquare, sizes, daq)
    % Get the size of the on screen window
    [screenXpixels, screenYpixels] = Screen('WindowSize', win);
    
    % Get the centre coordinate of the window
    [xCenter, yCenter] = RectCenter(winRect);
    
    % Make a base Rect of 200 by 200 pixels

    % Window is ~1800 x 1200
    lengthgrid = floor(950/sizes);
    widthgrid = floor(500/sizes)
    
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
    randSquare = [];
    %Adjust Probability Here
    for k = 1:1:16
        % Randomly choose which squares are black and white
        

        r=randi(2,numSquares,1)-1;
        possible_index_light = [1:numSquares];
        possible_index_dark = [1:numSquares];




        
        black=[];
        white=[];
        surround = [(-s1-1),(-s1),(1-s1),-1,0,1,s1-1,s1,s1+1];
        for i = 1: numSquares
            r(i)=0.5;
        end

       

        for j = 1: totalsquare
            lightindex = randsample(possible_index_light,1);
            white=[white;lightindex];
            possible_index_dark = possible_index_dark(possible_index_dark~=lightindex);
            darkindex = randsample(possible_index_dark,1);
            possible_index_light = possible_index_light(possible_index_light~=darkindex);
            black=[black;darkindex];
            for m = 1:9
                val = lightindex+surround(m);
                %possible_index_light = possible_index_light(possible_index_light~=val);
                possible_index_light(possible_index_light == val) = [];
            end
            for o = 1:9
                val = darkindex+surround(o);
                %possible_index_dark = possible_index_dark(possible_index_dark~=val);
                possible_index_dark(possible_index_dark == val) = [];
            end
            
            r(lightindex)=1;
            r(darkindex)=0;
           
               
        end
        black_white={black,white};
        randSquare=[randSquare;black_white];
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
        pause(.5);
        % Flip to the screen
        Screen('Flip', win);
        write(daq, 3);
        pause(.001);
        write(daq, 0);

        Screen('Fillrect', win, [127, 127, 127]);
        Screen('Flip', win);
        pause(.5);


    end

    pause(4);


    Screen('Flip', win);
    %write(daq, 3);
    %pause(.001);
    %write(daq, 0);
    
end

