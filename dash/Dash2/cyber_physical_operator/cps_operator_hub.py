"""
Central communication hub between the DASH CPS operator agent and the MiniCPS SWaT testbed using pyzmq (see link below for
additional information).

pyzmq - Adapted from https://zeromq.org/languages/python/, binds REP socket to tcp://*:5555
"""


import time
import zmq


def main():
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind("tcp://*:5555")

    print("Starting CPS operator hub...")
    while True:
        # Wait for next request from client
        json = socket.recv_json()
        response = {}

        if json["check_alerts"]:
            print("Action from operator: check_for_alerts")
            response["alerts_exist"] = False

        socket.send_json(obj={"res": response})


if __name__ == "__main__":
    main()
