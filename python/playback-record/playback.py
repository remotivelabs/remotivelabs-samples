from __future__ import annotations

import argparse
import signal as sig
import time
from threading import Event
from typing import Any, Optional, Sequence

import grpc
import remotivelabs.broker.sync as br

exit_event = Event()

playbacklist = [
    {
        "namespace": "custom_can",
        "path": "recordings/candump_uploaded.log",
        "mode": br.traffic_api_pb2.Mode.PLAY,
    },
    {
        "namespace": "ecu_A",
        "path": "recordings/candump.log",
        "mode": br.traffic_api_pb2.Mode.PLAY,
    },
    {
        "namespace": "ecu_C",
        "path": "recordings/candump_.log",
        "mode": br.traffic_api_pb2.Mode.PLAY,
    },
]


def read_signal(stub: br.network_api_pb2_grpc.NetworkServiceStub, signal: br.common_pb2.SignalId) -> br.network_api_pb2.Signals:
    """Read signals

    Parameters
    ----------
    stub : NetworkServiceStub
        Object instance of class
    signal : SignalId
        Object instance of class

    Returns
    -------
    Signal
        Object instance of class

    """
    read_info = br.network_api_pb2.SignalIds(signalId=[signal])
    return stub.ReadSignals(read_info)


def ecu_b_read(stub: br.network_api_pb2_grpc.NetworkServiceStub, pause: int) -> None:
    """Read some value published by ecu_A

    Parameters
    ----------
    stub : NetworkServiceStub
        Object instance of class
    pause : int
        Amount of time to pause, in seconds

    """
    while not exit_event.is_set():
        namespace = "custom_can"
        # client_id = br.common_pb2.ClientId(id="id_ecu_B")

        # Read value 'SteerAngle'
        steer_angle = br.common_pb2.SignalId(name="SteerAngle", namespace=br.common_pb2.NameSpace(name=namespace))
        response = read_signal(stub, steer_angle)
        print("ecu_B, (read) SteerAngle is ", response.signal[0].double)

        time.sleep(pause)


def ecu_b_subscribe_(stub: br.network_api_pb2_grpc.NetworkServiceStub) -> None:
    """Subscribe to a value published by ecu_A and output value

    Parameters
    ----------
    stub : NetworkServiceStub
        Object instance of class

    """

    namespace = "custom_can"
    client_id = br.common_pb2.ClientId(id="id_ecu_B")

    # Subscribe to value 'SteerAngle'
    steer_angle = br.common_pb2.SignalId(name="SteerAngle", namespace=br.common_pb2.NameSpace(name=namespace))
    sub_info = br.network_api_pb2.SubscriberConfig(
        clientId=client_id,
        signals=br.network_api_pb2.SignalIds(signalId=[steer_angle]),
        onChange=True,
    )

    # Output subscribed signal
    try:
        for subs_counter in stub.SubscribeToSignals(sub_info):
            # For clean exit when stopping script
            if exit_event.is_set():
                break
            print("ecu_B, (subscribe) SteerAngle is ", subs_counter.signal[0])
    except grpc.RpcError as err:
        print(err)


def read_on_timer(stub: br.network_api_pb2_grpc.NetworkServiceStub, signals: Sequence[br.common_pb2.SignalId], pause: int) -> None:
    """Simple reading with timer, logs on purpose tabbed with double space

    Parameters
    ----------
    stub : NetworkServiceStub
        Object instance of class
    signals : SignalId
        Object instance of class
    pause : int
        Amount of time to pause, in seconds

    """
    while not exit_event.is_set():
        read_info = br.network_api_pb2.SignalIds(signalId=signals)
        try:
            response = stub.ReadSignals(read_info)
            for signal in response.signal:
                print("  read_on_timer " + signal.id.name + " value " + str(signal.double))
        except grpc.RpcError as err:
            print(err)

        time.sleep(pause)


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


def stop_playback(url: str, x_api_key: str | None, access_token: str | None) -> None:
    """Stop ongoing playback"""
    intercept_channel = br.create_channel(url, x_api_key, access_token)
    traffic_stub = br.traffic_api_pb2_grpc.TrafficServiceStub(intercept_channel)
    for playback in playbacklist:
        playback["mode"] = br.traffic_api_pb2.Mode.STOP

    status = traffic_stub.PlayTraffic(br.traffic_api_pb2.PlaybackInfos(playbackInfo=list(map(create_playback_config, playbacklist))))
    print("Stop traffic status is ", status)


def exit_handler(url: str, x_api_key: str | None, access_token: str | None) -> None:
    exit_event.set()
    time.sleep(0.5)
    stop_playback(url, x_api_key, access_token)


def main() -> None:
    parser = argparse.ArgumentParser(description="Provide address to Beambroker")
    parser.add_argument(
        "-url",
        "--url",
        help="URL of the RemotiveBroker",
        type=str,
        required=False,
        default="http://127.0.0.1:50051",
    )

    parser.add_argument(
        "-x_api_key",
        "--x_api_key",
        type=str,
        help="API key is required when accessing brokers running in the cloud",
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
        "-c",
        "--configure",
        type=str,
        metavar="DIRECTORY",
        help="Configure broker with specified configuration directory",
        default="configuration_custom_udp",
    )

    args = parser.parse_args()

    run(args.url, args.configure, args.x_api_key, args.access_token)


def run(url: str, configure: str, x_api_key: Optional[str] = None, access_token: Optional[str] = None) -> None:
    # To do a clean exit of the script on CTRL+C
    sig.signal(sig.SIGINT, lambda signum, frame: exit_handler(url, x_api_key, access_token))

    # Setting up stubs and configuration
    intercept_channel = br.create_channel(url, x_api_key, access_token)
    # network_stub = br.network_api_pb2_grpc.NetworkServiceStub(intercept_channel)
    traffic_stub = br.traffic_api_pb2_grpc.TrafficServiceStub(intercept_channel)
    system_stub = br.system_api_pb2_grpc.SystemServiceStub(intercept_channel)
    br.check_license(system_stub)

    br.upload_folder(system_stub, configure)
    br.reload_configuration(system_stub)
    # Give us some time to see it all went according to plan
    time.sleep(1)

    # Lists available signals
    configuration = system_stub.GetConfiguration(br.common_pb2.Empty())
    for network_info in configuration.networkInfo:
        print(
            "signals in namespace ",
            network_info.namespace.name,
            system_stub.ListSignals(network_info.namespace),
        )

    # Optonally start threads
    # ecu_B_thread_subscribe = Thread(target=ecu_B_subscribe_, args=(network_stub,))
    # ecu_B_thread_subscribe.start()

    # ecu_B_thread_read = Thread(
    #     target=ecu_B_read,
    #     args=(
    #         network_stub,
    #         1,
    #     ),
    # )
    # ecu_B_thread_read.start()

    br.upload_file(
        system_stub,
        "recordings/traffic.log",
        "recordings/candump_uploaded.log",
    )

    recordlist = [
        {
            "namespace": "custom_can",
            "path": "recordings/candump_uploaded_recorded",
            "mode": br.traffic_api_pb2.Mode.RECORD,
        },
    ]
    status_record = traffic_stub.PlayTraffic(br.traffic_api_pb2.PlaybackInfos(playbackInfo=list(map(create_playback_config, recordlist))))
    print("record traffic result is ", status_record)

    # expect candump_.log does not exist, thus error string will be returned
    status = traffic_stub.PlayTraffic(br.traffic_api_pb2.PlaybackInfos(playbackInfo=list(map(create_playback_config, playbacklist))))
    print("play traffic result is ", status)

    time.sleep(5)

    recordlist = [
        {
            "namespace": "custom_can",
            "path": "recordings/candump_uploaded_recorded",
            "mode": br.traffic_api_pb2.Mode.STOP,
        },
    ]
    status_record = traffic_stub.PlayTraffic(br.traffic_api_pb2.PlaybackInfos(playbackInfo=list(map(create_playback_config, recordlist))))

    # now stop recording and download the recorded file
    br.download_file(
        system_stub,
        "recordings/candump_uploaded_recorded",
        "candump_uploaded_recorded_downloaded",
    )
    print("file is now downloaded")

    # ecu_B_thread_subscribe  = Thread(target = ecu_B_subscribe_, args = (network_stub,))
    # ecu_B_thread_subscribe.start()

    # read_signals = [br.common_pb2.SignalId(name="SteerAngle", namespace=br.common_pb2.NameSpace(name = "custom_can")),
    #                 br.common_pb2.SignalId(name="SteerAngleSpeed", namespace=br.common_pb2.NameSpace(name = "custom_can"))]
    # ecu_read_on_timer  = Thread(target = read_on_timer, args = (network_stub, read_signals, 2))
    # ecu_read_on_timer.start()


if __name__ == "__main__":
    main()
