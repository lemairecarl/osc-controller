"""
From https://python-osc.readthedocs.io/en/latest/server.html#concurrent-mode
"""

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
    
def on_receive_input(address, *args):
    key = address[1:]
    input_state[key] = args[0]

# Send to this address
client = udp_client.SimpleUDPClient("192.168.1.94", 54321)

dispatcher = Dispatcher()
dispatcher.map("/ping", on_receive_ping, needs_reply_address=True)
dispatcher.map("/pong", on_receive_pong, needs_reply_address=True)
dispatcher.map("/i", on_receive_input)

# For receiving
ip = "192.168.1.103"
port = 7000

input_state = {'test': 0}


def transform(state):
    # TODO transform state by creating new keys here
    # Just a dummy transformation for now
    return {"out_" + k: v for k, v in state.items()}


def send_all(state):
    for k, v in state.items():
        client.send_message('/' + k, v)


async def loop():
    while True:
        out_state = transform(input_state)
        print(out_state)
        send_all(out_state)
        await asyncio.sleep(1)


async def init_main():
    server = AsyncIOOSCUDPServer((ip, port), dispatcher, asyncio.get_event_loop())
    transport, protocol = await server.create_serve_endpoint()  # Create datagram endpoint and start serving

    await loop()  # Enter main loop of program

    transport.close()  # Clean up serve endpoint


asyncio.run(init_main())
