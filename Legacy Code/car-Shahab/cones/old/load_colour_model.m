function c = load_colour_model(fn)

f = fopen(fn, 'r');
c = textscan(f, '%f %f %f');
c = [c{1} c{2} c{3}]';
fclose(f);