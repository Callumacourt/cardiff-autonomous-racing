function fn = append_folder(fn, folder)

[p, n, e] = fileparts(fn);
fn = fullfile(p, folder, [n e]);
