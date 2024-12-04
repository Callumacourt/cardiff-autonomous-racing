#!env python3
import airsim
from simulator import Simulator

@profile
def main():
    sim = Simulator()
    requests = [airsim.ImageRequest("0", airsim.ImageType.Scene, False, False),
                airsim.ImageRequest("1", airsim.ImageType.Scene, False, False)]

    for i in range(100):
        responses = sim.client.simGetImages(requests)

if __name__ == "__main__":
    main()
