#!env python3

import cv2









bgr = cv2.imread('../../car_data/cones/amz/every10/000345.png')
image = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
image = np.ascontiguousarray(np.transpose(image[:, :, :, None], (3, 2, 0, 1)))


X_cpu = image.astype(np.float32)

net = CNN('net.mat')

res = net.predict(X_cpu)
print('\n')
start_bench()
for i in range(100):
    res = net.predict(X_cpu)

end_bench('CNN')
# print('Res before')
# print(res.shape)
# print(res.flags)


result = {'res': res}
sio.savemat('out.mat', result)


# # Clean up
libcudnn.cudnnDestroy(cudnn_context)
