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

            filePath = txtFilePath.Value;
            filePath = strtrim(filePath{1});
      
            % Command to run the Python script
            %commandStr = sprintf('python3 -m somaROIsys.py %s', filePath);
            commandStr = sprintf('python -m slap2_utils.experiments.somaROIsys %s', filePath);
            % Execute the command and capture the output
            [status, pyROI_Ints] = system(commandStr);
            
            if status == 0
                % Parse the output if the script executed successfully
                pyROI_Ints = pyROI_Ints
                [folderPath, baseFileName, extension] = fileparts(filePath);
                newFileName = fullfile(folderPath, ['maskInts_' baseFileName '.mat']);
                somaInts = load(newFileName);
                maskData = somaInts.masks;
                figure;
                imagesc(maskData);

                % Get metadata for slize info
                t = Tiff(filePath,'r');
                meataData = t.getTag('ImageDescription');
                hSliceData = jsondecode(meataData);
                genIntROIPlane(maskData, hSliceData.AcquisitionPathIdx, hSliceData.zsAbsolute);
                

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

function genIntROIPlane(labelsArr, pathID, zPos)
    
    roiList =  arrayfun(@(hAcqPath)hAcqPath.rois,hS2.hAcquisitionPaths,'UniformOutput',false);
    
    slice =  squeeze(labelsArr);
    labelInts = unique(slice);
    
    for j = 1:length(labelInts)
    
        label = labelInts(j)
        if label>0;
            [row, col] = find(slice ==label);
            roi_coord = double([row,col+400]);
            slap2_roi = slap2.roi.ArbitraryRoi(roi_coord, "Integrate", 5000);
            slap2_roi.z = zPos;
            roiList{pathID}(end+1) = slap2_roi;
    
        end
    end
    
    
    hS2.hAcquisitionPaths(pathID).rois = roiList{pathID}


end