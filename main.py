import asyncio
import threading

from networktables import NetworkTables
from vision import Vision

def connect(ip: str):
    cond = threading.Condition()
    notified = [False]

    def connectionListener(connected, info):
        print(info, '; Connected=%s' % connected)
        with cond:
            notified[0] = True
            cond.notify()

    NetworkTables.initialize(server=ip)
    NetworkTables.addConnectionListener(connectionListener, immediateNotify=True)

    with cond:
        print("Waiting for RoboRIO...")
        if not notified[0]:
            cond.wait()

async def toggle_vision(terminated: threading.Event, network, camera: Vision):
    while not terminated.is_set():
        if not network.getBoolean("is_enabled", False) and camera.is_enabled():
            camera.disable_vision()
        else:
            camera.enable_vision()
        
        await asyncio.sleep(0.05)

async def update_data(terminated: threading.Event, network, camera: Vision):
    """Take data off queue and put onto NetworkTables."""
    while not terminated.is_set():
        if camera.is_enabled() and camera.has_data():
            network.putNumber("pid_value", camera.get_data())
        
        await asyncio.sleep(0.05)

if __name__ == "__main__":
    WIDTH = 1920
    HEIGHT = 1080

    loop = asyncio.get_event_loop()
    terminator = threading.Event()

    # Create objects
    camera = Vision(terminator, 0, WIDTH, HEIGHT)

    # Connect to RoboRIO (Blocking Call)
    connect("10.3.69.2")
    print("Successfully connected to RoboRIO.")
    
    # Start camera thread
    camera.start()

    # Enable camera.
    table = NetworkTables.getTable("SmartDashboard").getSubTable("vision")
    table.putNumber("camera_width", WIDTH)
    table.putNumber("camera_height", HEIGHT)
    camera.enable_vision()

    try:
        # Schedule calls
        #loop.run_until_complete(toggle_vision(terminator, table, camera))
        loop.run_until_complete(update_data(terminator, table, camera))
        loop.run_forever()
    except KeyboardInterrupt as err:
        # Blocking call interrupted by loop.stop()
        print("Canceling Event Loop...")
        terminator.set()

    finally:
        loop.close()