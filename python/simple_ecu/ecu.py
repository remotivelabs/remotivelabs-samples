import argparse
import binascii
import grpc
import os
import queue
import sys, getopt
import time

from remotivelabs.broker.sync import SignalCreator
import remotivelabs.broker.sync as broker
import remotivelabs.broker.sync.helper as helper

from threading import Thread, Timer


signal_creator = None
q = queue.Queue()


def read_signals(stub, signal):
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
        read_info = broker.network_api_pb2.SignalIds(signalId=[signal])
        return stub.ReadSignals(read_info)
    except broker._channel._Rendezvous as err:
        print(err)


def ecu_A(stub, pause):
    """Publishes a value, read other value (published by ecu_B)

    Parameters
    ----------
    stub : NetworkServiceStub
        Object instance of class
    pause : int
        Amount of time to pause, in seconds

    """
    increasing_counter = 0
    namespace = "ecu_A"
    clientId = broker.common_pb2.ClientId(id="id_ecu_A")
    while True:

        print("\necu_A, seed is ", increasing_counter)
        # Publishes value 'counter'

        helper.publish_signals(
            clientId,
            stub,
            [
                signal_creator.signal_with_payload(
                    "counter", namespace, ("integer", increasing_counter)
                ),
                # add any number of signals here, make sure that all signals/frames are unique.
                # signal_creator.signal_with_payload(
                #     "TestFr04", namespace, ("raw", binascii.unhexlify("0a0b0c0d")), False
                # ),
            ],
        )

        time.sleep(pause)

        # Read the other value 'counter_times_2' and output result

        read_signal_response = read_signals(
            stub, signal_creator.signal("counter_times_2", namespace)
        )
        for signal in read_signal_response.signal:
            print(f"ecu_A, (result) {signal.id.name} is {get_value(signal)}")
        increasing_counter = (increasing_counter + 1) % 4


def read_on_timer(stub, signals, pause):
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
        read_info = broker.network_api_pb2.SignalIds(signalId=signals)
        try:
            response = stub.ReadSignals(read_info)
            for signal in response.signal:
                print(f"ecu_B, (read) {signal.id.name} is {get_value(signal)}")
        except broker._channel._Rendezvous as err:
            print(err)
        time.sleep(pause)


def get_value(signal):
    if signal.raw != b"":
        return "0x" + binascii.hexlify(signal.raw).decode("ascii")
    elif signal.HasField("integer"):
        return signal.integer
    elif signal.HasField("double"):
        return signal.double
    elif signal.HasField("arbitration"):
        return signal.arbitration
    else:
        return "empty"


def main(argv):
    parser = argparse.ArgumentParser(description="Provide address to Beambroker")
    parser.add_argument(
        "-url",
        "--url",
        type=str,
        help="URL of the Beamy Broker",
        required=False,
        default="http://127.0.0.1:50051",
    )
    parser.add_argument(
        "-reload_config",
        "--reload_config",
        action="store_true",
        help="Reload configuration",
        required=False,
        default=False,
    )
    parser.add_argument(
        "-x_api_key",
        "--x_api_key",
        type=str,
        help="required api key for https sessions",
        required=False,
        default="offline",
    )
    args = parser.parse_args()

    run(args.url, args.reload_config, args.x_api_key)


def double_and_publish(network_stub, client_id, trigger, signals):
    for signal in signals:
        print(f"ecu_B, (subscribe) {signal.id.name} {get_value(signal)}")
        if signal.id == trigger:
            helper.publish_signals(
                client_id,
                network_stub,
                [
                    signal_creator.signal_with_payload(
                        "counter_times_2", "ecu_B", ("integer", get_value(signal) * 2)
                    ),
                    # add any number of signals/frames here
                    # signal_creator.signal_with_payload(
                    #     "TestFr04", "ecu_B", ("raw", binascii.unhexlify("0a0b0c0d")), False
                    # )
                ],
            )


def run(url, restart_broker, x_api_key):
    """Main function, checking arguments passed to script, setting up stubs, configuration and starting Threads."""
    # Setting up stubs and configuration
    intercept_channel = helper.create_channel(url, x_api_key)

    network_stub = broker.network_api_pb2_grpc.NetworkServiceStub(intercept_channel)
    system_stub = broker.system_api_pb2_grpc.SystemServiceStub(intercept_channel)
    helper.check_license(system_stub)

    helper.upload_folder(system_stub, "configuration_udp")
    # upload_folder(system_stub, "configuration_lin")
    # upload_folder(system_stub, "configuration_can")
    # upload_folder(system_stub, "configuration_canfd")
    helper.reload_configuration(system_stub)

    global signal_creator
    signal_creator = SignalCreator(system_stub)

    # Lists available signals
    configuration = system_stub.GetConfiguration(broker.common_pb2.Empty())
    for networkInfo in configuration.networkInfo:
        print(
            "signals in namespace ",
            networkInfo.namespace.name,
            system_stub.ListSignals(networkInfo.namespace),
        )

    # Starting Threads

    # ecu b, we do this with lambda refering to double_and_publish.
    ecu_b_client_id = broker.common_pb2.ClientId(id="id_ecu_B")

    ecu_B_sub_thread = Thread(
        target=helper.act_on_signal,
        args=(
            ecu_b_client_id,
            network_stub,
            [
                signal_creator.signal("counter", "ecu_B"),
                # here you can add any signal from any namespace
                # signal_creator.signal("TestFr04", "ecu_B"),
            ],
            True,  # True: only report when signal changes
            lambda signals: double_and_publish(
                network_stub,
                ecu_b_client_id,
                signal_creator.signal("counter", "ecu_B"),
                signals,
            ),
            lambda subscripton: (q.put(("id_ecu_B", subscripton))),
        ),
    )
    ecu_B_sub_thread.start()
    # wait for subscription to settle
    ecu, subscription = q.get()

    # ecu a, this is where we publish, and
    ecu_A_thread = Thread(
        target=ecu_A,
        args=(
            network_stub,
            1,
        ),
    )
    ecu_A_thread.start()

    # ecu b, bonus, periodically, read using timer.
    signals = [
        signal_creator.signal("counter", "ecu_B"),
        # add any number of signals from any namespace
        # signal_creator.signal("TestFr04", "ecu_B"),
    ]
    ecu_read_on_timer = Thread(target=read_on_timer, args=(network_stub, signals, 1))
    ecu_read_on_timer.start()

    # once we are done we could cancel subscription
    # subscription.cancel()


if __name__ == "__main__":
    main(sys.argv[1:])
