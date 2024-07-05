from __future__ import annotations

import argparse
import binascii
import queue
import sys
import time
from threading import Thread
from typing import Any, Callable, Optional, Sequence

import grpc
import remotivelabs.broker.sync as br

q: queue.Queue[Any] = queue.Queue()


def read_signals(stub: br.network_api_pb2_grpc.NetworkServiceStub, signal: br.common_pb2.SignalId) -> br.network_api_pb2.Signals:
    """Read signals

    Parameters
    ----------
    stub : NetworkServiceStub
        Object instance of class
    signal : SignalId
        Object instance of class

    Returns
    -------
    Signals
        Object instance of class

    """
    try:
        read_info = br.network_api_pb2.SignalIds(signalId=[signal])
        return stub.ReadSignals(read_info)
    except grpc.RpcError as err:
        print(err)
        return sys.exit()


def ecu_a(stub: br.network_api_pb2_grpc.NetworkServiceStub, signal_creator: br.SignalCreator) -> None:
    """Publishes a value with set frequncy in database or default to 1000ms, read other value (published by ecu_B)

    Parameters
    ----------
    stub : NetworkServiceStub
        Object instance of class

    """
    if signal_creator is None:
        return

    namespace = "ecu_A"
    increasing_counter = 0
    counter_start_value = int(signal_creator.get_meta("counter", namespace).getStartValue(0))
    client_id = br.common_pb2.ClientId(id="id_ecu_A")
    counter_frame = signal_creator.frame_by_signal("counter", namespace)
    pause = 0.001 * signal_creator.get_meta(counter_frame.name, counter_frame.namespace.name).getCycleTime(1000.0)
    while True:
        print("\necu_A, seed is ", increasing_counter)
        # Publishes value 'counter'

        br.publish_signals(
            client_id,
            stub,
            [
                signal_creator.signal_with_payload("counter", namespace, ("integer", increasing_counter)),
                # add any number of signals here, make sure that all signals/frames are unique.
                # signal_creator.signal_with_payload(
                #     "TestFr04", namespace, ("raw", binascii.unhexlify("0a0b0c0d")), False
                # ),
            ],
        )

        time.sleep(pause)

        # Read the other value 'counter_times_2' and output result

        read_signal_response = read_signals(stub, signal_creator.signal("counter_times_2", namespace))
        for signal in read_signal_response.signal:
            print(f"ecu_A, (result) {signal.id.name} is {get_value(signal)}")
        increasing_counter = counter_start_value + (increasing_counter + 1) % 4


def read_on_timer(stub: br.network_api_pb2_grpc.NetworkServiceStub, signals: Sequence[br.common_pb2.SignalId], pause: int) -> None:
    """Simple reading with timer

    Parameters
    ----------
    stub : NetworkServiceStub
        Object instance of class
    signals : SignalId
        Object instance of class
    pause : int
        Amount of time to pause, in seconds

    """
    while True:
        read_info = br.network_api_pb2.SignalIds(signalId=signals)
        try:
            response = stub.ReadSignals(read_info)
            for signal in response.signal:
                print(f"ecu_B, (read) {signal.id.name} is {get_value(signal)}")
        except grpc.RpcError as err:
            print(err)
        time.sleep(pause)


def get_value(signal: br.network_api_pb2.Signal) -> Any:
    if signal.raw != b"":
        return "0x" + binascii.hexlify(signal.raw).decode("ascii")
    if signal.HasField("integer"):
        return signal.integer
    if signal.HasField("double"):
        return signal.double
    if signal.HasField("arbitration"):
        return signal.arbitration
    return "empty"


def main() -> None:
    parser = argparse.ArgumentParser(description="Provide address to Beambroker")

    parser.add_argument("-url", "--url", type=str, help="URL of the RemotiveBroker", default="http://127.0.0.1:50051", required=False)

    parser.add_argument(
        "-x_api_key",
        "--x_api_key",
        type=str,
        help="API key is required when accessing brokers running in the cloud",
        required=False,
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
        "-c",
        "--configure",
        type=str,
        metavar="DIRECTORY",
        help="Configure broker with specified configuration directory",
        default="configuration_udp",
    )

    args = parser.parse_args()
    run(args.url, args.configure, args.x_api_key, args.access_token)


def double_and_publish(
    network_stub: br.network_api_pb2_grpc.NetworkServiceStub,
    client_id: br.common_pb2.ClientId,
    trigger: Any,
    signals: Sequence[br.network_api_pb2.Signal],
    signal_creator: br.SignalCreator,
) -> None:
    if signal_creator is None:
        return

    for signal in signals:
        print(f"ecu_B, (subscribe) {signal.id.name} {get_value(signal)}")
        if signal.id == trigger:
            br.publish_signals(
                client_id,
                network_stub,
                [
                    signal_creator.signal_with_payload("counter_times_2", "ecu_B", ("integer", get_value(signal) * 2)),
                    # add any number of signals/frames here
                    # signal_creator.signal_with_payload(
                    #     "TestFr04", "ecu_B", ("raw", binascii.unhexlify("0a0b0c0d")), False
                    # )
                ],
            )


# pylint: disable=R0913
def subscribe(
    broker: Any,
    client_id: br.common_pb2.ClientId,
    network_stub: br.network_api_pb2_grpc.NetworkServiceStub,
    signals: Sequence[br.common_pb2.SignalId],
    on_subscribe: Callable[[Sequence[br.network_api_pb2.Signal]], None],
    on_change: bool = False,
) -> Any:
    sync: queue.Queue[Any] = queue.Queue()
    Thread(
        target=broker.act_on_signal,
        args=(
            client_id,
            network_stub,
            signals,
            on_change,  # True: only report when signal changes
            on_subscribe,
            sync.put,
        ),
    ).start()
    # wait for subscription to settle
    subscription = sync.get()
    return subscription


def run(url: str, configuration_folder: str, x_api_key: Optional[str] = None, access_token: Optional[str] = None) -> None:
    """Main function, checking arguments passed to script, setting up stubs, configuration and starting Threads."""
    # Setting up stubs and configuration
    intercept_channel = br.create_channel(url, x_api_key, access_token)

    network_stub = br.network_api_pb2_grpc.NetworkServiceStub(intercept_channel)
    system_stub = br.system_api_pb2_grpc.SystemServiceStub(intercept_channel)
    br.check_license(system_stub)

    print(f"Using configuration {configuration_folder}")
    br.upload_folder(system_stub, configuration_folder)
    br.reload_configuration(system_stub)

    signal_creator = br.SignalCreator(system_stub)

    # Lists available signals
    configuration = system_stub.GetConfiguration(br.common_pb2.Empty())
    for network_info in configuration.networkInfo:
        print(
            "signals in namespace ",
            network_info.namespace.name,
            system_stub.ListSignals(network_info.namespace),
        )

    # ecu b, we do this with lambda refering to double_and_publish.
    ecu_b_client_id = br.common_pb2.ClientId(id="id_ecu_B")

    # Starting subscription thread
    _ = subscribe(
        br,
        ecu_b_client_id,
        network_stub,
        [
            signal_creator.signal("counter", "ecu_B"),
            # here you can add any signal from any namespace
            # signal_creator.signal("TestFr04", "ecu_B"),
        ],
        lambda signals: double_and_publish(
            network_stub, ecu_b_client_id, signal_creator.signal("counter", "ecu_B"), signals, signal_creator
        ),
    )

    # ecu a, this is where we publish, and
    Thread(
        target=ecu_a,
        args=(network_stub, signal_creator),
    ).start()

    # ecu b, bonus, periodically, read using timer.
    signals = [
        signal_creator.signal("counter", "ecu_B"),
        # add any number of signals from any namespace
        # signal_creator.signal("TestFr04", "ecu_B"),
    ]
    Thread(target=read_on_timer, args=(network_stub, signals, 1)).start()

    # once we are done we could cancel subscription
    # subscription.cancel()


if __name__ == "__main__":
    main()
