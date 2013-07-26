
function [npre,npost,nnorm,outdat,outdat2] = evtsplit(evt,pretime,posttime,sr,task,normtime,datamat,whicheye,twoeye,starttime)

%splits the time series data in data with sampling rate sr into a matrix of
%snippets with one row for each event timestamp in evt; pretime and
%posttime are the times prior to and following evt to grab; time is a list
%of times for each bin relative to the entries in evt
%starttime is the timestamp of the first bin in data



%define frequency if it isn't supplied
if ~exist('sr','var')
    sr = 1;
end

if ~exist('starttime','var')
    starttime = 0;
end


numevt=numel(evt); %number of event timestamps
dt = 1/sr; %time bin size
npre = ceil(pretime*sr); %number of bins to grab before
npost = ceil(posttime*sr); %number of bins to grab after
nnorm = ceil(normtime*sr); %number of bins to normalize over

% evtrel = evt - starttime;
if exist('twoeye') % If we want two eyes
    outdat2= nan(numevt,npre+npost+1); 
end

outdat = nan(numevt,npre+npost+1); %npre+npost+0 bin
for ind = 1:numevt
    bins_to_grab = (-npre:npost) + evt(ind);

%now take care of ends of time series
if bins_to_grab(1) < 1  %if we're at the start of series...
    bins_to_grab = bins_to_grab(bins_to_grab >= 1); %truncate
    outdat(ind,(end-length(bins_to_grab)+1):end) = datamat(bins_to_grab,whicheye);
if exist('twoeye') % If we want two eyes
    outdat2(ind,(end-length(bins_to_grab)+1):end) = datamat(bins_to_grab,whicheye+1);
end

elseif bins_to_grab(end) > length(datamat) %if we're at the end...
    bins_to_grab = bins_to_grab(bins_to_grab <= length(data)); %truncate
    outdat(ind,1:length(bins_to_grab)) = datamat(bins_to_grab,whicheye);
if exist('twoeye') % If we want two eyes
    outdat2(ind,1:length(bins_to_grab)) = datamat(bins_to_grab,whicheye+1);
end
else
    outdat(ind,1:length(bins_to_grab)) = datamat(bins_to_grab,whicheye);
    if exist('twoeye')
    outdat2(ind,1:length(bins_to_grab)) = datamat(bins_to_grab,whicheye+1);
    end
end


end

outdat = outdat';

for ind = 1:length(evt)
outdat(:,ind) = outdat(:,ind)-(nanmean(datamat((evt(ind)-nnorm):evt(ind),whicheye)));
end


time = (-npre:npost)*dt;

