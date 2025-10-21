# Scripted Signals

Remotive Broker enables you to perform computations on a stream of signals on the fly using your own Lua script while the signals are being streamed.

For a broader general overview, take a look at the [Scripted Signals documentation](https://docs.remotivelabs.com/docs/remotive-broker/scripted_signals).

## Usage

One use case for Scripted Signals is mapping signals between different signal databases, for example, mapping your proprietary signal database to the Vehicle Signal Specification (VSS).

### Prerequisites

Like all Python samples in this repository, the `remotivelabs-broker` pip package is required. Install all requirements using [pip](https://pypi.org/):

```shell
pip install -r requirements.txt
```

### Examples

The script `subscribe_scripted.py` is designed to work with our [Remotive Cloud](https://cloud.remotivelabs.com/) environment with the sample recording "Highway driving in Halland".

This example is easy to get started with as you use RemotiveCloud to run a RemotiveBroker.

1. Open [Remotive Cloud](https://cloud.remotivelabs.com/)
2. Login
3. Make sure you have imported the sample recording "Highway driving in Halland"
4. Open ""Highway driving in Halland", make sure `No transformation` is selected, then press `Play`.
5. Wait for playback to start, then open `Examples to subscribe to signals from an external application` and select `Python` panel.

Only look at the python command at the last line, which looks something like

```shell
python3 subscribe.py --url BROKER_URL --x_api_key API_KEY --signals VehicleBus:ID257DIspeed.DI_vehicleSpeed
```

Instead of running this command try:

```shell
python3 subscribe_scripted.py --url BROKER_URL --x_api_key API_KEY --script_path=scripts/Vehicle.Powertrain.TractionBattery.StateOfCharge.Displayed.lua
```

(ie keep BROKER_URL and API_KEY)

This command will subscribe to the signal named `Vehicle.Powertrain.TractionBattery.StateOfCharge.Displayed`, which is mapped from signals `ID352BMS_energyStatus.BMS_nominalFullPackEnergy` and `ID352BMS_energyStatus.BMS_nominalEnergyRemaining`, as defined in [scripts/Vehicle.Powertrain.TractionBattery.StateOfCharge.Displayed.lua](scripts/Vehicle.Powertrain.TractionBattery.StateOfCharge.Displayed.lua).

You can also change the frequency of emitted signals, as demonstrated in the following example:

```shell
python3 subscribe_scripted.py --url __BROKER_URL__ --x_api_key __API_KEY__ --script_path=scripts/Vehicle.Powertrain.TractionBattery.StateOfCharge.Displayed_10Hz.lua
```

For an example of how to simply rename a signal, try the script below:

```shell
python3 subscribe_scripted.py --url __BROKER_URL__ --x_api_key __API_KEY__ --script_path=scripts/Vehicle.Speed.lua
```
