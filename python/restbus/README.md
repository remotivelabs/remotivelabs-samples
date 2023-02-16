# Restbus
This sample will take a given selection of frames and publish them out on a name space using their default / start values with the frequency specified in the database configuration.

If a frame doesn't have a cycle time, the frame will be published once when the script starts.

## Usage

As all python samples in this repository, the pip package [remotivelabs-broker](https://pypi.org/project/remotivelabs-broker/) is required. Install all requirements with [pip](https://pypi.org/):

    pip install -r requirements.txt

Run restbus for entire name space.

    python restbus.py --configure configuration_can --namespace ecu_A

Note: To reconfigure the broker, add the argument `--configure <directory>`. Where `<directory>` is the path of the directory containing the configuration you want to use.

To get an understanding of what is happening on the restbus, add the argument `--verbose`. This will print detailed information:

    python restbus.py --namespace ecu_A --verbose

To only echo out a given set of frames, use the argument `--frame`. This can be done multiple times for multiple frames:

    python restbus.py --namespace ecu_A --frame FrameA --frame FrameB

To do an exact opposite selection, add the argument `--exclude`:

    python restbus.py --namespace ecu_A --frame FrameA --frame FrameB --exclude

All frames except `FrameA` and `FrameB` will be echoed.

