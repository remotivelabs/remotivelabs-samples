from __future__ import annotations
from alive_progress import alive_bar

import alive_progress
import argparse
import time
import csv
from typing import Optional
from remotivelabs.broker.sync import (
    Client,
    SignalsInFrame,
    BrokerException,
    SignalIdentifier
)


def run_subscribe_sample(url: str, namespace: str, filename: str, secret: Optional[str] = None):
    client = Client(client_id="Sample client")
    client.connect(url=url, api_key=secret)
    signals =  list(filter(lambda s: s.namespace == namespace, client.list_signal_names()))
    if len(signals) == 0:
        print(f"No signals found on namespace {namespace}")
        exit(1)

    csv_file = open(filename, "w", newline='')

    with alive_bar(None, spinner='dots_waves2', title='Writing signals to csv') as bar:

        def csv_logger(csv_writer, signals):
            for signal in signals:
                bar()
                csv_writer.writerow(
                    ["{:.6f}".format(signal.timestamp_us()/1000000) ,signal.name(), signal.value()]
                )

        csv_logger_fun = lambda signals: csv_logger(csv.writer(
            csv_file, delimiter=",", quotechar="|", quoting=csv.QUOTE_MINIMAL
        ), signals)

        client.on_signals = csv_logger_fun

        try:
            subscription = client.subscribe(
                signals_to_subscribe_to=signals,
                changed_values_only=False,
            )
        except BrokerException as e:
            print(e)
            exit(1)
        except Exception as e:
            print(e)
            exit(1)

        try:
            print(
                "Broker connection and subscription setup completed, waiting for signals..."
            )
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            subscription.cancel()
            csv_file.close()
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
        "--access-token",
        help="Personal or service-account access token",
        type=str,
        required=False,
        default=None,
    )

    parser.add_argument(
        "-n",
        "--namespace",
        help="Namespace to export signals on",
        type=str,
        required=True,
        default=None,
    )

    parser.add_argument(
        "-f",
        "--file",
        help="File to export csv to",
        type=str,
        required=True,
        default=None,
    )

    try:
        args = parser.parse_args()
    except Exception as e:
        return print("Error specifying signals to use:", e)

    secret = args.x_api_key if args.x_api_key is not None else args.access_token
    run_subscribe_sample(args.url, args.namespace, args.file, secret)


if __name__ == "__main__":
    main()
