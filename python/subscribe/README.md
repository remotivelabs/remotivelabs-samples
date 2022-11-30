# Subscribe
This sample will subscribe to a given signal and print any published values to this signal.

## Usage

As all python samples in this repository, the pip package [remotivelabs-broker](https://pypi.org/project/remotivelabs-broker/) is required. Install all requirements with [pip](https://pypi.org/):

    pip install -r requirements.txt

Subscribe to a signal by running.

    python subscribe.py --url http://192.168.4.1:50051 --namespace ecu_A --signal TestFr06_Child02

The script can take multiple `--signal` arguments for subscribing to several signals:

    python subscribe.py --url http://192.168.4.1:50051 --namespace ecu_A --signal TestFr06_Child02 --signal TestFr06_Child03
