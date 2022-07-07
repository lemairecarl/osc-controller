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

# Send to this address
client = udp_client.SimpleUDPClient("192.168.1.94", 54321)

dispatcher = Dispatcher()
dispatcher.map("/ping", on_receive_ping, needs_reply_address=True)
dispatcher.map("/pong", on_receive_pong, needs_reply_address=True)

# For receiving
ip = "192.168.1.103"
port = 7000


async def loop():
    """Example main loop that only runs for 10 iterations before finishing"""
    for i in range(10):
        print(f"{i}: sending ping")
        client.send_message("/ping", 0)
        await asyncio.sleep(1)


async def init_main():
    server = AsyncIOOSCUDPServer((ip, port), dispatcher, asyncio.get_event_loop())
    transport, protocol = await server.create_serve_endpoint()  # Create datagram endpoint and start serving

    await loop()  # Enter main loop of program

    transport.close()  # Clean up serve endpoint


asyncio.run(init_main())
