
num = [1]
denom = [1 3 1]
Gp = tf(num, denom)
H = [1]
M = feedback(Gp, H)
step(M)
hold on

Kp = 27
Ki = 0
Kd = 0

Gc = pid(Kp, Ki, Kd)

Mc = feedback(Gc*Gp, H)
step(Mc)
grid on