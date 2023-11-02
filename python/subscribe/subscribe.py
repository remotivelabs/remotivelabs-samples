import argparse
import math
import time
import remotivelabs.broker.sync as br
import queue
from threading import Thread, Timer
import grpc

from typing import Callable, Generator, Iterable, Optional, TypeVar, Sequence, Tuple, Optional


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


def run(
    url: str,
    signals: list[Tuple[str, str]],
    x_api_key:  Optional[str] = None,
    access_token: Optional[str] = None
) -> None:
    # gRPC connection to RemotiveBroker
    intercept_channel = br.create_channel(url, x_api_key, access_token)

    system_stub = br.system_api_pb2_grpc.SystemServiceStub(intercept_channel)
    network_stub = br.network_api_pb2_grpc.NetworkServiceStub(intercept_channel)
    br.check_license(system_stub)

    # Generate a list of values ready for subscribe
    subscribeValues = list(subscribe_list(br.SignalCreator(system_stub), signals))
    if len(subscribeValues) == 0:
        print("No signals found. Nothing to do...")
        return

    clientIdName = "MySubscriber_{}".format(math.floor(time.monotonic()))
    clientId: br.common_pb2.ClientId = br.common_pb2.ClientId(id=clientIdName)

    print("Subscribing on signals...")
    subscription = subscribe(br, clientId, network_stub, subscribeValues, printer)

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
        required=True,
    )

    parser.add_argument(
        "-s",
        "--signal",
        help="Signal to subscribe to",
        required=True,
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
    run(args.url, signals, args.x_api_key, args.access_token)


if __name__ == "__main__":
    main()
