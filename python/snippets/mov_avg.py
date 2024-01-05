#!/usr/bin/env python3

import os
import time
from collections import deque
from typing import Deque

import grpc
from remotivelabs.broker.sync import SignalWrapper, BrokerException, Client as BrokerClient

# Let´s keep the last window of signals here
received_signals: Deque[SignalWrapper] = deque(maxlen=int(os.environ.get("WINDOW", 1000)))
subscription = None

try:

    client = BrokerClient()
    client.on_connect = lambda c: print(f"Yay! - connected as {c.client_id} to {c.url}")
    client.on_signals = received_signals.extend  # Add all signals to received_signals

    client.connect(url=os.environ.get("URL", "http://localhost:50051"),
                   api_key=os.environ.get("API_KEY", None))

    subscription = client.subscribe(
        signal_names=[os.environ.get("SIGNAL_NAME", "Vehicle.Speed")],
        namespaces=[os.environ.get("NAMESPACE", "vss")],
        changed_values_only=False)

    def avg():
        all_values: list = list(map(lambda signal: signal.value(), list(received_signals)))
        if len(all_values) == 0:
            return None
        else:
            return {
                'avg': round(sum(all_values) / len(all_values), 2),
                'min': min(all_values),
                'max': max(all_values),
                'latest': all_values[-1],
                'count': len(all_values)
            }

    # Periodically calculate a moving average using avg() function
    while True:
        time.sleep(float(os.environ.get("INTERVAL", 2)))
        print(avg())


except grpc.RpcError as e:
    print("Problems connecting or subscribing")
    print(type(e))
    if isinstance(e, grpc.Call):
        print(f"{e.code()} - {e.details()}")
    else:
        print(e)

except BrokerException as e:
    print(e)
    if subscription is not None:
        subscription.cancel()

except KeyboardInterrupt:
    print("Keyboard interrupt received. Closing subscription.")
    if subscription is not None:
        subscription.cancel()
