import asyncio
from camera import Camera
from socket import *

def spinImage(cam, lo, sock):
    errorVal = cam.process()
    print(errorVal)
    sock.sendall(str(errorVal).encode("UTF-8"))
    lo.call_later(0.1, spinImage, cam, lo, sock)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()

    # Create objects
    camera = Camera(1650, 1080)
    
    # Create socket
    datagram = socket(AF_INET, SOCK_DGRAM)
    datagram.connect(("192.168.43.113", 10000))

    try:
        # Schedule calls
        loop.call_soon(spinImage, camera, loop, datagram)
        loop.run_forever()
    except KeyboardInterrupt as err:
        # Blocking call interrupted by loop.stop()
        print("Canceling Event Loop...")
        #camera.freeResources()

    finally:
        loop.close()