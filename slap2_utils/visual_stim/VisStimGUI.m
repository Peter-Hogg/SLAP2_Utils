function StimControl(s2Obj)

% Log all Stim to an array
stimlog.time = {};
stimlog.stim_type = {};
stimlog.stim_info = {};
% Create a directory to save the stimLog array as
if ~exist('stimLogs', 'dir')
mkdir('stimLogs')
end


StimControlPanel = figure('Color','w');
[myWin, winRect] = CreateStimWindow();

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

CloseWinButton = uicontrol(gcf,'Style', 'push', ...
                           'String', 'Close Stim Window', ...
                           'BackgroundColor', 'red', ...
                           'Position', [20 10 200 30], ...
                           'CallBack', @closeStimWindow);

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
    ang = userAngel.getValue
    GenGrating(myWin, ang, 2, .0034, 1200, 1200, DAQ6001)
end

function randoGrating(source,event)
    pseudoRandGrating(myWin, DAQ6001)
end

function randSTAStimuli(source,event)
    
    for i = [1:1:15]
        fprintf("STA Stim "+ i)
        
        t2 = now();
        datetime(t2,'ConvertFrom','datenum')
        [t, sType, stimD] = STACheckerStim(myWin, winRect, DAQ6001);
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


function saveStimLog(source,event)
    saveTime = clock();
    fileName = ['stimLog', saveTime(4:6), '.csv']
    writetable(stimLog, fullfile('stimLogss', fileName) )
end

function closeStimWindow(source,event)
    sca;
end

end
