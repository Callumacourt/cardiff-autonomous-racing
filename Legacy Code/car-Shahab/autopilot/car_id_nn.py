#!env python3
import os
import sys
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '1' 
import numpy as np
import tensorflow as tf
import tensorflow_docs as tfdocs
import tensorflow_docs.plots
import tensorflow_docs.modeling

# sess = tf.compat.v1.Session(config=tf.compat.v1.ConfigProto(log_device_placement=True))
# data_train = np.genfromtxt('id_training_int.csv', delimiter=',')
# data_test = np.genfromtxt('id_testing_int.csv', delimiter=',')
# np.savez('id_data', train=data_train, test=data_test)

id_data = np.load('id_data.npz')
data_train = id_data['train']
data_test = id_data['test']
print(data_train.shape)
print(data_test.shape)

avg = np.mean(data_train, axis=0)
data_train -= avg
sd = np.std(data_train, axis=0)
data_train /= sd

# x_train = data_train[0:-1, 1:]
# y_train = data_train[1:, [9, 10, 11, 15, 16, 17, 18]]


horizon = 10
idx_predict = [9, 10, 11, 15, 16, 17, 18]
x_train = np.zeros((data_train.shape[0] - horizon, data_train.shape[1] - 1))
y_train = np.zeros((data_train.shape[0] - horizon, 7 * horizon))
for i in range(x_train.shape[0]):
    x_train[i, :] = data_train[i, 1:]
    future = data_train[i + 1:i + 1 + horizon, idx_predict]
    y_train[i, :] = future.flatten()
    
print(x_train.shape)
print(y_train.shape)
# sys.exit(0)
model = tf.keras.Sequential()
model.add(tf.keras.layers.Dense(10,
                                input_shape=(x_train.shape[1],),
                                activation='relu'))
model.add(tf.keras.layers.Dense(10, activation='relu'))
model.add(tf.keras.layers.Dense(30, activation='relu'))
model.add(tf.keras.layers.Dense(y_train.shape[1]))

model.compile(loss='mse',
              optimizer=tf.keras.optimizers.RMSprop(0.001),
              metrics=['mae', 'mse'])

print(model.summary())

EPOCHS = 10000

history = model.fit(
    x_train, y_train,
    batch_size=16384,
    epochs=EPOCHS, validation_split=0.2, verbose=1,
    callbacks=[tfdocs.modeling.EpochDots(),
               tf.keras.callbacks.TensorBoard(log_dir='./logs')])
