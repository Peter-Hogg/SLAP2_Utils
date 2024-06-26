function StimControl(s2Obj)

% Log all Stim to an array
stimlog.time = {};
stimlog.stim_type = {};
stimlog.stim_info = {};

%Added
stimlog.stim_freq = {};
stimlog.stim_orientation = {};


% Create a directory to save the stimLog array as
if ~exist('stimLogs', 'dir')
mkdir('stimLogs')
end


StimControlPanel = figure('Color','w');
[myWin, winRect] = CreateStimWindow();
ToggleScreenOff = 0
DAQ6001 = daq('ni')
stimTrig = addoutput(DAQ6001, "Dev1", "ao0", "Voltage");

%StimPanel = uifigure;
%toggleOFFButton = uicontrol(gcf,'Style', 'push', ...
%                          'String', 'Toggle Screen Off', ...
%                           'Position', [20 260 80 30], ...
%                           'CallBack', @toggleOFF);




OFFStimBut = uicontrol(gcf,'Style', 'push', ...
                           'String', 'OFF Stim', ...
                           'Position', [20 170 80 30], ...
                           'CallBack', @OffStimPush);


batteryGratingButton = uicontrol(gcf,'Style', 'push', ...
                           'String', 'Pseudo Random Grating', ...
                           'Position', [20 200 200 30], ...
                           'CallBack', @randoGrating);


userGratingButton = uicontrol(gcf,'Style', 'push', ...
                           'String', 'User Angle', ...
                           'Position', [20 60 100 30], ...
                           'CallBack', @userGrating);

psuedoRandSTA = uicontrol(gcf,'Style', 'push', ...
                           'String', 'Pseudo Random STA', ...
                           'Position', [20 230 180 30], ...
                           'CallBack', @randSTAStimuli);

%Added
allenRandSTA = uicontrol(gcf,'Style', 'push', ...
                           'String', 'Allen Checker STA', ...
                           'Position', [20 260 180 30], ...
                           'CallBack', @allenSTAStimuli);

userSquareGratingn = uicontrol(gcf,'Style', 'push', ...
                           'String', 'Square Grating', ...
                           'Position', [20 140 180 30], ...
                           'CallBack', @SquareGrating);


CloseWinButton = uicontrol(gcf,'Style', 'push', ...
                           'String', 'Close Stim Window', ...
                           'BackgroundColor', 'red', ...
                           'Position', [20 10 200 30], ...
                           'CallBack', @closeStimWindow);

SingleBarStim = uicontrol(gcf,'Style', 'push', ...
                           'String', 'Single Bar', ...
                           'Position', [20 290 180 30], ...
                           'CallBack', @singleBarStim);

SingleSineStim = uicontrol(gcf,'Style', 'push', ...
                           'String', 'Single Sine Bar', ...
                           'Position', [20 320 180 30], ...
                           'CallBack', @singleSineStim);

primeExperiment = uicontrol(gcf,'Style', 'push', ...
                           'String', 'Prime Experiment', ...
                           'BackgroundColor', 'green', ...
                           'Position', [20 350 180 30], ...
                           'CallBack', @primeStim);


blankScreen = uicontrol(gcf,'Style', 'push', ...
                           'String', 'Blank Screen', ...
                           'Position', [20 380 180 30], ...
                           'CallBack', @blankScreenCallback);

% Java Slider to pick grating angle 
userAngel = javaObjectEDT(javax.swing.JSlider(0,360,1))
userAngel.setBackground(java.awt.Color.white);  % Java setter-method notation
userAngel.setPaintTicks(true);
set(userAngel, 'MinorTickSpacing',15, 'MajorTickSpacing',90, 'SnapToTicks',true, 'PaintLabels',true);  % HG set notation
[hSlider5, hContainer5] = javacomponent(userAngel, [120 60 250 45], StimControlPanel);


function OffStimPush(source,event)
    [t, sType, stimD] = OFFStim(myWin, DAQ6001);
    stimlog.time = [stimlog.time, {t}]
    stimlog.stim_type = [stimlog.stim_type, {sType}]
    stimlog.stim_info = [stimlog.stim_info, {stimD}]
end


function toggleOFF(source,event)
    % Full Field Off Simulus - 50 ms 
    toggleStimOFF(myWin, DAQ6001);


end
function userGrating(source,event)
    speed = 10;
    ang = userAngel.getValue;
    [t, sType] = GenGrating(myWin, ang, speed, .0034, 1920, 1080, DAQ6001);
    stimlog.time = [stimlog.time, {t}]
    stimlog.stim_type = [stimlog.stim_type, {sType}]
    stimlog.stim_frequency = [stimlog.stim_frequency, {speed}]
    stimlog.stim_orientation = [stimlog.stim_orientation, {ang}]
    %ang = userAngel.getValue
    %GenGrating(myWin, ang, 2, .0034, 1200, 1200, DAQ6001)
end

function singleBarStim(source,event)
    speed = 2;
    ang = userAngel.getValue;
    [t, sType] = SingleBar(myWin, 45, speed, 5000, 500, 1080, DAQ6001);
    stimlog.time = [stimlog.time, {t}]
    stimlog.stim_type = [stimlog.stim_type, {sType}]
    stimlog.stim_frequency = [stimlog.stim_frequency, {speed}]
    stimlog.stim_orientation = [stimlog.stim_orientation, {ang}]
    %ang = userAngel.getValue
    %GenGrating(myWin, ang, 2, .0034, 1200, 1200, DAQ6001)
end

function singleSineStim(source,event)
    speed = 2;
    ang = userAngel.getValue;
    [t, sType] = SingleSine(myWin, 135, speed, 5000, 500, 1080, DAQ6001);
    stimlog.time = [stimlog.time, {t}]
    stimlog.stim_type = [stimlog.stim_type, {sType}]
    stimlog.stim_frequency = [stimlog.stim_frequency, {speed}]
    stimlog.stim_orientation = [stimlog.stim_orientation, {ang}]
    %ang = userAngel.getValue
    %GenGrating(myWin, ang, 2, .0034, 1200, 1200, DAQ6001)
end


function SquareGrating(source,event)
    speed = 2;
    ang = userAngel.getValue;
    [t, sType] = GenSquareGrating(myWin, ang, speed, .0034, 1920, 1080, DAQ6001);
    stimlog.time = [stimlog.time, {t}]
    stimlog.stim_type = [stimlog.stim_type, {sType}]
    stimlog.stim_frequency = [stimlog.stim_frequency, {speed}]
    stimlog.stim_orientation = [stimlog.stim_orientation, {ang}]
    %ang = userAngel.getValue
    %GenGrating(myWin, ang, 2, .0034, 1200, 1200, DAQ6001)
end


function randoGrating(source,event)

    r = readmatrix('Rand_Grating.txt');
    [t, sType, angle, speed] = pseudoRandGrating(myWin, r, DAQ6001)
    stimlog.time = [stimlog.time, {t}]
    stimlog.stim_type = [stimlog.stim_type, {sType}]
    stimlog.stim_frequency = [stimlog.stim_frequency, {speed}]
    stimlog.stim_orientation = [stimlog.stim_orientation, {angle}]



end

function randSTAStimuli(source,event)
    r = readmatrix('Rand_OriCheck_15.txt')
    for i = [1:1:15]
        fprintf("STA Stim "+ i)
        
        t2 = now();
        datetime(t2,'ConvertFrom','datenum')
        [t, sType, stimD] = STACheckerStim(myWin, winRect, r, DAQ6001);
        stimlog.time = [stimlog.time, {t}];
        datetime(t,'ConvertFrom','datenum')
        stimlog.stim_type = [stimlog.stim_type, {sType}];
        stimlog.stim_info = [stimlog.stim_info, {stimD}];
        x = randi([2,6]);
        pause(x);
    end
    
    t3 = now();
    datetime(t3,'ConvertFrom','datenum')


end

function allenSTAStimuli(source,event)
     r = readmatrix('Rand_AllenCheck_15.txt')
     for i = [1:1:1]
        fprintf("STA Stim "+ i)
        
        t2 = now();
        datetime(t2,'ConvertFrom','datenum')
        [sType] = AllenSTACheckerFast(myWin, winRect, 3, 200, DAQ6001);
        stimlog.time = [stimlog.time, {t}];
        datetime(t,'ConvertFrom','datenum')
        %stimlog.stim_type = [stimlog.stim_type, {sType}];
        %stimlog.stim_info = [stimlog.stim_info, {stimD}];
        x = randi([2,6]);
        pause(x);
    end
    
    t3 = now();
    datetime(t3,'ConvertFrom','datenum')


end

function primeStim(source,event)
     %AllenSTACheckerFast(myWin, winRect, 0.05, 250,  DAQ6001);
     gratingRFbattery(myWin, winRect, DAQ6001);
     %RFTriggerStim(myWin, winRect, DAQ6001);


end

    function blankScreenCallback(source,event)
        
        if ToggleScreenOff == 0
                colorFill = [255,0,0];
                Screen('Fillrect', myWin, colorFill);
                Screen('Flip', myWin);
                ToggleScreenOff = 1
        else ToggleScreenOff == 1
             ToggleScreenOff = 0
             colorFill = [0,0,0];
             Screen('Fillrect', myWin, colorFill);
             Screen('Flip', myWin);
        end

end
function saveStimLog(source,event)
    saveTime = clock();
    fileName = ['stimLog', saveTime(4:6), '.csv']
    writetable(stimLog, fullfile('stimLogss', fileName) )
end

function closeStimWindow(source,event)
    sca;
end

end