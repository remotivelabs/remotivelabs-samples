import argparse
import math
import time
import remotivelabs.broker.sync as br
import queue
from threading import Thread, Timer
import grpc

from typing import Callable, Generator, Iterable, Optional, TypeVar, Sequence, Tuple


def subscribe(
    broker,
    client_id: br.common_pb2.ClientId,
    network_stub: br.network_api_pb2_grpc.NetworkServiceStub,
    mapped_code: str,
    on_subscribe: Callable[[Sequence[br.network_api_pb2.Signal]], None],
    on_change: bool = False,
) -> grpc.RpcContext:
    sync = queue.Queue()
    thread = Thread(
        target=broker.act_on_mapped_signal,
        args=(
            client_id,
            network_stub,
            mapped_code,
            on_change,  # True: only report when signal changes
            on_subscribe,
            lambda subscription: (sync.put(subscription)),
        ),
    )
    thread.start()
    # wait for subscription to settle
    subscription = sync.get()
    return subscription, thread


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


def read_mapping_code_file(file_path: str) -> str:
    try:
        with open(file_path, "r") as file:
            return file.read()
    except FileNotFoundError:
        print("File not found. Please check your file path.")
        return ""


def run(
    url: str,
    mapping_code_path: str,
    x_api_key:  Optional[str] = None,
    access_token: Optional[str] = None
) -> None:
    # gRPC connection to RemotiveBroker
    intercept_channel = br.create_channel(url, x_api_key, access_token)
    system_stub = br.system_api_pb2_grpc.SystemServiceStub(intercept_channel)
    network_stub = br.network_api_pb2_grpc.NetworkServiceStub(intercept_channel)
    br.check_license(system_stub)

    mapped_code = read_mapping_code_file(mapping_code_path)
    # Generate a list of values ready for subscribe
    # subscribeValues = list(subscribe_list(br.SignalCreator(system_stub), signals))
    if len(mapped_code) == 0:
        print("The mapping code file is empty.")
        return

    client_id_name = "MySubscriber_{}".format(math.floor(time.monotonic()))
    client_id: br.common_pb2.ClientId = br.common_pb2.ClientId(id=client_id_name)

    print("Subscribing on signals...")
    subscription, thread = subscribe(br, client_id, network_stub, mapped_code, printer)

    try:
        thread.join()
    except KeyboardInterrupt:
        subscription.cancel()
        print("Keyboard interrupt received. Closing scheduler.")


class MappingCodePathArgument(argparse.Action):
    def __call__(self, _parser, namespace, value, _option):
        print("Mapping code path in use:", value)
        setattr(namespace, "mapping_code_path", value)


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
        "-p",
        "--mapping_code_path",
        help="Path to Lua mapping code",
        type=str,
        action=MappingCodePathArgument,
        required=True,
    )

    try:
        args = parser.parse_args()
    except Exception as e:
        return print("Error specifying mapping code to use:", e)
    run(args.url, args.mapping_code_path, args.x_api_key,args.access_token )


if __name__ == "__main__":
    main()
