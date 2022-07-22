import sys
sys.path.extend(['../../']) # need to have 'webdash' directory in $PYTHONPATH, if we want to run script (as "__main__")

import random
from Dash2.core.system2 import System2Agent
from Dash2.core.system1 import System1Agent
from Dash2.core.human_traits import HumanTraits
from Dash2.core.sem_agent import SEMAgent
from Dash2.core.dash_action import DASHAction
from Dash2.core.des_agent import DESAgent
from semopy.examples import political_democracy
desc = political_democracy.get_model()
data = political_democracy.get_data()


class CPSOperatorAgent(DESAgent):

    def __init__(self, **kwargs):
        DESAgent.__init__(self, **kwargs)

    def agent_decision_cycle(self, **kwargs):
        agent_data = kwargs.get('agent_data', None)
        event_time = kwargs.get('event_time', None)
        if agent_data is None or event_time is None:
            raise AssertionError("decision_data_object and event_time cannot be None")

        action = self.choose_action(**kwargs)
        self.perform_action(action, **kwargs)
        log_item = {'actionType': action, 'nodeTime': str(event_time)}
        print(log_item)
        self.event_counter += 1
        return action

    def choose_action(self, **kwargs):
        return random.choice(['provide_input', 'inspect_reading', 'fix_machine'])

    def provide_input(self, **kwargs):
        print("Operator providing random number: " + str(random.randint(-100, 100)))
        return "provide_input"

    def inspect_reading(self, **kwargs):
        print("Machine providing random number: " + str(random.randint(-100, 100)))
        return "inspect_reading"

    def fix_machine(self, **kwargs):
        print("Machine fixed")
        return "fix_machine"


if __name__ == "__main__":
    # test_agent = DESAgent()
    # test_agent.agent_loop(max_iterations=10, agent_data={})

    cps_operator1 = CPSOperatorAgent()
    cps_operator1.agent_loop(max_iterations=10, agent_data={})
