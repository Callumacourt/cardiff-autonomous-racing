function B = filter_bboxes_energy(im, bbox, RMS_MIN)

B = [];
for i = 1:size(bbox, 1)
    b = bbox(i, :);
    wnd = im(b(2):b(2)+b(4), b(1):b(1)+b(3));
    avg = mean(wnd(:));
    d = (wnd - avg) .^ 2;
    rms = sqrt(mean(d(:)));
    if rms > RMS_MIN
        B = [B; b];
    end
end
