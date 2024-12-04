fn = list_files('/storage/large/slam/*.png');

for i = 1:numel(fn)
    i
im = imread(fn{i});

if 0
im(:, 1:80, :) = 0;
im(1:200, :, :) = 0;
im(64:end, 1:128, :) = 0;
im(295:end, 1:370, :) = 0;
im(400:end, 1:500, :) = 0;
end


%im(664:end, 1:1110, :) = 0;
im(900:end, 300:1400, :) = 0;
im(500:end, 600:1300, :) = 0;
im(700:900, 400:1350, :) = 0;
idx = find(im == 0);
im(im == 0) = randi(256, [numel(idx) 1]) - 1;
%figure(1); sc(im);
imwrite(im, fn{i});

end
