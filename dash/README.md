Main files with implementation is in Dash2/cyber_physical_operator. Documentation
and steps on how to run in-progress. You should be running Python3.

Everything is meant to be run alongside a working simulator of SWaT through MiniCPS/MiniVM.

# Set-Up Steps
## Installing MiniCPS/MiniVM
1. 

## Running Everything
Note that you have to start python programs in this exact order for the processes to communicate
as intended.
```
TERMINAL 1
$ cd minicps/examples/swat-s1
$ sudo python2 custom_physical_process.py

TERMINAL 2
$ cd CPSOperatorSim/dash/Dash2/cyber_physical_operator
$ python3 cps_operator_agent.py

TERMINAL 3
$ cd CPSOperatorSim/dash/Dash2/cyber_physical_operator
$ python3 cps_operator_hub.py
```
