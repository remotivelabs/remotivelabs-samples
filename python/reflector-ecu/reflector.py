import argparse
import binascii
import getopt
import grpc
import os
import queue
import sys
import time

from threading import Thread, Timer

import remotivelabs.broker.sync as br

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
        read_info = br.network_api_pb2.SignalIds(signalId=[signal])
        return stub.ReadSignals(read_info)
    except grpc._channel._Rendezvous as err:
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
    clientId = br.common_pb2.ClientId(id="id_ecu_A")
    while True:

        print("\necu_A, seed/counter is ", increasing_counter)
        # Publishes value 'counter'

        br.publish_signals(
            clientId,
            stub,
            [
                signal_creator.signal_with_payload(
                    "counter", namespace, ("integer", increasing_counter)
                ),
                # signal_creator.signal_with_payload(
                #     "TestFr07_Child01_UB", namespace, ("integer", 1)
                # ),
                # signal_creator.signal_with_payload(
                #     "TestFr07_Child02_UB", namespace, ("integer", 1)
                # ),
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
        read_info = br.network_api_pb2.SignalIds(signalId=signals)
        try:
            response = stub.ReadSignals(read_info)
            for signal in response.signal:
                print(f"ecu_B, (read) {signal.id.name} is {get_value(signal)}")
        except grpc._channel._Rendezvous as err:
            print(err)
        time.sleep(pause)


def get_value_pair(signal):
    if signal.raw != b"":
        raise Exception(f"not a valid signal, probably a frame {signal}")
    elif signal.HasField("integer"):
        return ("integer", signal.integer)
    elif signal.HasField("double"):
        return ("double", signal.double)
    elif signal.HasField("arbitration"):
        return ("arbitration", signal.arbitration)
    elif signal.HasField("empty"):
        return ("empty", signal.empty)
    else:
        raise Exception(f"not a valid signal {signal}")


def act_on_signal(client_id, stub, sub_signals, on_change, fun, on_subcribed=None):
    sub_info = br.network_api_pb2.SubscriberConfig(
        clientId=client_id,
        signals=br.network_api_pb2.SignalIds(signalId=sub_signals),
        onChange=on_change,
    )
    try:
        subscripton = stub.SubscribeToSignals(sub_info, timeout=None)
        if on_subcribed:
            on_subcribed(subscripton)
        print("waiting for signal...")
        for subs_counter in subscripton:
            fun(subs_counter.signal)

    except grpc.RpcError as e:
        try:
            subscripton.cancel()
        except grpc.RpcError as e2:
            pass

    except grpc._channel._Rendezvous as err:
        print(err)
    # reload, alternatively non-existing signal
    print("subscription terminated")


def main(argv):
    parser = argparse.ArgumentParser(description="Provide address to Beambroker")

    parser.add_argument(
        "-url",
        "--url",
        type=str,
        help="URL of the RemotiveBroker",
        required=True,
    )

    parser.add_argument(
        "-x_api_key",
        "--x_api_key",
        type=str,
        help="API key is required when accessing brokers running in the cloud",
        required=False,
        default="offline",
    )

    parser.add_argument(
        "-port",
        "--port",
        type=str,
        help="grpc port used on RemotiveBroker",
        required=False,
        default="50051",
    )

    args = parser.parse_args()
    run(args.url, args.x_api_key, args.port)


def double_and_publish(network_stub, client_id, trigger, signals):
    for signal in signals:
        # print(f"signals contains {signals}")
        print(f"ecu_B, (subscribe) {signal.id.name} {get_value(signal)}")
        if signal.id == trigger:
            br.publish_signals(
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


def all_siblings(name, namespace_name):
    frame_name = signal_creator.frame_by_signal(name, namespace_name)
    return signal_creator.signals_in_frame(frame_name.name, frame_name.namespace.name)


def some_function_to_calculate_crc(a, b, c):
    return 1


def change_namespace(signals, namespace_name):
    for signal in signals:
        signal.id.namespace.name = namespace_name


# TD;LR
# Forward all frames from ecu_A to ecu_B except TestFr07 which is modified on the fly. Gateway/reflector/forwarder
# forward all frames from ecu_B to ecu_A without exception
# TestFr07 is split into all signals. Some signals are modified and then dispatched on ecu_B
#
# refer to interfaces.json for reflector configuration.
def run(url, x_api_key, port):
    """Main function, checking arguments passed to script, setting up stubs, configuration and starting Threads."""
    # Setting up stubs and configuration
    intercept_channel = br.create_channel(url, x_api_key)

    network_stub = br.network_api_pb2_grpc.NetworkServiceStub(intercept_channel)
    system_stub = br.system_api_pb2_grpc.SystemServiceStub(intercept_channel)
    br.check_license(system_stub)

    br.upload_folder(system_stub, "configuration_can")
    br.reload_configuration(system_stub)

    global signal_creator
    signal_creator = br.SignalCreator(system_stub)

    # ecu a, we do this with lambda refering to modify_signal_publish_frame.
    reflector_client_id = br.common_pb2.ClientId(id="reflector_client_id")

    def modify_signals_publish_frame(
        network_stub, client_id, destination_namespace_name, signals
    ):
        # work in dictonary domain for easier access.
        signal_dict = {signal.id.name: signal for signal in signals}

        # example, lets update TestFr07_Child02
        (type, value) = get_value_pair(signal_dict["TestFr07_Child02"])
        signal_dict["TestFr07_Child02"] = signal_creator.signal_with_payload(
            "TestFr07_Child02", destination_namespace_name, (type, value + 1)
        )

        # example, lets update TestFr07_Child01_UB just invert this single bit
        (type, value) = get_value_pair(signal_dict["TestFr07_Child01_UB"])
        signal_dict["TestFr07_Child01_UB"] = signal_creator.signal_with_payload(
            "TestFr07_Child01_UB", destination_namespace_name, (type, 1 - value)
        )

        # example, lets compute counter_times_2 using some formula
        (type, value) = get_value_pair(signal_dict["counter_times_2"])
        signal_dict["counter_times_2"] = signal_creator.signal_with_payload(
            "counter_times_2",
            destination_namespace_name,
            (
                type,
                some_function_to_calculate_crc(
                    id,
                    destination_namespace_name,
                    [
                        (
                            "TestFr07_Child02",
                            get_value_pair(signal_dict["TestFr07_Child02"])[0],
                        ),
                        (
                            "TestFr07_Child01_UB",
                            get_value_pair(signal_dict["TestFr07_Child01_UB"])[0],
                        ),
                    ],
                ),
            ),
        )

        publish_list = signal_dict.values()
        # update destination namespace for all entrys in list
        change_namespace(publish_list, destination_namespace_name)
        # print(f"updates lists {publish_list}")
        br.publish_signals(client_id, network_stub, publish_list)

    Thread(
        target=act_on_signal,
        args=(
            reflector_client_id,
            network_stub,
            # get all childs in frame, alternatively we could do # all_siblings("counter_times_2", "ecu_A")
            signal_creator.signals_in_frame("TestFr07", "ecu_A"),
            False,  # True = only report when signal changes
            lambda signals: modify_signals_publish_frame(
                network_stub,
                reflector_client_id,
                "ecu_B",
                signals,
            ),
        ),
    ).start()


if __name__ == "__main__":
    main(sys.argv[1:])
