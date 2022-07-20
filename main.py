"""
From https://python-osc.readthedocs.io/en/latest/server.html#concurrent-mode
"""
from collections import defaultdict

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
ip = "10.10.10.11"  # FIXME command line arg
port = 7001

X, Y, Z = 0, 1, 2

input_state = defaultdict(lambda: np.zeros(3))


def transform(state):
    left_hand_from_torso = state['Left Hand'] - state['Torso']
    right_hand_from_torso = state['Right Hand'] - state['Torso']
    
    new_state = {
        # Julia parameters
        #'cur1X': left_hand_from_torso[X] / 600.0,
        #'cur1Y': left_hand_from_torso[Y] / 600.0,
        
        # Panning
        #'cur2X': right_hand_from_torso[X] / 600.0,
        #1'cur2Y': right_hand_from_torso[Y] / 600.0,
        
        # Other Mandalive params
        
        # [0.3, 0.7] -> [0.02, 0.12]
        # -0.3 [0, 0.5]
        # *2 [0, 1]
        
        'p/Zoom': (state['Torso'][Z] / 3000.0 - 0.3) * 2 * 0.1 + 0.02,
    }
    
    #print(new_state['p/Zoom'])
    
    return new_state


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
