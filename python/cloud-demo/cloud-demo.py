import time

from lib.broker import Broker
from lib import arguments
import sys

"""
Simple program designed to be used with our cloud demo.
It is expected that you have followed the steps at
https://demo.remotivelabs.com and started a broker + uploaded
a recording.

Once you complete the stages in our cloud-demo you will get all 
information required to run this program. It will look something like:

python3 cloud-demo.py \
     --url <broker_url> \
     --api-key <api_key> \
     --signals Speed,Accelerator_PedalPosition
     
"""


def print_signals(frame):
    for s in frame:
        print(s)


def main(args):
    print(f"Connecting to {args.url}")
    broker = Broker.connect(args.url, args.api_key)

    print("Listing available signals")
    for signal in broker.list_signal_names():
        print(f" - {signal}")

    subscription = broker.subscribe(
        signals=args.signals,
        on_frame=print_signals,
        changed_values_only=True)

    broker.play(namespace="custom_can", path="turning-torso-drivecycle.zip")

    time.sleep(20)

    print("Cancelling subscription after 20 seconds")
    subscription.cancel()


if __name__ == "__main__":
    args = arguments.parse(sys.argv[1:])
    main(args)
