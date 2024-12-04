[inner, outer] = im2cones('track1.png');
inner = inner / 0.1 * 1.0;
inner = bsxfun(@plus, inner, [w/2; h/2] - mean(inner, 2));
outer = outer / 0.1 * 1.0;
outer = bsxfun(@plus, outer, [w/2; h/2] - mean(outer, 2));

I = inner; O = outer;

w = 256; h = 256; [X, Y] = meshgrid(1:w, 1:h); XX = [X(:) Y(:)]';

Niter = max(size(I, 2), size(O, 2));
figure(1); figure(5);
for iter = 41:max(size(I, 2), size(O, 2))
    
    inner = I(:, 1:round(size(I, 2) * iter / Niter));
    outer = O(:, 1:round(size(O, 2) * iter / Niter));
    
    edgesi = fit_polyline(inner, 'method', 'tsp');
    edgeso = fit_polyline(outer, 'method', 'tsp');
    
    polyi = [];
    for i = 1:size(edgesi, 1)
        polyi = [polyi [inner(1, edgesi(i, 1)); inner(2, edgesi(i, 1)); inner(1, edgesi(i, 2)); inner(2, edgesi(i, 2))]];
    end
    polyo = [];
    for i = 1:size(edgeso, 1)
        polyo = [polyo [outer(1, edgeso(i, 1)); outer(2, edgeso(i, 1)); outer(1, edgeso(i, 2)); outer(2, edgeso(i, 2))]];
    end
    
    Pinner = polydist(polyi, XX); Pinner = reshape(Pinner(1, :), h, w);
    Pouter = polydist(polyo, XX); Pouter = reshape(Pouter(1, :), h, w);
    
    C = abs(Pouter) > abs(Pinner);
    [B, L, N, A] = bwboundaries(C);
    if N > 1
        error('More than one component!');
    end
    center = B{1}';
    center = fliplr(flipud(center)); % ??
    center = center(:, 1:5:end);
    
    edgesc = fit_polyline(center, 'method', 'tsp');
    polyc = [];
    for i = 1:size(edgesc, 1)
        polyc = [polyc [center(1, edgesc(i, 1)); center(2, edgesc(i, 1)); center(1, edgesc(i, 2)); center(2, edgesc(i, 2))]];
    end
    Pcenter = polydist(polyc, XX); Pcenter = reshape(Pcenter(1, :), h, w);
    
    
    IDX = zeros(1, size(XX, 2));
    P = inf(1, size(XX, 2));
    for i = 1:size(polyc, 2)
        p = psdist(polyc(1:2, i), polyc(3:4, i), XX);
        closer = p < P;
        IDX(closer) = i;
        P = min(P, p);
    end
    
    traced = 30;
    last = zeros(1, size(edgesc, 1)); % Index of an edge where we end up after tracing for TRACED
    for i = 1:size(edgesc, 1)
        d = 0;
        e = i;
        while d <= traced
            len = vnorm(polyc(1:2, e) - polyc(3:4, e));
            d = d + len;
            e = edgesc(e, 2);
        end
        last(i) = e;
    end
    
    adv = polyc(1:2, last(IDX)) - XX;
    % return
    
    set(0, 'CurrentFigure', 1);
    % sc(F, [0 8], hot);
    sc(abs(Pinner - Pouter), inferno);
    hold on
    plot(inner(1, :), inner(2, :), 'go');
    plot(outer(1, :), outer(2, :), 'bo');
    plot_poly(edgesi, inner, 'g');
    plot_poly(edgeso, outer, 'b');
    plot_poly(edgesc, center, 'r');
    axis xy
    hold off
    
    export_fig(sprintf('potential%05d.png', iter));
    % filter = fspecial('gaussian', 25, 15);
    % DP = Pinner - Pouter;
    % DP = imfilter(DP, filter, 'replicate');
    % [gx, gy] = gradient(Pcenter);
    
    % [gxa, gya] = gradient((DP));
            set(0, 'CurrentFigure', 5);
%     figure(5);
    % fx = 0.5 * -gxa - gy;
    % fy = 0.5 * -gya + gx;
    % fx = -gxa;
    % fy = -gya;
    fx = reshape(adv(1, :), h, w);
    fy = reshape(adv(2, :), h, w);
    norm = sqrt(fx .^ 2 + fy .^ 2);
    fx = fx ./ norm;
    fy = fy ./ norm;
    %     quiver(0.5 * -gxa(1:4:end, 1:4:end) - gy(1:4:end, 1:4:end), 0.5 * -gya(1:4:end, 1:4:end) + gx(1:4:end, 1:4:end));
    quiver(X(1:8:end, 1:8:end), Y(1:8:end, 1:8:end), fx(1:8:end, 1:8:end), fy(1:8:end, 1:8:end), 0.5);
    axis tight
    hold on
    plot(inner(1, :), inner(2, :), 'go');
    plot(outer(1, :), outer(2, :), 'bo');
    
    plot_poly(edgesi, inner, 'g');
    plot_poly(edgeso, outer, 'b');
    plot_poly(edgesc, center, 'r');
    hold off
    export_fig(sprintf('direction%05d.png', iter));
end



