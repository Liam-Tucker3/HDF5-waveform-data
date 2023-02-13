function activate()

% Copyright 2001-2019 Verasonics, Inc. Verasonics Registered U.S. Patent
% and Trademark Office.
%
% activate:  Utility to confirm user has set the Matlab working directory
% to a valid Vantage Product Folder (VPF), and if so set up environment
% variables and paths as needed by the vantage software, load SW libraries,
% and add VPF subfolders to the Matlab path.  After the current VPF has
% been successfully actived, any subsequent calls to this function will
% detect that and return without doing anything.

% updated April 22, 2019 VTS-1200 error and status reporting cleanup

    % VTS-902, 887: Check for supported version of Matlab.
    % Use of Matlab versions outside this range may result in an error
    % condition, a Matlab crash, or other system malfunctions
    if verLessThan('matlab', '9.2') % 9.2 is R2017a
        error('Minimum supported MATLAB version is R2017a')
    end

    % Root path may not be the current directory for a deployed application.
    if isdeployed
        vpfRoot = ctfroot;
    else
        vpfRoot = pwd;
    end

    % set "activateNeeded" to false, indicating this is a redundant call to
    % activate and we don't need to do anything.  If a condition is
    % discovered that implies this is the first call to activate for the
    % current Matlab session, this flag will be set to true.
    activateNeeded = false;
    vpfRootChanged = false;

    VS_S = getenv('VERASONICS_VPF_ROOT');
    if ~strcmp(VS_S, vpfRoot)
        % The current VPF does not match the 'VERASONICS_VPF_ROOT' environment
        % variable, so we need to do the full activate and set the variable.
        activateNeeded = true;
        vpfRootChanged = true;
    elseif ~exist('P_Files', 'dir')
        % The VERASONICS_VPF_ROOT environment variable doesn't need to be
        % modified, but we still need to do the other full activate steps
        % since the VPF subfolders have not yet been added to the path
        % (identified here by looking for "P_Files" subfolder of "System").
        activateNeeded = true;
    end

    if ~isdeployed && activateNeeded
        % complete the following steps only if full activation is
        % underway, and isdeployed is false

        % Check for existence of 'System' subfolder to determine if the
        % current matlab working directory is a valid VPF
        currLibsFolder = fullfile(vpfRoot, 'System');
        matlabLoaderFile = fullfile(currLibsFolder, 'matlab-verasonics-loader-0.1.0.jar');
        if ~exist(currLibsFolder, 'dir')
            fprintf(2, 'activate: Vantage software cannot be used because you have not set the Matlab\n');
            fprintf(2, ' working directory to the root level of a Vantage Software Product Folder.\n');
            error(' ');
        elseif ~exist(matlabLoaderFile, 'file')
            % Can't find the required library .jar file
            fprintf(2, 'activate: The Vantage libraries have not been found.  You must build them\n');
            fprintf(2, ' using the ''build'' utility (or equivalent), before running activate.\n')
            error(' ');
        end

        % Unload libary and clear all workspace variables.
        evalin('base', 'clear all');

        % Ensure initially-empty directories exists.
        make_dirs(vpfRoot, {'MatFiles'})

        % Clear all working directories from the MATLAB path, including
        % any that may have been added by the user independent of the
        % activate function, and then add the Verasonics software
        % directories to the path.
        restoredefaultpath
        addpath(generate_path());
        rehash;

        % -----------------------------------------------------------------
        % Perform actions related to Verasonics libraries.
        % -----------------------------------------------------------------
        javaaddpath(matlabLoaderFile);
        matlabLoader = com.verasonics.matlab.MatlabVerasonicsLoader();

        % Add the Verasonics' libraries to Matlab's path if not already done.
        if ~matlabLoader.isVerasonicsPathInitialized()
            matlabLoader.addVerasonicsToMatlabPath();
        end

        % Determine if Matlab has already loaded Verasonics libraries from a different activated folder.
        % If Matlab has loaded libraries from a different folder, Matlab needs to be restarted to
        %  prevent using the wrong libraries.
        if matlabLoader.isLibraryLoadedOutsideOfCurrentPath('libVerasonicsCommon', currLibsFolder)
            fprintf(2, 'activate: You must quit and restart Matlab before activating this directory.\n');
            error(' ');
        end

        % See if this is a software only system, where the device
        % driver is NOT installed.  We must determine that now so
        % when it is time to open the Hal we won't try (the old Hal
        % requires the driver, so attempting to open it without a
        % driver will trigger an error.  Knowing there is no driver
        % means we can avoid that, and happily report the
        % software-only configuration.)
        if ~matlabLoader.isWinDriverInstalled()
            matlabLoader.enableVantageSoftwareOnly();
        end
    end

    % Publish an environment variable that identifies the MATLAB root folder.
    %
    % The Verasonics Hal uses this environment variable to find and make a
    % reference to the mexPrintf() function. This is done to support the
    % output of debug information.
    %
    % This environment variable (like all such variables) does not persist
    % across MATLAB sessions.
    setenv('HOME_MATLAB', matlabroot);

    % While the VERASONICS_VPF_ROOT environment variable
    % usually exists, it doesn't always exist. We might be
    % running on Linux or Mac (where environment variables
    % are not persisted across process instances) or we might
    % be running activate for the first time for a given user.
    %
    % If the VERASONICS_VPF_ROOT environment variable is set
    % to a different directory, we need to de-activate that
    % directory before we attempt to activate the current
    % directory.
    %
    % We don't have to do anything special if VERASONICS_VPF_ROOT
    % is not set. The result will be a zero-length string if it
    % is unset.

    % If VERASONICS_VPF_ROOT is not set or is set to a
    % directory other than the current directory, then
    % we need to do the work to activate the current
    % directory. Otherwise, this work can be skipped.
    if vpfRootChanged
        if ~isempty(VS_S)
            disp(['Deactivating directory ' VS_S])
            set_vpf_root('');
        end

        % Publish an environment variable that identifies the
        % currently activated Vantage project folder.
        %
        % Other scripts can inspect this variable and, if it
        % exists, treat the value of the variable as a path
        % to the root of the last-activated Vantage project
        % folder.
        %
        % This environment variable (like all such variables)
        % does not persist across MATLAB sessions.
        set_vpf_root(vpfRoot);
    end

    if activateNeeded
        % Notify user we are activating the current working directory.
        disp(['Activating directory ', vpfRoot])
    end

end

function set_vpf_root(vpfRoot)
    if isempty(vpfRoot), vpfRoot = '""'; end
    setenv('VERASONICS_VPF_ROOT', vpfRoot)
    if isequal(computer, 'PCWIN64')
        system(sprintf('setx VERASONICS_VPF_ROOT "%s" > :NUL', vpfRoot));
    end
end

function path = generate_path()
    % Generate path, excluding all hidden directories.
    inpath = strsplit(genpath(cd()), pathsep);
    excluded_dir = {
        'Documentation', 'Hal', 'HwDiag', '.git', '.settings', ...
        'build', 'build-process', 'dev-apps', 'dev-deps', 'dev-libs', ...
        'installer'
    };
    sep = regexptranslate('escape', filesep);
    pattern = sprintf('%s(%s)(%s|$)', sep, strjoin(excluded_dir, '|'), sep);
    outpath = {};
    j = 0;
    for i = 1:length(inpath)
        if isempty(regexp(inpath{i}, pattern, 'once'))
            j = j + 1;
            outpath{j} = inpath{i}; %#ok<AGROW>
        end
    end
    path = strjoin(outpath, pathsep);
end

function make_dirs(vpfroot, dirnames)
    for i = 1:length(dirnames)
        dirpath = fullfile(vpfroot, dirnames{i});
        if ~exist(dirpath, 'dir')
            mkdir(dirpath)
        end
    end
end
