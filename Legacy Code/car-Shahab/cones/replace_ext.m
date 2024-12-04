function fn = replace_ext(fn, ext)

if numel(ext) < 1, return; end
if ext(1) ~= '.', ext = ['.' ext]; end
[p, n, ~] = fileparts(fn);
fn = [fullfile(p, n) ext];
