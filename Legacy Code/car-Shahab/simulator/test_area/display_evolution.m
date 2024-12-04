f = fopen('state/progress.txt', 'r');
pop = {};
i = 1;
while ~feof(f)
    line = fgets(f);
    p = textscan(line, '%f', 'delimiter', ',');
    pop{p{1}(1) + 1} = p{1};
    i = i + 1;
end
fclose(f);

figure(1); clf;
hold on
avg = [];
for i = 1:numel(pop)
    gen = pop{i}(1);
    fit = pop{i}(2:end);
    avg(gen + 1) = mean(fit);
    plot(repmat(gen, 1, numel(fit)), fit, 'b.', 'MarkerSize', 1);
    plot(gen, max(fit), 'b+');
end
x = 0:numel(avg)-1;
plot(x, avg, 'r', 'LineWidth', 2);
% p = polyfit(x, avg, 1);
% val = polyval(p, x);
% plot(x, val, 'k:', 'LineWidth', 2);
hold off
grid minor
tightfig;