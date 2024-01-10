function SLAP2UtilFuncs()
    P = py.sys.path;
    if count(P, '/mnt/cf28d361-d831-452b-ac27-06bb7bb8fb9e/SSD_Drive/SLAP2_Test_Binaries/SLAP2_Utils') == 0
        insert(P, int32(0), '/mnt/cf28d361-d831-452b-ac27-06bb7bb8fb9e/SSD_Drive/SLAP2_Test_Binaries/SLAP2_Utils');
    end


    % Create the UI figure
    fig = uifigure('Name', 'SLAP2 Util Functions', 'Position', [100 100 600 400]);

    % Create a grid layout
    gl = uigridlayout(fig, [6, 2]);
    gl.RowHeight = {30, 30, 30, 30, 30};
    gl.ColumnWidth = {'1x', '3x'};

    % Create the first file selector button and text box
    btnFileSelect1 = uibutton(gl, 'Text', 'Select TIF - T0');
    btnFileSelect1.Layout.Row = 1;
    btnFileSelect1.Layout.Column = 1;
    txtFilePath1 = uitextarea(gl);
    txtFilePath1.Layout.Row = 1;
    txtFilePath1.Layout.Column = 2;
    txtFilePath1.Editable = 'off';

    % Assign the callback function with additional parameters
    btnFileSelect1.ButtonPushedFcn = @(btn,event) fileSelectCallback(btn, txtFilePath1);

    % Create the second file selector button and text box
    btnFileSelect2 = uibutton(gl, 'Text', 'Select TIF - T1');
    btnFileSelect2.Layout.Row = 2;
    btnFileSelect2.Layout.Column = 1;
    txtFilePath2 = uitextarea(gl);
    txtFilePath2.Layout.Row = 2;
    txtFilePath2.Layout.Column = 2;
    txtFilePath2.Editable = 'off';

    % Assign the callback function with additional parameters
    btnFileSelect2.ButtonPushedFcn = @(btn,event) fileSelectCallback(btn, txtFilePath2);

    bntSoma = uibutton(gl, 'Text', 'Generate Soma ROI');
    bntSoma.Layout.Row = 3;
    bntSoma.Layout.Column = 1;
    bntSoma.ButtonPushedFcn = @(btn,event) somaCallback(btn, txtFilePath1);

    
    % Placeholder buttons
    for i = 4:5
        btn = uibutton(gl, 'Text', ['Button ' num2str(i)]);
        btn.Layout.Row = i;
        btn.Layout.Column = 1;
    end

    % Create a text area for debugging in the lower right corner
    txtDebug = uitextarea(gl);
    txtDebug.Layout.Row = 6; % Spanning two rows
    txtDebug.Layout.Column = [2,3]; % Last column
    txtDebug.Editable = 'off';



    function somaCallback(btn, txtFilePath)
        if isTifFilePath(txtFilePath) == 0;
            txtDebug.Value ='No Tiff Selected';
        else
            txtDebug.Value = 'Generating Soma ROI...';

            % Import the Python script as a module
            %pyModule = py.importlib.import_module('somaROI');
            %pyModule = py.importlib.reload(pyModule);
            filePath = txtFilePath.Value;
            filePath = strtrim(filePath{1})
            % Call the function in the Python script
            %pyROI_Ints = pyModule.genSomaROI(filePath);
            % Command to run the Python script
            %commandStr = sprintf('python3 -m somaROIsys.py %s', filePath);
            commandStr = sprintf('python3 -m slap2_utils.experiments.somaROIsys %s', filePath);
            % Execute the command and capture the output
            [status, pyROI_Ints] = system(commandStr);
            
            if status == 0
                % Parse the output if the script executed successfully
                pyROI_Ints = pyROI_Ints
                [folderPath, baseFileName, extension] = fileparts(filePath);
                newFileName = fullfile(folderPath, ['maskInts_' baseFileName '.mat']);
                somaInts = load(newFileName)
                maskData = somaInts.masks;
                figure;
                imagesc(maskData);
            else
                % Handle errors
                error('Python script failed: %s', pyROI_Ints);
            end
                
            % Convert the Python object to a MATLAB array
           


        end
    end
end

function fileSelectCallback(btn, txtFilePath)
    % File selection callback
    [file, path] = uigetfile('*.*');
    if file ~= 0
        txtFilePath.Value = fullfile(path, file);
    end
end




function isTifFile = isTifFilePath(txtFilePath)
    % Check if the text area contains a .tif file path
    value = txtFilePath.Value;
    
    % Handle cases where the value is an empty cell array
    if isempty(value) || (iscell(value) && all(cellfun(@isempty, value)))
        % If the text area is empty, return false
        isTifFile = false;
        return;
    end

    % Handle cases where the value is a cell array (multiline text area)
    if iscell(value)
        % Concatenate all lines into a single string
        value = strtrim(strjoin(value));
    end

    % Check if the string ends with .tif (case-insensitive)
    isTifFile = endsWith(lower(value), '.tif');
end


