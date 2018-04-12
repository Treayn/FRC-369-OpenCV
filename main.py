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

async def toggle_vision(network, camera: Vision):
        if not network.getBoolean("vision_enabled", False) and camera.is_enabled():
            camera.disable_vision()
        else:
            camera.enable_vision()
        
        await asyncio.sleep(0.02)

async def update_data(network, camera: Vision):
    """Take data off queue and put onto NetworkTables."""
    while True:
        if camera.is_enabled():
            network.putNumber("vision_pid", camera.get_data())
        
        await asyncio.sleep(0.02)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()

    # Create objects
    camera = Vision(0, 1650, 1080)

    # Connect to RoboRIO (Blocking Call)
    connect("10.3.69.2")
    print("Successfully connected to RoboRIO.")
    
    # Start camera thread
    camera.start()

    # Enable camera.
    table = NetworkTables.getTable("SmartDashboard").getSubTable("vision")
    camera.enable_vision()

    try:
        # Schedule calls
        loop.run_until_complete(toggle_vision(table, camera))
        loop,run_until_complete(update_data(table, camera))
        loop.run_forever()
    except KeyboardInterrupt as err:
        # Blocking call interrupted by loop.stop()
        print("Canceling Event Loop...")

    finally:
        loop.close()