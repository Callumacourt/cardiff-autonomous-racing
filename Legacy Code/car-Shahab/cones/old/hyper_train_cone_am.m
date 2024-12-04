% energy = 0.90:0.01:0.99;
% 
% am = cell(1, numel(energy));
% conf = cell(1, numel(energy));
% 
% for i = 1:numel(energy)
%     [am{i}, conf{i}] = train_cone_am('energy', energy(i));
% end

% ch = 10:2:32;
% 
% am = cell(1, numel(ch));
% conf = cell(1, numel(ch));
% 
% for i = 1:numel(ch)
%     [am{i}, conf{i}] = train_cone_am('energy', 0.95, 'ch', ch(i));
% end

fn = cellfun(@(x) x(2, 1), conf);
fp = cellfun(@(x) x(1, 2), conf);

fig(1); clf;

plot(ch, fp);
hold on
plot(ch, fn);
plot(ch, fp + fn);
hold off
legend('FP', 'FN', 'ALL');
