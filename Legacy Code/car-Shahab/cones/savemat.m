function [] = savemat(m, f)
[r, c]= size(m);
file = fopen(f,'w');
if isinteger(m)
    for i=1:r
        for j=1:c-1
            fprintf(file, '%d ', m(i, j));
        end
        fprintf(file, '%d\n', m(i, c));
    end
else
    for i=1:r
        for j=1:c-1
            fprintf(file, '%f ', m(i, j));
        end
        fprintf(file, '%f\n', m(i, c));
    end
end
fclose(file);