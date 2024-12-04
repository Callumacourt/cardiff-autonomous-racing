function [R_inv, T_inv] = invert_rt(R, T)

tf_inv = inv([R T; 0 0 1]);
R_inv = tf_inv(1:2, 1:2);
T_inv = tf_inv(1:2, 3);
