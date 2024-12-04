function imp = inpaint(im, mask, varargin)

opt.eps = 0.001;
opt.dilate = false;
opt = parseargs(opt, varargin{:});
imp = im;
[h w d] = size(im);

% colour = [0; 0; 0];
% mask = (abs(im(:, :, 1) - colour(1)) < opt.eps) ...
%     & (abs(im(:, :, 2) - colour(2)) < opt.eps) ...
%     & (abs(im(:, :, 3) - colour(3)) < opt.eps);
% if opt.dilate
%     se = strel('disk', 4, 4);
%     mask = imdilate(mask, se);
% end
mask(1, :) = false;
mask(h, :) = false;
mask(:, 1) = false;
mask(:, w) = false;
id_missing = find(mask);
mp = zeros(w*h, 1);
mp(id_missing) = 1:numel(id_missing);

N = numel(id_missing);
%A = sparse([], [], [], N, N, 5);
b = zeros(N, 1);

%ID = reshape((1:w*h)', h, w);
I = zeros(5 * N, 1);
J = zeros(5 * N, 1);
S = zeros(5 * N, 1);
count = 0;
for y = 2:h-1
    for x = 2:w-1
        if mask(y, x)
            id = sub2ind([h w], y, x);
            n = mp(id);
            bb = 0;
            if mask(y-1, x)
                count = count + 1;
                I(count) = n; J(count) = mp(id - 1); S(count) = 1;
                %A(n, mp(id - 1)) = 1;
            else
                bb = bb - squeeze(im(y-1, x));
            end
            
            if mask(y, x-1)
                count = count + 1;
                I(count) = n; J(count) = mp(id - h); S(count) = 1;
                %                A(n, mp(id - h)) = 1;
            else
                bb = bb - squeeze(im(y, x-1));
            end
            count = count + 1;
            I(count) = n; J(count) = mp(id); S(count) = -4;
            %A(n, mp(id)) = -4;
            
            if mask(y, x+1)
                count = count + 1;
                I(count) = n; J(count) = mp(id + h); S(count) = 1;
                % A(n, mp(id + h)) = 1;
            else
                bb = bb - squeeze(im(y, x+1));
            end
            
            if mask(y+1, x)
                count = count + 1;
                I(count) = n; J(count) = mp(id + 1); S(count) = 1;
                % A(n, mp(id + 1)) = 1;
            else
                bb = bb - squeeze(im(y+1, x));
            end
            
            i = mp(id);
            b(i) = bb';
            %n = n + 1;
        end
    end
end
A = sparse(I(1:count), J(1:count), S(1:count), N, N, 5*N);
X = A\b;
%X = linsolve(A, b);

% X(X > 1) = 1;
% X(X < 0) = 0;
for i = 1:N
    [y, x] = ind2sub([h w], id_missing(i));
    imp(y, x) = X(i, :);
end
