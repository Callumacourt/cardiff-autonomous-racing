function [xbest, fbest, nfc] = optimise(fun, varargin)
%OPTIMISE    Global optimisation.
%   [XBEST, FBEST] = OPTIMISE(FUN, ...) performs a global optimisation of a
%   function FUN.  This is a wrapper for several 3rd party optimisation routines.
%   The remaining arguments to OPTIMISE are passed as a list of name-value pairs
%   detailed below.
%
%   'x0'
%     The initial guess to the solution.
%
%   'verbose'
%     Whether to print out additional information (true/false, default false).
%
%   'minx' and 'maxx'
%     The lower and the upper bounds on the argmin. This is relevant when
%     the optimisation method solves a bound constrained optimisation
%     problem, e.g. Multilevel Coordinate Search.
%
%   'method'
%     The optimisation method to be used. The following methods are
%     available:
%
%   'mcs'
%     Multilevel Coordinate Search. See the relevant documentation and
%     references by typing 'help mcs'.
%   
%   'fminsearch'
%     Built-in Nelder-Mead optimiser.
%
%   FOR INTERNAL USE ONLY! DO NOT DISTRIBUTE!
%
%   Copyright 2012 Kirill Sidorov
%   Email: k.sidorov@cs.cardiff.ac.uk
%
%   See also MCS, FMINSEARCH

opt.method = 'mcs';
opt.x0 = [];
opt.minx = [];
opt.maxx = [];
opt.maxeval = [];
opt.verbose = false;
opt.budget = [];
opt = parseargs(opt, varargin{:});


switch lower(opt.method)
    case 'mcs'
        if isempty(opt.minx) || isempty(opt.maxx)
            error('optimise:arguments', ...
                'MCS requires upper and lower bounds on the solution, MINX and MAXX.');
        end
        if ~isempty(opt.x0)
            warning('optimise:arguments', ...
                'MCS does not require an initial guess, x0 ignored.');
        end
        n = length(opt.minx);		% problem dimension
        smax = 5 * n + 10;  		% number of levels used
        nf = 50 * n^2;      		% limit on number of f-calls
        if ~isempty(opt.budget), nf = opt.budget; end
        stop(1) = 1;%3*n;          % = m, integer defining stopping test
        stop(2) = -inf;         % = freach, function value to reach
        
        [xbest, fbest, ~, ~, nfc, ~, flag] = mcs(@(data, x) fun(x), [], opt.minx, opt.maxx, ...
            opt.verbose, smax, nf, stop);
        if 2 == flag
            warning('optimise:results', 'Function evaluation budget exhausted.');
        end
        
    case 'fminsearch'
        if isempty(opt.x0)
            opt.x0 = 0.5*(opt.minx + opt.maxx);
        end
        n = length(opt.minx);
        nf = 50 * n^2;      		% limit on number of f-calls
        if ~isempty(opt.budget), nf = opt.budget; end
        display = 'off';
        if opt.verbose > 0
            display = 'iter';
        end
%         options = optimset('tolfun', 1e-1, 'tolx', 1e-3, 'display', display, 'MaxFunEvals', nf);
        options = optimset('Display', 'iter', 'MaxFunEvals', 100000, 'MaxIter', 100000, 'TolX', 1e-8, 'TolFun', 1e-8);

        [xbest, fbest, flags, out] = fminsearch(fun, opt.x0, options);
        nfc = out.iterations;
    otherwise
        error('Unknown optimisation method');
end
