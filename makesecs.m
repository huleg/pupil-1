    % Convert timestamps into function 
    function output = makesecs(datamat)
    datamat(:,3)=(double(datamat(:,3)))/1000000;
    end