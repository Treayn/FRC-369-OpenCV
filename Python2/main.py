import socket
import trollius
from camera import Camera

def spinImage(cam, lo, soc):
    errorVal = cam.process()
    print errorVal
    soc.sendall(str(errorVal).encode('UTF-8'))
    lo.call_later(0.01, spinImage, cam, lo, soc)

if __name__ == "__main__":
    loop = trollius.get_event_loop()
    
    # Create objects
    camera = Camera(1080, 720)
    
    # Create a UDP socket
    datagram = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    datagram.connect(('roborio-369-frc.local', 10000))
    
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