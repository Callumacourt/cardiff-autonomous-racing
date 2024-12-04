inf = '~/research/car_data/test_days/2019-12-11/recording0_calib/*.jpg';
outf = '~/research/car_data/test_days/2019-12-11/recording0_calib_flipped';

fn = list_files(inf);
for i = 1:numel(fn)
    [p, n, e] = fileparts(fn{i});
    outfn = fullfile(outf, [n e]);
    flip_stereo(fn{i}, outfn);
end
