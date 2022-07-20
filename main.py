"""
From https://python-osc.readthedocs.io/en/latest/server.html#concurrent-mode
"""
from collections import defaultdict

import numpy as np
from pythonosc.osc_server import AsyncIOOSCUDPServer
from pythonosc.dispatcher import Dispatcher
from pythonosc import udp_client
import asyncio


# NETWORK CONFIG
LOCAL_IP_AND_PORT = ("10.10.10.11", 7001)  # AEmulator sends to this address. FIXME set using command line arg
MANDALIVE_IP_AND_PORT = ("127.0.0.1", 7000)


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
client = udp_client.SimpleUDPClient(*MANDALIVE_IP_AND_PORT)


dispatcher = Dispatcher()
dispatcher.map("/ping", on_receive_ping, needs_reply_address=True)
dispatcher.map("/pong", on_receive_pong, needs_reply_address=True)
dispatcher.map("/position/*", on_receive_position)

X, Y, Z = 0, 1, 2

input_state = defaultdict(lambda: np.zeros(3))


def normalize(v, vmin, vmax):
    # vmin -> 0
    # vmax -> 1
    return (v - vmin) / (vmax - vmin)


def map_range(v, out_min, out_max):
    # 0 -> out_min
    # 1 -> out_max
    return v * (out_max - out_min) + out_min


def transform(state):
    # Compute normalized vectors
    # I have determined empirically that [-500, 500] is a good range for coords of the vector going from torso to left
    #   hand. Thus, the [-500, 500] will be normalized to [0, 1]
    left_hand_from_torso = normalize(state['Left Hand'] - state['Torso'], -500, 500)
    right_hand_from_torso = normalize(state['Right Hand'] - state['Torso'], -500, 500)
    torso = normalize(state['Torso'][Z], 1000, 2000)
    
    new_state = {
        # Julia parameters
        # I have determined empirically that [0.4, 0.6] is a good range for the cur1X parameter.
        'cur1X': map_range(left_hand_from_torso[X], 0.4, 0.6),
        'cur1Y': map_range(left_hand_from_torso[Y], 0.3, 0.4),
        
        # Panning
        'cur2X': right_hand_from_torso[X],
        'cur2Y': right_hand_from_torso[Y],
        
        # Other Mandalive params
        'p/Hue': torso,
    }
    
    return new_state


def send_all(state):
    for k, v in state.items():
        client.send_message('/' + k, v)


async def loop():
    while True:
        out_state = transform(input_state)
        send_all(out_state)
        await asyncio.sleep(0.01)


async def init_main():
    server = AsyncIOOSCUDPServer(LOCAL_IP_AND_PORT, dispatcher, asyncio.get_event_loop())
    transport, protocol = await server.create_serve_endpoint()  # Create datagram endpoint and start serving

    await loop()  # Enter main loop of program

    transport.close()  # Clean up serve endpoint


asyncio.run(init_main())
