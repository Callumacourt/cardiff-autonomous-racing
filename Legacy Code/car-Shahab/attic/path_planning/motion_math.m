x = 1
y = 1 
len = 20.0  
theta = 1
bearing_noise = 0.0
steering_noise = 0.0
distance_noise = 0.0

car = vehicle(len, 0.0, 0.0, 0.0)
car.set_noise(bearing_noise, steering_noise, distance_noise)
%[steering angle, distance]
motions = [[0.0, 10.0], [pi / 6.0, 10.0], [0.0, 20.0]]

for t = 1:2:length(motions)
    car.move(motions(t:t+1))
end

   

