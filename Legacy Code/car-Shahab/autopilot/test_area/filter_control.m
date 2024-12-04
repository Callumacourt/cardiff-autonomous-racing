function predicted_averages = filter_control(dFn, dt)
% dFn is the control sequence taken from the mppi program
% dt is the interval between the time points
control_size = size(dFn);
iter_dimension = control_size(1);
predicted_averages = zeros(4, iter_dimension);
spline_length = control_size(2)-1;
for i = 1:iter_dimension
    cc = spline(0:dt:dt*spline_length,dFn(i,:));
    spline_size = size(cc.coefs);
    for j = 1:spline_size(2)
        predicted_averages(j, i) = cc.coefs(1, j);
    end
end
predicted_averages = transpose(predicted_averages);
disp(predicted_averages)
end