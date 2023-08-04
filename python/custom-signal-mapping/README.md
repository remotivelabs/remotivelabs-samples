# Custom Signal Mapping

Custom signal mapping is a feature of RemotiveBroker that enables you to perform computations on a stream of signals
using your own Lua code while the data is being streamed. A common use case would be mapping signals between different
signal databases - for example, mapping your proprietary signal database to the Vehicle Signal Specification (VSS).

However, it can also be used to execute any type of computation within the broker itself.

In a single step, custom signal mapping allows you to:

1) Write your own mapping code,
2) Apply it to the broker,
3) Subscribe to mapped values.

> Currently, the script only operates against the demo environment (https://demo.remotivelabs.com/) or against a RemotiveBroker version `sha-af7ece7`.

## Usage

### Prerequisites

Like all Python samples in this repository, the pip package [remotivelabs-broker](https://pypi.org/project/remotivelabs-broker/)
is required. Install all requirements with [pip](https://pypi.org/):

    pip install -r requirements.txt

### Examples

Subscribe to mapped signals by running:

    python subscribe.py --url http://192.168.4.1:50051 --mapping_code_path=mapping_code/Vehicle.Powertrain.TractionBattery.StateOfCharge.Displayed.lua

This will subscribe to the signal named `Vehicle.Powertrain.TractionBattery.StateOfCharge.Displayed` that is mapped
from signals `ID352BMS_energyStatus.BMS_nominalFullPackEnergy` and `ID352BMS_energyStatus.BMS_nominalEnergyRemaining`,
as defined in
[mapping_code/Vehicle.Powertrain.TractionBattery.StateOfCharge.Displayed.lua](mapping_code/Vehicle.Powertrain.TractionBattery.StateOfCharge.Displayed.lua).

You can also change the frequency of emitted signals, as demonstrated in the following example:

    python subscribe.py --url http://192.168.4.1:50051 --mapping_code_path=mapping_code/Vehicle.Powertrain.TractionBattery.StateOfCharge.Displayed_10Hz.lua

For an example of how to simply rename a signal, try the script below:

    python subscribe.py --url http://192.168.4.1:50051 --mapping_code_path=mapping_code/Vehicle.Speed.lua
