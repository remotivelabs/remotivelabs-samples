from __future__ import annotations

import argparse
import math
import queue
import sys
import time
from threading import Thread
from typing import Any, Callable, Generator, Optional, Sequence, Tuple

import remotivelabs.broker.sync as br


def subscribe(
    broker: Any,
    client_id: br.common_pb2.ClientId,
    network_stub: br.network_api_pb2_grpc.NetworkServiceStub,
    script: bytes,
    on_subscribe: Callable[[Sequence[br.network_api_pb2.Signal]], None],
    on_change: bool = False,
) -> Tuple[Any, Thread]:
    # pylint: disable=R0913
    sync: queue.Queue[Any] = queue.Queue()
    thread: Thread = Thread(
        target=broker.act_on_scripted_signal,
        args=(
            client_id,
            network_stub,
            script,
            on_change,  # True: only report when signal changes
            on_subscribe,
            sync.put,
        ),
    )
    thread.start()
    # wait for subscription to settle
    subscription = sync.get()
    return subscription, thread


def subscribe_list(signal_creator: Any, signals: list[Tuple[str, str]]) -> Generator[br.common_pb2.SignalId, None, None]:
    for namespace, signal in signals:
        yield signal_creator.signal(signal, namespace)


def _get_value_str(signal: br.network_api_pb2.Signal) -> str:
    if signal.raw != b"":
        return str(signal.raw)
    if signal.HasField("integer"):
        return str(signal.integer)
    if signal.HasField("double"):
        return str(signal.double)
    if signal.HasField("arbitration"):
        return str(signal.arbitration)
    return "empty"


def printer(signals: Sequence[br.network_api_pb2.Signal]) -> None:
    for signal in signals:
        print(f"{signal.id.name} {signal.id.namespace.name} {_get_value_str(signal)}")


def read_script_file(file_path: str) -> bytes:
    try:
        with open(file_path, "rb") as file:
            return file.read()
    except FileNotFoundError:
        print("File not found. Please check your file path.")
        return b""


def create_playback_config(item: dict[str, Any]) -> br.traffic_api_pb2.PlaybackInfo:
    """Creating configuration for playback

    Parameters
    ----------
    item : dict
        Dictionary containing 'path', 'namespace' and 'mode'

    Returns
    -------
    PlaybackInfo
        Object instance of class

    """
    playback_config = br.traffic_api_pb2.PlaybackConfig(
        fileDescription=br.system_api_pb2.FileDescription(path=item["path"]),
        namespace=br.common_pb2.NameSpace(name=item["namespace"]),
    )
    return br.traffic_api_pb2.PlaybackInfo(
        playbackConfig=playback_config,
        playbackMode=br.traffic_api_pb2.PlaybackMode(mode=item["mode"]),
    )


def run(
    url: str,
    script_path: str,
    x_api_key: str,
    access_token: Optional[str] = None,
) -> None:
    # gRPC connection to RemotiveBroker
    intercept_channel = br.create_channel(url, x_api_key, access_token)
    system_stub = br.system_api_pb2_grpc.SystemServiceStub(intercept_channel)
    network_stub = br.network_api_pb2_grpc.NetworkServiceStub(intercept_channel)
    traffic_stub = br.traffic_api_pb2_grpc.TrafficServiceStub(intercept_channel)
    br.check_license(system_stub)
    br.upload_folder(system_stub, "configuration")
    br.reload_configuration(system_stub)

    br.upload_file(
        system_stub,
        "recordings/chassis_bus_recording",
        "recordings/chassis_bus_recording",
    )

    br.upload_file(
        system_stub,
        "recordings/vehicle_bus_recording",
        "recordings/vehicle_bus_recording",
    )

    record_list = [
        {
            "namespace": "VehicleBus",
            "path": "recordings/vehicle_bus_recording",
            "mode": br.traffic_api_pb2.Mode.PLAY,
        },
    ]

    status_record = traffic_stub.PlayTraffic(br.traffic_api_pb2.PlaybackInfos(playbackInfo=list(map(create_playback_config, record_list))))
    print("Recording playback status: ", status_record)

    script = read_script_file(script_path)
    # Generate a list of values ready for subscribe
    # subscribeValues = list(subscribe_list(br.SignalCreator(system_stub), signals))
    if len(script) == 0:
        print("The script file is empty.")
        return

    client_id_name = f"MySubscriber_{math.floor(time.monotonic())}"
    client_id: br.common_pb2.ClientId = br.common_pb2.ClientId(id=client_id_name)

    print("Subscribing on signals...")
    subscription, thread = subscribe(br, client_id, network_stub, script, printer)

    try:
        thread.join()
    except KeyboardInterrupt:
        subscription.cancel()
        print("Keyboard interrupt received. Closing scheduler.")


class ScriptPathArgument(argparse.Action):
    # pylint: disable=R0903
    # pylint: disable=W0222
    def __call__(self, _parser: Any, namespace: argparse.Namespace, value: Any, _option: Any) -> None:  # type: ignore
        print("Script path in use:", value)
        setattr(namespace, "script_path", value)


def main() -> None:
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
        "--script_path",
        help="Path to Lua code",
        type=str,
        action=ScriptPathArgument,
        required=True,
    )

    try:
        args = parser.parse_args()
    except argparse.ArgumentError as e:
        print("Error specifying script to use:", e)
        sys.exit()
    run(args.url, args.script_path, args.x_api_key, args.access_token)


if __name__ == "__main__":
    main()
