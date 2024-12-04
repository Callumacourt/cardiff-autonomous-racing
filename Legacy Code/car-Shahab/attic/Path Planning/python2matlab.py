import matlab.engine
import json
eng = matlab.engine.start_matlab()
names = matlab.engine.find_matlab()

print(eng, names)

G = eng.gcd(100, 80, nargout=3)
print(G)
eng.hybrid_astar()
data = eng.getData(nargout=1)
data = json.loads(data)
print(data)

def fcall(s):
    print(s)
    return 'hello'