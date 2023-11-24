import argparse
import math
import time
import remotivelabs.broker.sync as br
import queue
from threading import Thread, Timer
import grpc

from typing import (
    Callable,
    Generator,
    Iterable,
    Optional,
    TypeVar,
    Sequence,
    Tuple,
    Optional,
)


def publish(
    broker,
    client_id: br.common_pb2.ClientId,
    network_stub: br.network_api_pb2_grpc.NetworkServiceStub,
    signals_with_values: [],
) -> grpc.RpcContext:
    broker.publish_signals(client_id, network_stub, signals_with_values)


def subscribe(
    broker,
    client_id: br.common_pb2.ClientId,
    network_stub: br.network_api_pb2_grpc.NetworkServiceStub,
    signals: br.network_api_pb2.Signals,
    on_subscribe: Callable[[Sequence[br.network_api_pb2.Signal]], None],
    on_change: bool = False,
) -> grpc.RpcContext:
    sync = queue.Queue()
    Thread(
        target=broker.act_on_signal,
        args=(
            client_id,
            network_stub,
            signals,
            on_change,  # True: only report when signal changes
            on_subscribe,
            lambda subscription: (sync.put(subscription)),
        ),
    ).start()
    # wait for subscription to settle
    subscription = sync.get()
    return subscription


def subscribe_list(
    signal_creator, signals: list[Tuple[str, str]]
) -> Generator[br.common_pb2.SignalId, None, None]:
    for namespace, signal in signals:
        yield signal_creator.signal(signal, namespace)


def _get_value_str(signal: br.network_api_pb2.Signal) -> str:
    if signal.raw != b"":
        return signal.raw
    elif signal.HasField("integer"):
        return signal.integer
    elif signal.HasField("double"):
        return signal.double
    elif signal.HasField("arbitration"):
        return signal.arbitration
    else:
        return "empty"


def printer(signals: br.network_api_pb2.Signals) -> None:
    for signal in signals:
        print(
            "{} {} {}".format(
                signal.id.name, signal.id.namespace.name, _get_value_str(signal)
            )
        )


def composeControlClimateFrame(signal_creator):
    # make sure to populate all relevant signals in this frame, alternatively publish a full frame.
    # to get reliability make sure to remove the unit that produces this frame. Alternative filter it out using RemotiveLabs reflector
    # 1 find all relevant sibling
    frame = signal_creator.frame_by_signal("ClimaRqrd1", "body_can_write")
    signals_in_frame = signal_creator.signals_in_frame(frame.name, frame.namespace.name)
    # for signal in signals_in_frame:
    #     print("Signal to pupulate", signal)

    # populate _all_ siblings. The ones not populate will be padded with binary zeros.
    signal_dict = {signal.name: signal for signal in signals_in_frame}
    signal_write_dict = dict()
    signal_write_dict["ClimaRqrd1"] = signal_creator.signal_with_payload(
        "ClimaRqrd1", signal_dict["ClimaRqrd1"].namespace.name, ("double", 10)
    )
    # recreate the signal list to be published.
    return signal_write_dict.values()


def run(
    url: str,
    signals: list[Tuple[str, str]],
    x_api_key: Optional[str] = None,
    access_token: Optional[str] = None,
) -> None:
    # gRPC connection to RemotiveBroker
    intercept_channel = br.create_channel(url, x_api_key, access_token)

    system_stub = br.system_api_pb2_grpc.SystemServiceStub(intercept_channel)
    network_stub = br.network_api_pb2_grpc.NetworkServiceStub(intercept_channel)
    br.check_license(system_stub)

    signal_creator = br.SignalCreator(system_stub)

    # Generate a list of values ready for subscribe
    subscribeValues = list(subscribe_list(signal_creator, signals))
    if len(subscribeValues) == 0:
        print("No signals found. Nothing to do...")
        return

    clientIdName = "MySubscriber_{}".format(math.floor(time.monotonic()))
    clientId: br.common_pb2.ClientId = br.common_pb2.ClientId(id=clientIdName)

    def publisher(signals: br.network_api_pb2.Signals) -> None:
        # just for log purposes
        printer(signals)
        pub_signals = composeControlClimateFrame(signal_creator)
        publish(br, clientId, network_stub, pub_signals)

    print("Subscribing on signals...")
    subscription = subscribe(br, clientId, network_stub, subscribeValues, publisher)

    try:
        while True:
            pass
    except KeyboardInterrupt:
        subscription.cancel()
        print("Keyboard interrupt received. Closing scheduler.")


class NamespaceArgument(argparse.Action):
    def __call__(self, _parser, namespace, value, _option):
        print("Select namespace:", value)
        setattr(namespace, "namespace", value)


class SignalArgument(argparse.Action):
    def __call__(self, _parser, namespace, value, _option):
        ns = getattr(namespace, "namespace")
        if not ns:
            raise Exception(f'Namespace must be specified before signal ("{value}")')
        namespace.accumulated.append((ns, value))


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
        action=NamespaceArgument,
        required=False,
    )

    parser.add_argument(
        "-s",
        "--signal",
        help="Signal to subscribe to",
        required=False,
        type=str,
        dest="accumulated",
        action=SignalArgument,
        default=[],
    )

    try:
        args = parser.parse_args()
    except Exception as e:
        return print("Error specifying signals to use:", e)
    signals = args.accumulated

    # hard code for the purpose of this demo, this specific signals is the one we are implementing.
    signals = [("vss_publish", "VehicleBodyMirrorsLeftPan")]
    run(args.url, signals, args.x_api_key, args.access_token)


# start by doing
# relevant project https://console.cloud.remotivelabs.com/p/vccdefault/recordings/2926915681680700400
# use configuration configuration_xc90_write_vss
# if needed
# $> pip install -U remotivelabs-cli 
# hint: try "remotive tui"
# $> remotive cloud auth login
# then 
# hard coded in data for the purpose to this demo, check "signals" in main method
# for out data check "composeControlClimateFrame"
# $> python3 subscribe_to_vss_publish_to_can.py --url https://personal-xktvetbdzw-vccdefault-sglnqbpwoa-ez.a.run.app --access_token $(remotive cloud auth print-access-token)

if __name__ == "__main__":
    main()
