
% Example usage
[myWin, winRect] = CreateStimWindow();

daqDevice = 'Dev1'; % Replace with your DAQ device name or ID
channel = 'ai1';   % Replace with the channel you want to listen to
threshold =4.8;   % Adjust the threshold as needed
callback = @myCallbackFunction; % Replace with your custom callback function
listenForRisingEdge(daqDevice, channel, threshold, callback, myWin);





function listenForRisingEdge(daqDevice, channel, threshold, callback, window)
    persistent DAQses,
    % Listen for a rising edge on the specified channel of the DAQ device.
    % When a rising edge is detected, execute the provided callback function.
    DAQ6001 = daq('ni')
    stimTrig = addoutput(DAQ6001, "Dev1", "ao0", "Voltage");
    % Create a DAQ session
    DAQses = daq.createSession('ni');


    % Add an analog input channel (or digital input channel) for listening
    ai1 = addAnalogInputChannel(DAQses, daqDevice, channel, 'Voltage');
    % Configure the input range and trigger settings
    DAQses.Rate = 1000; % Set the sample rate (adjust as needed)
    DAQses.IsContinuous = true;
    DAQses.TriggersPerRun = 1;    
    % Define the trigger condition (rising edge detection)
    lh = DAQses.addlistener('DataAvailable', @(src, event) detectRisingEdge(event, threshold, callback));
    
    % Start the DAQ session
    startBackground(DAQses);


    function detectRisingEdge(event, threshold, callback)
        data = event.Data
        % Check for a rising edge (assuming the input is a voltage signal)
        if any(event.Data > threshold) %&& data(end-1) <= threshold
            % Rising edge detected, execute the callback
            myCallbackFunction();
           
        end
    end
    
    
    % Define your custom callback function
    function myCallbackFunction()
        disp('Rising edge detected!'); % Replace with your desired action
        delete(lh)

        % First test: grating, but will move on to others laters
        %[t, sType, angle, speed] = 
        gratingProbing(window, DAQ6001)
        
        pause(4)
    end
end


