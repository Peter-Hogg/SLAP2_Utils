%%% Create a timestamp of tiggers from the SLAP2 microscope 
%%% that present visual stimulus
usbDaq = daq('ni');

addinput(usbDaq, 'Dev1', 0, 'Voltage');

stimTrig = addtrigger(usbDaq, 'Digital', 'StartTrigger', 'External', 'Dev1/PFI0');

stimTrig.Condition = 'FallingEdge';

fprintf('Stim')