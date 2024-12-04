function d = psdist(v, w, p)

vw = v - w;
l2 = vw(1)^2 + vw(2)^2;
if l2 == 0.0
    vp = v - p;
    d = sqrt(vp(1, :).^2 + vp(2, :).^2);
    return
end
%   // Consider the line extending the segment, parameterized as v + t (w - v).
%   // We find projection of point p onto the line.
%   // It falls where t = [(p-v) . (w-v)] / |w-v|^2
%   // We clamp t from [0,1] to handle points outside the segment vw.
t = max(0, min(1, dot(p - v, repmat(w - v, 1, size(p, 2))) / l2));
proj = bsxfun(@plus, bsxfun(@times, (w - v), t), v);
pproj = p - proj;
% vp = v - p;
% c = bsxfun(@cross, [vp; zeros(1, size(vp, 2))], [vw; 0]);
% c = cross([vp; zeros(1, size(vp, 2))], repmat([vw; 0], 1, size(vp, 2)));
% d = sign(c(3, :)) .* (sqrt(pproj(1, :).^2 + pproj(2, :).^2));
d = sqrt(pproj(1, :).^2 + pproj(2, :).^2);