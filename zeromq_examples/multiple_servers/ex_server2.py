# Adapted from https://learning-0mq-with-pyzmq.readthedocs.io/en/latest/pyzmq/patterns/client_server.html 

import zmq
import time
import sys

context = zmq.Context()
socket = context.socket(zmq.REP)
socket.bind("tcp://*:5556")

while True:
    msg = socket.recv()
    print("Received request: ", msg)
    time.sleep(1)
    socket.send(b"Hello from 5556")