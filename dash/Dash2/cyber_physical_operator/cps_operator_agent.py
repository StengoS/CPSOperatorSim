"""
Main implementation component of the Human-Cyber SWaT model and proof-of-concept for "Modeling Human-Cyber
Interactions in Safety-Critical Cyber-Physical/Industrial Control Systems (CPS/ICS)" as part of USC ISI REU 2022;
this is the CPS operator side of the implementation.
"""

import sys; sys.path.extend(['../../'])

from Dash2.core.dash_agent import DASHAgent
from Dash2.core.system2 import isVar
from Dash2.core.string_aux import convert_camel
from Dash2.core.system2 import System2Agent, substitute
from Dash2.core.system1 import System1Agent
from Dash2.core.client import Client
from Dash2.core.human_traits import HumanTraits

import argparse
import zmq


class OperatorDashAction(Client, System1Agent, System2Agent):
    """
    Created a "custom" DashAction class copied directly from Dash2/core/dash_action.py so that we can add 'print'
    statements and take a closer look at what's going on as we're learning how to use DASH and create a custom
    DASH agent.

    Customized to work with the central operator hub connection using pyzmq, leveraging **kwargs, json/dictionaries,
    etc.

    TODO: Comment differences from original DASHAction and document control flow (e.g., how does a decision get
     made and how are results tracked).
    """
    parameters = []  # Input parameters, each an instance of Parameter giving a name and info about the possible values
    measures = []  # Possible measures on the performance of the agent used for validation or as an outcome

    def __init__(self, system1_class=System1Agent, system2_class=System2Agent):
        Client.__init__(self)
        system2_class.__init__(self)
        system1_class.__init__(self)

        # TODO: Put back all the original traces.
        self.traceUpdate = False
        self.traceAction = False
        self.traceLoop = True
        # Although 'forget' is defined in system2, it is assigned primitive here because that module is compiled first
        self.primitiveActions([('forget', self.forget), ['sleep', self.sleep]])

        # Instantiate some agent values from the declared parameters. By default, use the default value,
        # otherwise sample the distribution
        # Need some code for when there is no distribution etc.
        for p in self.__class__.parameters:
            setattr(self, p.name, p.distribution.sample() if p.default is None else p.default)

    # This is in the java part in the old agent
    #
    def agent_loop(self, max_iterations=-1, disconnect_at_end=True, **kwargs):
        next_action = self.agent_decision_cycle(next_action=None)
        iteration = 0
        while next_action is not None and (max_iterations < 0 or iteration < max_iterations):
            next_action = self.agent_decision_cycle(next_action=next_action)
            iteration += 1
        if self.traceLoop and next_action is None:
            print("Exiting simulation: no action chosen")
        elif self.traceLoop and 0 <= max_iterations <= iteration:
            print("Exiting simulation: finished finite agent cycles:", iteration, "of max", max_iterations)
        if disconnect_at_end:
            self.disconnect()
        # return the action chosen so the caller can tell if there is more for the agent to do
        return next_action

    # This is agent's individual decision step.
    def agent_decision_cycle(self, **kwargs):
        if 'next_action' in kwargs:
            next_action = kwargs['next_action']
            if next_action is None:
                # self.spreading_activation()
                self.system1_update()
                next_action = self.choose_action()
            else:
                if self.traceAction:
                    print(self.id, "next action is", next_action)
                result = self.perform_action(next_action)
                self.update_beliefs(result, next_action)
                # self.spreading_activation()
                self.system1_update()
                next_action = self.choose_action()
                self.system1_step()
            return next_action
        else:  # need this for DES_work_processor
            # self.spreading_activation()
            self.system1_update()
            next_action = self.choose_action()
            if self.traceAction:
                print(self.id, "next action is", next_action)
            result = self.perform_action(next_action)
            self.update_beliefs(result, next_action)
            # self.spreading_activation()
            self.system1_update()
            next_action = self.choose_action()
            self.system1_step()
            return next_action

    def choose_action(self):
        # system1_actions = self.actions_over_threshold(threshold=self.system1_threshold)
        system1_actions = self.system1_propose_actions()
        if system1_actions and self.bypass_system2(system1_actions):
            return system1_actions[0]  # will ultimately choose
        system2_action = self.system2_propose_action()
        # For now always go with the result of reasoning if it was performed
        chosen_action = self.arbitrate_system1_system2(system1_actions, system2_action)
        return chosen_action

    # Given that system 2 was not bypassed, choose between the action it suggests and any actions
    # suggested by system 1
    def arbitrate_system1_system2(self, system1_actions, system2_action):
        # By default return system2 action if it is available
        if system2_action is None and system1_actions:
            return system1_actions[0]
        else:
            return system2_action

    # If system1 proposes some actions, should the agent just go with them or opt to employ deliberative reasoning?
    def bypass_system2(self, system1_action_nodes):
        print('considering system1 suggested actions ', system1_action_nodes)
        return True  # try system 1 by default if it's available

    def primitiveActions(self, l):
        # Add the items into the set of known primitive actions
        # mapping name to function
        for item in l:
            if isinstance(item, str):
                self.primitiveActionDict[item] = item  # store the name and look for the function at planning time
            else:
                self.primitiveActionDict[item[0]] = item[1]

    # This format is now inefficient since we have different ways that a predicate can be a primitive action
    def perform_action(self, action):
        if self.isPrimitive(action):
            predicate = action[0]
            if predicate in self.primitiveActionDict:
                function = self.primitiveActionDict[action[0]]
            elif hasattr(self, predicate) and callable(getattr(self, predicate)):
                function = getattr(self, predicate)
            else:
                underscore_action = convert_camel(predicate)
                if hasattr(self, underscore_action) and callable(getattr(self, underscore_action)):
                    function = getattr(self, underscore_action)
                else:
                    return
            return function(action)

    def update_beliefs(self, result, action):
        # print("Updating beliefs based on action", action, "with result", result)
        if result == 'TryAgain':
            return  # in some cases, want the side effects to happen and then re-try the same goal.
        elif not result and not self.isTransient(action):
            # print("Adding known false", action)
            self.knownFalseTuple(action)
            self.add_activation(action, 0.3)  # smaller bump for a failed action
        if isinstance(result, list):
            for bindings in result:
                concrete_result = substitute(action, bindings)
                if not self.isTransient(concrete_result):
                    # print("Adding known true and performed", concrete_result)
                    self.knownTuple(concrete_result)  # Mark action as performed/known
                    self.knownTuple(
                        ('performed', concrete_result))  # Adding both lets both idioms be used in the agent code.
                self.add_activation(concrete_result, 0.8)

    # Call a named measure on the agent
    def call_measure(self, name):
        measure = self.find_measure(name)
        if measure is not None:
            return measure.eval(self)

    # Find a measure given a name
    def find_measure(self, name):
        for m in self.measures:
            if m.name == name:
                return m

    # Generic primitive actions

    # A null action that always succeeds, useful for dummy steps
    def succeed(self, action):
        print("Primitive action", action, "trivially succeeds")
        return [{'performed': action}]


class OperatorDASHAgent(OperatorDashAction, HumanTraits):
    def __init__(self):
        print("Using custom OperatorDASHAgent...")

        HumanTraits.__init__(self)
        OperatorDashAction.__init__(self)


class CPSOperator(OperatorDASHAgent):
    """
    Custom DASH agent in-progress, meant to model the actions and behaviors of a CPS human operator maintaining a water treatment
    system. This simulated operator interacts with a simulated water treatment testbed, Singapore University of Technology and
    Design's Secure Water Treatment (SWaT).
    """

    def __init__(self, socket):
        OperatorDASHAgent.__init__(self)

        # TODO: Add more possible actions, configure so that based on results of alert.
        self.readAgent("""
goalWeight doWork 1

goalRequirements doWork
  checkForAlerts(alert)
  addressAlert(alert)
  sleep(1)
  forget([checkForAlerts(x), addressAlert(x), sleep(x)])

goalRequirements doWork
  checkTankWaterLevel(tanklevel)
  forget([checkTankWaterLevel(x)])
  
transient doWork
                       """)

        self.hub_connection = socket


    # Operator checks for any alerts from the water treatment plant, signifying that there is something that urgent
    # that needs to be addressed. 
    def check_for_alerts(self, goal):
        print("Checking for alerts from the water treatment testbed...")

        res = {
            "replier": "dash_agent"
        }

        received_req = self.hub_connection.recv_json()
        self.hub_connection.send_json(obj=res)
        if len(received_req["alerts"]) == 0:
            print("\tNo alerts reported.")

            return []

        else:
            print("\tSome alerts reported.")

            return [{}]

    # If there is an active alert from the water treatment plant, operator then "addresses" it as necessary. For
    # example, if the plant sends an alert that the water tank is at 'HH' level, operator needs to drain some water.
    # TODO: Finish implementation.
    def address_alert(self, goal):
        print("Addressing some alert...")

        received_req = self.hub_connection.recv_json()
        print(received_req)

        res = {
            "replier": "dash_agent"
        }
        self.hub_connection.send_json(obj=res)

        return [{}]
    
    # Operator checks the water level of the tank from the water treatment plant. 
    def check_tank_water_level(self, goal):
        print("Checking tank water level...")

        received_req = self.hub_connection.recv_json()
        print("\tWater tank level reported to be %g." % (received_req["tank_level"]))

        res = {
            "replier": "dash_agent"
        }
        self.hub_connection.send_json(obj=res)

        return [{}]
    
    # Operator drains some water from the tank of the water treatment plant.
    # TODO: Finish implementation.
    def drain_tank(self, goal):
        print("Draining water tank...")

        received_req = self.hub_connection.recv_json()
        print(received_req)

        res = {
            "replier": "dash_agent"
        }
        self.hub_connection.send_json(obj=res)

        return [{}]


def main():
    # Adapted from https://zeromq.org/languages/python/, binds REP socket to tcp://*:5555; setting up client connection
    # to cps_operator_hub.py, assuming it's already active.
    context = zmq.Context()

    # Socket to talk to server/hub
    print("Connecting to cps_operator_hub.py...")
    socket = context.socket(zmq.REP)
    socket.bind("tcp://*:5556")

    test_agent = CPSOperator(socket)
    test_agent.agent_loop(max_iterations=100)


if __name__ == "__main__":
    main()
