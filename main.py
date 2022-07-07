"""
From https://python-osc.readthedocs.io/en/latest/server.html#concurrent-mode
"""

from pythonosc.osc_server import AsyncIOOSCUDPServer
from pythonosc.dispatcher import Dispatcher
from pythonosc import udp_client
import asyncio


def pong(address, *args):
    print(f"received {address}: {args}")

# Send to this address
client = udp_client.SimpleUDPClient("127.0.0.1", 1337)

dispatcher = Dispatcher()
dispatcher.map("/ping", pong)

# For receiving
ip = "127.0.0.1"
port = 1337


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
