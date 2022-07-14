"""
From https://python-osc.readthedocs.io/en/latest/server.html#concurrent-mode
"""
import numpy as np
from pythonosc.osc_server import AsyncIOOSCUDPServer
from pythonosc.dispatcher import Dispatcher
from pythonosc import udp_client
import asyncio


def on_receive_ping(ip_address_and_port, address, *args):
    print(f"received ping")
    
    # Configure a temporary client to send the pong
    ip_address, port = ip_address_and_port
    client = udp_client.SimpleUDPClient(ip_address, port)
    client.send_message("/pong", 7000)
    
def on_receive_pong(ip_address, address, *args):
    print(f"received pong")
    
def on_receive_position(address, *args):
    key = address[len("/position/"):]
    input_state[key] = np.array(args)  # args is 3 floats

# Send to this address
#client = udp_client.SimpleUDPClient("192.168.1.94", 54321)
client = udp_client.SimpleUDPClient("127.0.0.1", 7000)

dispatcher = Dispatcher()
dispatcher.map("/ping", on_receive_ping, needs_reply_address=True)
dispatcher.map("/pong", on_receive_pong, needs_reply_address=True)
dispatcher.map("/position/*", on_receive_position)

# For receiving
ip = "192.168.1.102"
port = 7001

input_state = {}


def transform(state):
    return {
        'cur1X': state.get('Left Hand', np.zeros(3))[0] / 600.0,
        'cur1Y': state.get('Left Hand', np.zeros(3))[1] / 600.0,
        'cur2X': state.get('Right Hand', np.zeros(3))[0] / 600.0,
        'cur2Y': state.get('Right Hand', np.zeros(3))[1] / 600.0,
        'p/Zoom': state.get('Torso', np.zeros(3))[2] / 6000.0,
    }


def send_all(state):
    for k, v in state.items():
        client.send_message('/' + k, v)


async def loop():
    t = float(0)
    while True:
        out_state = transform(input_state)
        #print(out_state)
        send_all(out_state)
        #client.send_message("/cur1X", 0.33 + 0.03 * np.sin(0.5 * t))
        #client.send_message("/cur1Y", 0.33 + 0.03 * np.sin(0.4 * t))
        #t += 0.01
        await asyncio.sleep(0.01)


async def init_main():
    server = AsyncIOOSCUDPServer((ip, port), dispatcher, asyncio.get_event_loop())
    transport, protocol = await server.create_serve_endpoint()  # Create datagram endpoint and start serving

    await loop()  # Enter main loop of program

    transport.close()  # Clean up serve endpoint


asyncio.run(init_main())
