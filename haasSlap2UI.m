function haasSlap2UI(localSlap, localGUI)
    
    % temp edit, original: 'C:\Users\haasl\Documents\SLAP2_Utils'
    shift_record = [0;0;0];
    slap2PythonPath = 'C:\Users\haasl\Documents\SLAP2_Utils';
    setenv('PYTHONPATH', slap2PythonPath);    setenv('PYTHONPATH', slap2PythonPath);
    P = py.sys.path;
    if count(P, 'C:\Users\haasl\Documents\SLAP2_Utils') == 0;
        insert(P, int32(0), 'C:\Users\haasl\Documents\SLAP2_Utils');
    end
    mod = py.importlib.import_module('slap2_utils');

    % Create the UI figure
    fig = uifigure('Name', 'SLAP2 Util Functions', 'Position', [100 100 600 400]);

    % Create a grid layout
    gl = uigridlayout(fig, [6, 6]);
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


    % DMD Radio button for latest file
    tiffDMDgroup = uibuttongroup(gl); 
    tiffDMDgroup.Layout.Row = 1;
    tiffDMDgroup.Layout.Column = [4:5];
    rb1 = uiradiobutton(tiffDMDgroup, 'Text', 'DMD1', 'Position', [20, 10, 80, 20]);
    rb2 = uiradiobutton(tiffDMDgroup, 'Text', 'DMD2', 'Position', [95, 10, 100, 20]);
    %fullFileName

    % Button to average last tiff
    lastAcquTif = uibutton(gl, 'Text', 'Last TIF');
    lastAcquTif.Layout.Row = 1;
    lastAcquTif.Layout.Column = 6;
    lastAcquTif.ButtonPushedFcn = @(btn,event) lastTifCallBack(btn, localSlap, rb1, rb2, txtFilePath1);

    
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
    bntSoma.ButtonPushedFcn = @(btn,event) somaCallback(btn, txtFilePath1, localSlap);

    
    btnAvgStack = uibutton(gl, 'Text', ['Avg Stack']);
    btnAvgStack.Layout.Row = 4;
    btnAvgStack.Layout.Column = 1;
    btnAvgStack.ButtonPushedFcn = @(btn,event) avgStackCallback(btn, txtFilePath1);


    % Jerry - Button for ROI shift, under dev
    btnShift = uibutton(gl, 'Text', 'Shift 2stacks');
    btnShift.Layout.Row = 5;
    btnShift.Layout.Column = 1;
    btnShift.ButtonPushedFcn = @(btn,event) ShiftAdjustment(btn,txtFilePath1,txtFilePath2,localSlap);


    btnShiftPlane = uibutton(gl, 'Text', 'Shift UI');
    btnShiftPlane.Layout.Row = 6;
    btnShiftPlane.Layout.Column = 1;
    
   
    
    % Saved image path for 

    btnShiftPlane.ButtonPushedFcn = @(btn,event) ShiftAdjustmentUI(btn,txtFilePath1,localSlap,localGUI);
    




    % Placeholder buttons
    
    btn = uibutton(gl, 'Text', ['Button ' num2str(i)]);
    btn.Layout.Row = 7;
    btn.Layout.Column = 1;

    % Create a text area for debugging in the lower right corner
    txtDebug = uitextarea(gl);
    txtDebug.Layout.Row = 7; % Spanning two rows
    txtDebug.Layout.Column = [2,3]; % Last column
    txtDebug.Editable = 'off';



    function somaCallback(btn, txtFilePath, localSlap)
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
                metaData = t.getTag('ImageDescription');
                hSliceData = jsondecode(metaData);
                genIntROIPlane(localSlap, maskData, hSliceData.AcquisitionPathIdx, hSliceData.zsAbsolute);
                

            else
                % Handle errors
                error('Python script failed: %s', pyROI_Ints);
            end
                
            % Convert the Python object to a MATLAB array
           


        end
    end
end

% Jerry - Shift Adjustment
function ShiftAdjustment(btn,txtFilePath1,txtFilePath2,localSlap)
    if localSlap.arm == 0
       localSlap.disarm;
    end 

    if isTifFilePath(txtFilePath1) == 0
        txtDebug.Value ='No Tiff Selected';
    end
    if isTifFilePath(txtFilePath2) == 0
        txtDebug.Value ='No Tiff Selected';
    end

    % Select the two path
    filePath1 = txtFilePath1.Value;
    filePath1 = strtrim(filePath1{1});
  

    filePath2 = txtFilePath2.Value;
    filePath2 = strtrim(filePath2{1});
    
    disp(filePath1)
    disp(filePath2);

  % in linux this will be python 
    commandStr = sprintf('python -m slap2_utils.functions.xyzshift %s %s', filePath1, filePath2);
    
    [status, result] = system(commandStr);

    % Using str as output, and result is converted, order is z, y, x
    shift_list = str2num (result);
    
    shift_list(2)=round(shift_list(2));
    shift_list(3)=round(shift_list(3));

    % Change local variable
    
    % Loop through local field to change it
    for i = 1:length(localSlap.hAcquisitionPath1.rois)
        localSlap.hAcquisitionPath1.rois(1,i).z = localSlap.hAcquisitionPath1.rois(1,i).z - shift_list(1);
        for j = 1:length(localSlap.hAcquisitionPath1.rois(1, i).shapeData)
            localSlap.hAcquisitionPath1.rois(1,i).shapeData(j,1) = localSlap.hAcquisitionPath1.rois(1,i).shapeData(j,1) - shift_list(2);
            localSlap.hAcquisitionPath1.rois(1,i).shapeData(j,2) = localSlap.hAcquisitionPath1.rois(1,i).shapeData(j,2) - shift_list(3);


        end

    end

     for i = 1:length(localSlap.hAcquisitionPath2.rois)
        localSlap.hAcquisitionPath2.rois(1,i).z = localSlap.hAcquisitionPath2.rois(1,i).z - shift_list(1);
        for j = 1:length(localSlap.hAcquisitionPath2.rois(1, i).shapeData)

            localSlap.hAcquisitionPath2.rois(1,i).shapeData(j,1) = localSlap.hAcquisitionPath2.rois(1,i).shapeData(j,1) - shift_list(2);
            localSlap.hAcquisitionPath2.rois(1,i).shapeData(j,2) = localSlap.hAcquisitionPath2.rois(1,i).shapeData(j,2) - shift_list(3);

        end 
     end



    
    if status == 0
        txtDebug.Value = 'worked';
    end
    localSlap.arm;
end


% Jerry - Shift Adjustment UI
function ShiftAdjustmentUI(btn,txtFilePath1,localSlap,localGUI)
    
    if localSlap.armed == 0
       localSlap.disarm;
    end 
    basePath = localSlap.fileDir;

    Folderinfo = dir(basePath);
    
    newestdate=-100;
    newestname='100';
    for i = 1:length(Folderinfo)
        if contains(Folderinfo(i).name, 'UIimg')
            if newestdate == -100 | newestdate > Folderinfo(i).datenum
                newestdate = Folderinfo(i).datenum
                newestname = Folderinfo(i).name
            end

        end
    end

    if isTifFilePath(txtFilePath1) == 0
        txtDebug.Value ='No Tiff Selected';
    end


    % Select the two path
    filePath1 = txtFilePath1.Value;
    filePath1 = strtrim(filePath1{1});
    [path,name,~] = fileparts(filePath1);
    filePath1 = strcat(path,'\averageGPU_',name,'.tif');
  

    imagecell =  localGUI.hViewports(1).hImView.hFrameDisplayBuffer.data(1,1);
    image = imagecell{1,1}{1,1};

    % We rotate it because its been rotated when compared with the image
    image = rot90(image,3);
    image = fliplr(image);
    imagepath = strcat(path,'\',name,'UIimg.tif');
    

    
    
    t = Tiff(imagepath,'w');
    image = uint32(image);
    % Setup tags
    % Lots of info here:
    % http://www.mathworks.com/help/matlab/ref/tiffclass.html
    tagstruct.ImageLength     = size(image,1);
    tagstruct.ImageWidth      = size(image,2);
    tagstruct.Photometric     = Tiff.Photometric.MinIsBlack;
    tagstruct.BitsPerSample   = 32;
    tagstruct.SamplesPerPixel = 1;
    tagstruct.RowsPerStrip    = 16;
    %tagstruct.PlanarConfiguration = Tiff.PlanarConfiguration.Chunky;
    tagstruct.Software        = 'MATLAB';
    t.setTag(tagstruct)
    
    t.write(image);
    t.close();

    slice = localGUI.hViewports(1).currentZ;

    

  % in linux this will be python 
    commandStr = sprintf('python -m slap2_utils.functions.xyzshift_ui %s %d %s', filePath1, slice, imagepath);
    
    
    [status, result] = system(commandStr);

    
    % Using str as output, and result is converted, order is z, y, x
    shift_list = str2num (result);
    for i = 1:length(shift_list)
        shift_list(i)=round(shift_list(i)) - shift_record(i);
        shift_record(i)=shift_list(i);        
    end
    
    if newestdate == -100
        % Change local variable
     
        
        % Loop through local field to change it
        for i = 1:length(localSlap.hAcquisitionPath1.rois)
            localSlap.hAcquisitionPath1.rois(1,i).z = localSlap.hAcquisitionPath1.rois(1,i).z - shift_list(1);
            for j = 1:length(localSlap.hAcquisitionPath1.rois(1, i).shapeData)
                localSlap.hAcquisitionPath1.rois(1,i).shapeData(j,1) = localSlap.hAcquisitionPath1.rois(1,i).shapeData(j,1) - shift_list(2);
                localSlap.hAcquisitionPath1.rois(1,i).shapeData(j,2) = localSlap.hAcquisitionPath1.rois(1,i).shapeData(j,2) - shift_list(3);
    
    
            end
    
        end
    
         for i = 1:length(localSlap.hAcquisitionPath2.rois)
            localSlap.hAcquisitionPath2.rois(1,i).z = localSlap.hAcquisitionPath2.rois(1,i).z - shift_list(1);
            for j = 1:length(localSlap.hAcquisitionPath2.rois(1, i).shapeData)
    
                localSlap.hAcquisitionPath2.rois(1,i).shapeData(j,1) = localSlap.hAcquisitionPath2.rois(1,i).shapeData(j,1) - shift_list(2);
                localSlap.hAcquisitionPath2.rois(1,i).shapeData(j,2) = localSlap.hAcquisitionPath2.rois(1,i).shapeData(j,2) - shift_list(3);
    
            end 
         end
    
    
        localSlap.arm;
    
        if status == 0
            txtDebug.Value = 'worked';
        end

    else 
        
        commandStr2 = sprintf('python -m slap2_utils.functions.xyzshift_ui %s %d %s', filePath1, slice, imagepath);

        [~, result2] = system(commandStr2);

    
        % Using str as output, and result is converted, order is z, y, x
        shift_list2 = str2num (result2);
        for i = 1:length(shift_list2)
            shift_list2(i)=round(shift_list2(i));
        end

        for i = 1:length(localSlap.hAcquisitionPath1.rois)
            localSlap.hAcquisitionPath1.rois(1,i).z = localSlap.hAcquisitionPath1.rois(1,i).z - shift_list(1) + shift_list2(1);
            for j = 1:length(localSlap.hAcquisitionPath1.rois(1, i).shapeData)
                localSlap.hAcquisitionPath1.rois(1,i).shapeData(j,1) = localSlap.hAcquisitionPath1.rois(1,i).shapeData(j,1) - shift_list(2) + shift_list2(2);
                localSlap.hAcquisitionPath1.rois(1,i).shapeData(j,2) = localSlap.hAcquisitionPath1.rois(1,i).shapeData(j,2) - shift_list(3) + shift_list2(3);
    
    
            end
    
        end
    
         for i = 1:length(localSlap.hAcquisitionPath2.rois)
            localSlap.hAcquisitionPath2.rois(1,i).z = localSlap.hAcquisitionPath2.rois(1,i).z - shift_list(1) + shift_list2(1);
            for j = 1:length(localSlap.hAcquisitionPath2.rois(1, i).shapeData)
    
                localSlap.hAcquisitionPath2.rois(1,i).shapeData(j,1) = localSlap.hAcquisitionPath2.rois(1,i).shapeData(j,1) - shift_list(2) + shift_list2(2);
                localSlap.hAcquisitionPath2.rois(1,i).shapeData(j,2) = localSlap.hAcquisitionPath2.rois(1,i).shapeData(j,2) - shift_list(3) + shift_list2(3);
    
            end 
         end
    
    
        localSlap.arm;
    
        if status == 0
            txtDebug.Value = 'worked';
        end

    end
    


end

function avgStackCallback(btn, txtFilePath)
        if isTifFilePath(txtFilePath) == 0;
            txtDebug.Value ='No Tiff Selected';
        else
            txtDebug.Value = 'Generating Average Stack...';

            filePath = txtFilePath.Value;
            filePath = strtrim(filePath{1});
  
            commandStr = sprintf('python -m slap2_utils.functions.imagestacks %s', filePath)
            [status, avgStackPath] = system(commandStr);
            
            if status == 0
                txtDebug.Value = 'Average Stack Complete';
            else
                % Handle errors
                error('Python script failed: %s', avgStackPath);
            end
                
          


        end
end

function autoROICallback(btn, txtFilePath)
        if isTifFilePath(txtFilePath) == 0;
            txtDebug.Value ='No Tiff Selected';
        else
            txtDebug.Value = 'Generating Average Stack...';

            filePath = txtFilePath.Value;
            filePath = strtrim(filePath{1});
  
            commandStr = sprintf('python -m slap2_utils.functions.imagestacks %s', filePath);
            [status, avgStackPath] = system(commandStr);
            
            if status == 0
                txtDebug.Value = 'Average Stack Complete';
                [folderPath, baseFileName, extension] = fileparts(filePath);
                newFileName = fullfile(folderPath, ['averageGPU_' baseFileName extension]);
                commandStr = sprintf('python -m slap2_utils.functions.unetROI %s', newFileName)
                [status2, avgStackPath] = system(commandStr);
                if status2 == 0
                    txtDebug.Value = 'ROI Created';
                
                else
                    error('Python script failed: %s', avgStackPath);

                end
                %somaInts = load(newFileName);
                %maskData = somaInts.masks;
                %figure;
                %imagesc(maskData);

                % Get metadata for slize info
                %t = Tiff(filePath,'r');
                %meataData = t.getTag('ImageDescription');
                %hSliceData = jsondecode(meataData);
                %genIntROIPlane(maskData, hSliceData.AcquisitionPathIdx, hSliceData.zsAbsolute);
                
            
                txtDebug.Value = 'ROI Created';

            else
                % Handle errors
                error('Python script failed: %s', avgStackPath);
            end
                
            % Convert the Python object to a MATLAB array
           


        end
end

function fileSelectCallback(btn, txtFilePath)
    % File selection callback
    [file, path] = uigetfile('*.*');
    if file ~= 0
        txtFilePath.Value = fullfile(path, file);
    end
end


function lastTifCallBack(btn, localSlap,  dmd1, dmd2, txtFilePath)
    basePath = localSlap.fullFileName;
    if dmd1.Value
        pathEnd =   '_DMD1.tif';
    end
    if dmd2.Value
        pathEnd =   '_DMD1.tif';
    end
    if basePath ~= 0
        txtFilePath.Value = strcat(basePath, pathEnd);
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

function genIntROIPlane(hS2Local, labelsArr, pathID, zPos)
    
    roiList =  arrayfun(@(hAcqPath)hAcqPath.rois,hS2Local.hAcquisitionPaths,'UniformOutput',false);
    
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
    
    
    hS2Local.hAcquisitionPaths(pathID).rois = roiList{pathID}


end



%% Import the array, each interger is an roi
function loadROI(roiMATfile)
    labels = load(roiMATfile);
    stack_size = size(labels);
    roiList =  arrayfun(@(hAcqPath)hAcqPath.rois,hS2.hAcquisitionPaths,'UniformOutput',false);
   
    %% Array of unique 
    stepSize = 2;
    for i = 1:stack_size[0]
        slice =  squeeze(labels(i,:,:));
        labelInts = unique(slice);
    
        for j = 1:length(labelInts)
    
            label = labelInts(j)
            if label>0;
                z = hS2.hAcquisitionPath1.acquisitionZs(i);
                [row, col] = find(slice ==label);
                roi_coord = double([row,col]);
                slap2_roi = slap2.roi.ArbitraryRoi(roi_coord, "Integrate", 5000);
                slap2_roi.z = z;
                roiList{1}(end+1) = slap2_roi;
        
            end
        end
    end
    
    hS2.hAcquisitionPaths(1).rois = roiList{1}
end

