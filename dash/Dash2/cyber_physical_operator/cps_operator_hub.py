"""
Central communication hub between the DASH CPS operator agent and the MiniCPS SWaT testbed using pyzmq (see link below for
additional information).

pyzmq - Adapted from https://zeromq.org/languages/python/, binds REQ socket to tcp://*:5555
"""


import time
import zmq


def main():
    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    socket.connect("tcp://localhost:5555")
    socket.connect("tcp://localhost:5556")

    print("Starting CPS operator hub...")

    minicps_json = {
        "recipient": "minicps"
    }

    while True:
        socket.send_json(obj=minicps_json)
        received_minicps = socket.recv_json()
        print(received_minicps)

        dash_json = {
            "recipient": "dash_agent",
            "tank_level": received_minicps["tank_level"],
            "alerts": received_minicps["alerts"]
        }

        socket.send_json(obj=dash_json)
        received_dash = socket.recv_json()
        print(received_dash)



if __name__ == "__main__":
    main()
