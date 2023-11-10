function listenForRisingEdge(daqDevice, channel, threshold, callback)
    % Listen for a rising edge on the specified channel of the DAQ device.
    % When a rising edge is detected, execute the provided callback function.

    % Create a DAQ session
    s = daq.createSession('ni');
    
    % Add an analog input channel (or digital input channel) for listening
    addAnalogInputChannel(s, daqDevice, channel, 'Voltage');
    
    % Configure the input range and trigger settings
    s.Rate = 1000; % Set the sample rate (adjust as needed)
    s.IsContinuous = true;
    s.TriggersPerRun = inf;
    
    % Define the trigger condition (rising edge detection)
    listener = s.addlistener('DataAvailable', @(src, event) detectRisingEdge(event, threshold, callback));
    
    % Start the DAQ session
    startBackground(s);
end

function detectRisingEdge(event, threshold, callback)
    % This function is called when data is available from the DAQ device.
    % It checks for a rising edge and executes the callback if detected.
    
    data = event.Data;
    
    % Check for a rising edge (assuming the input is a voltage signal)
    if data(end) > threshold && data(end-1) <= threshold
        % Rising edge detected, execute the callback
        callback();
    end
end


% Example usage
daqDevice = 'Dev1'; % Replace with your DAQ device name or ID
channel = 'ai0';   % Replace with the channel you want to listen to
threshold = 2.0;   % Adjust the threshold as needed
callback = @myCallbackFunction; % Replace with your custom callback function

listenForRisingEdge(daqDevice, channel, threshold, callback);

% Define your custom callback function
function myCallbackFunction()
    disp('Rising edge detected!'); % Replace with your desired action
end
