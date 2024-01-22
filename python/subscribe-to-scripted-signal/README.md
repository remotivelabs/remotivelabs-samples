# Scripted Signals

Remotive Broker enables you to perform computations on a stream of signals on the fly using your own Lua script while the signals are being streamed.

For a broader general overview, take a look at the [Scripted Signals documentation](https://docs.remotivelabs.com/docs/broker/scripted_signals).

## Usage

One use case for Scripted Signals is mapping signals between different signal databases, for example, mapping your proprietary signal database to the Vehicle Signal Specification (VSS).

### Prerequisites

Like all Python samples in this repository, the `remotivelabs-broker` pip package is required. Install all requirements using [pip](https://pypi.org/):

```shell
pip install -r requirements.txt
```

### Examples

There are two example scripts in this sample.

The script `demo_subscribe.py` is designed to work with our [Remotive Cloud Demo](https://console.demo.remotivelabs.com/p/demo/recordings/13303517729834103000) environment.

The script `subscribe_standalone.py` is a comprehensive standalone script that works with any Remotive Broker setup.

#### Demo example

You can try `demo_subscribe.py` when you don't have a broker at hand and just want to explore how scripted signals work.

Visit our Remotive Cloud Demo [sample recording](https://console.demo.remotivelabs.com/p/demo/recordings/13303517729834103000), select `configuration_vss`, then press `Play`. Wait for a new page to open, then select the `Scripted Signals` tab in the `Examples to subscribe to signals from an external application` panel to find the full command to run `subscribe_demo.py`.

The command will look something like this:

```shell
python3 subscribe.py --url __BROKER_URL__ --x_api_key __API_KEY__ --scripted_code_path=scripted_code/Vehicle.Powertrain.TractionBattery.StateOfCharge.Displayed.lua
```

This command will subscribe to the signal named `Vehicle.Powertrain.TractionBattery.StateOfCharge.Displayed`, which is mapped from signals `ID352BMS_energyStatus.BMS_nominalFullPackEnergy` and `ID352BMS_energyStatus.BMS_nominalEnergyRemaining`, as defined in [scripts/Vehicle.Powertrain.TractionBattery.StateOfCharge.Displayed.lua](scripts/Vehicle.Powertrain.TractionBattery.StateOfCharge.Displayed.lua).

You can also change the frequency of emitted signals, as demonstrated in the following example:

```shell
python3 subscribe.py --url __BROKER_URL__ --x_api_key __API_KEY__ --script_path=scripts/Vehicle.Powertrain.TractionBattery.StateOfCharge.Displayed_10Hz.lua
```

For an example of how to simply rename a signal, try the script below:

```shell
python3 subscribe.py --url __BROKER_URL__ --x_api_key __API_KEY__ --script_path=scripts/Vehicle.Speed.lua
```

#### Standalone example

Using `subscribe.py` will reconfigure your broker with configuration from the `configuration` folder and upload sample recordings from the `recordings` folder.

The `configuration` folder contains the same configuration used in the demo example. Feel free to examine the files to see how to configure the scripted signals.

Let's imagine you are running a Remotive Broker at the URL `http://192.168.4.1:50051`.

Subscribe to the scripted signal `Vehicle.Powertrain.TractionBattery.StateOfCharge.Displayed` by running:

```shell
python3 subscribe.py --url http://192.168.4.1:50051 --script_path=scripts/Vehicle.Powertrain.TractionBattery.StateOfCharge.Displayed.lua
```

You can also change the frequency of emitted signals, as demonstrated in the following example:

```shell
python3 subscribe.py --url http://192.168.4.1:50051 --script_path=scripts/Vehicle.Powertrain.TractionBattery.StateOfCharge.Displayed_10Hz.lua
```

For an example of how to simply rename a signal, try the script below:

```shell
python3 subscribe.py --url http://192.168.4.1:50051 --script_path=scripts/Vehicle.Speed.lua
```
