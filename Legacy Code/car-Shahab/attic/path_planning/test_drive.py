import socketio
import eventlet
import eventlet.wsgi
import json
from flask import Flask

sio = socketio.Server()
app = Flask(__name__)

MAX_SPEED = 25
MIN_SPEED = 10

speed_limit = MAX_SPEED

@sio.on('connect')
def connect(sid, environ):
    print('connect ', sid)

@sio.on('disconnect')
def disconnect(sid):
    print('disconnect ', sid)

### THIS IS THE MAIN FUNCTION ###
@sio.on('telemetry')
def telemetry(sid, data):
    if data:
        steering_angle = float(data['steering_angle'])
        throttle = float(data['throttle'])
        speed = float(data['speed'])
        car_world_position = float(data['car_world_position'])
        #poisiton = float(data['position'])
        print(data.keys())
        try:
            global speed_limit
            if speed > speed_limit:
                speed_limit = MIN_SPEED  # slow down
            else:
                speed_limit = MAX_SPEED
            throttle = 1.0 - steering_angle**2 - (speed/speed_limit)**2

            print('{} {} {} {}'.format(steering_angle, throttle, speed, car_world_position))
            send_control(steering_angle, throttle)
        except Exception as e:
            print(e)
    else:
        sio.emit('manual', data={}, skip_sid=True)

def send_control(steering_angle, throttle):
    sio.emit(
        "steer",
        data={
            'steering_angle': steering_angle.__str__(),
            'throttle': throttle.__str__()
        },
        skip_sid=True)

if __name__ == '__main__':
    print("Starting test drive")
    app = socketio.Middleware(sio, app)

    port = 4567
    print("listening on port "+str(port))
    # deploy as an eventlet WSGI server
    eventlet.wsgi.server(eventlet.listen(('', port)), app)
