# Adapted from https://learning-0mq-with-pyzmq.readthedocs.io/en/latest/pyzmq/patterns/client_server.html

import zmq
import sys

context = zmq.Context()
print("Connecting to servers...")
socket = context.socket(zmq.REQ)

# Connection order seems to determine which port/server socket.send() goes to first, but not confirmed 
socket.connect("tcp://localhost:5556")
socket.connect("tcp://localhost:5555")

while True:
    """
    Alternate format commented out to make sure desired order of '5555 first, then 5556'
    but requires constant connection/disconnection (need to look more into networking concepts/zmq)
    """

    # socket.connect("tcp://localhost:5555")
    socket.send(b"Hello1")
    msg1 = socket.recv()
    print("Received reply: ", msg1)
    # socket.disconnect("tcp://localhost:5555")

    # socket.connect("tcp://localhost:5556")
    socket.send(b"Hello2")
    msg2 = socket.recv()
    print("Received reply: ", msg2)
    # socket.disconnect("tcp://localhost:5556")

