import signal as signals
import sys
import threading
from argparse import Namespace
from typing import Any

from lib import arguments
from lib.broker import Broker

# Simple program designed to be used with our cloud demo.
# It is expected that you have followed the steps at
# https://demo.remotivelabs.com and started a broker + uploaded
# a recording.

# Once you complete the stages in our cloud-demo you will get all
# information required to run this program. It will look something like:

# python3 cloud_demo.py \
#      --url <broker_url> \
#      --api-key <api_key> \
#      --signals VehicleSpeed,ChassisAcceleratorPedalposition

expected_available_signals = [
    "VehicleSpeed",
    "ChassisSteeringwheelAngle",
    "ChassisAcceleratorPedalposition",
    "VehicleCurrentlocationLongitude",
    "VehicleCurrentlocationLatitude",
]


def print_signals(frame: Any) -> None:
    for s in frame:
        print(s)


def main(argv: Namespace) -> None:
    print(f"Connecting to {argv.url}")

    broker = Broker(argv.url, argv.api_key, argv.access_token)

    print("Listing available signals")
    available_signals = broker.list_signal_names()
    for signal in available_signals:
        print(f" - {signal}")

    # Sanity check so we are running against the expected recording
    if available_signals != expected_available_signals:
        print(
            "It does not look like you have started the demo recording in cloud. \n"
            "Make sure you play turning-torso-drivecycle.zip on this broker from "
            "https://demo.remotivelabs.com/p/demo/brokers"
        )
        sys.exit(0)

    # Start subscribe to selected signals
    subscription = broker.subscribe(signals=argv.signals, on_frame=print_signals, changed_values_only=True)

    # play demo recording
    broker.play(namespace="custom_can", path="turning-torso-drivecycle.zip")

    # Wait 20 seconds and then shutdown.
    # Remove the lines below to just have it running
    sleep(seconds=20)

    print("Cancelling subscription (20 secs or ctr-c, you can change this to just keep it running)")
    subscription.cancel()


def sleep(seconds: float) -> None:
    lock = threading.Event()
    signals.signal(signals.SIGINT, lambda signum, frame: lock.set())
    lock.wait(timeout=seconds)


if __name__ == "__main__":
    args = arguments.parse()
    main(args)
