from __future__ import annotations

import argparse
import time
from typing import Optional, List
from remotivelabs.broker.sync import Client, SignalsInFrame


def run_subscribe_sample(
        url: str,
        signals: list[str],
        namespaces: list[str],
        secret: Optional[str] = None
):
    client = Client(client_id="Sample client")
    client.connect(url=url, api_key=secret)

    def on_signals(signals_in_frame: SignalsInFrame):
        for signal in signals_in_frame:
            print(signal.to_json())

    client.on_signals = on_signals

    subscription = client.subscribe(signal_names=signals, namespaces=namespaces, changed_values_only=False)

    try:
        print("Broker connection and subscription setup completed, waiting for signals...")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        subscription.cancel()
        print("Keyboard interrupt received, closing")


def main():
    parser = argparse.ArgumentParser(description="Provide address to RemotiveBroker")

    parser.add_argument(
        "-u",
        "--url",
        help="URL of the RemotiveBroker",
        type=str,
        required=False,
        default="http://127.0.0.1:50051",
    )

    parser.add_argument(
        "-x",
        "--x_api_key",
        help="API key is required when accessing brokers running in the cloud",
        type=str,
        required=False,
        default=None,
    )

    parser.add_argument(
        "-t",
        "--access_token",
        help="Personal or service-account access token",
        type=str,
        required=False,
        default=None,
    )

    parser.add_argument(
        "-n",
        "--namespace",
        help="Namespace to select frames on",
        type=str,
        required=True,
        nargs="*"
    )

    parser.add_argument(
        "-s",
        "--signal",
        help="Signal to subscribe to",
        required=True,
        nargs="*"
    )

    try:
        args = parser.parse_args()
    except Exception as e:
        return print("Error specifying signals to use:", e)

    secret = args.x_api_key if args.x_api_key is not None else args.access_token
    run_subscribe_sample(args.url, args.signal, args.namespace, secret)


if __name__ == "__main__":
    main()
