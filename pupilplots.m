%simple function to plot pupil points
%for dark

<<<<<<< HEAD
yL = [-1 4];
fig = figure('Name','Pupil During Dark Test'); 
k=plot(timeStampAll_dark,rightEyeAll_dark(:,12));
set(k, 'Color', 'm')
=======
function [x,y] = pupilplots(timeStampAll,rightEyeAll, leftEyeAll, StimOff, StimOnSet);
>>>>>>> cef2ed92073e5f44f83c217860baa3c9bd05a800
hold on
q=plot(timeStampAll_dark,leftEyeAll_dark(:,12));
set(q, 'Color', 'b')
for i=1:length(StimOff)
line([StimOff_dark(i) StimOff_dark(i)], yL, 'Color', 'r');
line([StimOnSet_dark(i) StimOnSet_dark(i)], yL, 'Color', 'g');
end
% for light
yL = [-1 4];
fig = figure('Name','Pupil During Light Test'); 
k=plot(timeStampAll_light,rightEyeAll_light(:,12));
set(k, 'Color', 'm')
hold on
q=plot(timeStampAll_light,leftEyeAll_light(:,12));
set(q, 'Color', 'b')
for i=1:length(StimOff)
line([StimOff_light(i) StimOff_light(i)], yL, 'Color', 'r');
line([StimOnSet_light(i) StimOnSet_light(i)], yL, 'Color', 'g');
end

%for reversal learning
yL = [-1 4];
fig = figure('Name','Pupil During Reversal Learning'); 
k=plot(timeStampAll_rl,rightEyeAll_rl(:,12));
set(k, 'Color', 'm')
hold on
q=plot(timeStampAll_rl,leftEyeAll_rl(:,12));
set(q, 'Color', 'b')
plwoe=[soundtime' sndplay'];
    %FINISH THIS, NEED TO PLOT POINTS OF SURPRISE


