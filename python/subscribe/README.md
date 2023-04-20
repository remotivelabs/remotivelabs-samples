# Subscribe
This sample will subscribe to a given signal and print any published values to this signal.

## Usage

As all python samples in this repository, the pip package [remotivelabs-broker](https://pypi.org/project/remotivelabs-broker/) is required. Install all requirements with [pip](https://pypi.org/):

    pip install -r requirements.txt

Subscribe to a signal by running.

    python subscribe.py --url http://192.168.4.1:50051 --namespace ecu_A --signal TestFr06_Child02

The script can take multiple `--signal` arguments for subscribing to several signals:

    python subscribe.py --url http://192.168.4.1:50051 --namespace ecu_A --signal TestFr06_Child02 --signal TestFr06_Child03

Always put the argument `--namespace` before `--signal`. This in necesarry because it's possible to read signals from multiple namespaces at once. This is archived by specifying several namespaces. Signals will be selected from the last given namespace. As an example:

    python subscribe.py --namespace ecu_A --signal TestFr06_Child02 --namespace ecu_B --signal TestFr06_Child02

This will subscribe to the signal `TestFr06_Child02` from the namespace `ecu_A` and the signal `TestFr06_Child02` from namespace `ecu_B`.
