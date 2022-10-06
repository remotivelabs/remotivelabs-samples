import argparse
import binascii
import grpc
import os
import queue
import sys, getopt
import time
import datetime

import remotivelabs.broker.sync as br

from threading import Thread, Timer


signal_creator = None
q = queue.Queue()

speed_signals = []

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


def handle_signals(signals):
    print_signals(signals)
    calculate_average_speed(signals)


def print_signals(signals):
    for signal in signals:
        print(f"{datetime.datetime.fromtimestamp(signal.timestamp / 1000000).strftime('%Y-%m-%d %H:%M:%S')} {signal.id.name} {get_value(signal)}")


def calculate_average_speed(signals):
    for signal in signals:
        if signal.id.name == "Speed":
            speed = list(map(lambda s: get_value(s), signals))
            for s in speed:
                speed_signals.append(s)

    if len(speed_signals) % 10 == 0:
        print("Drive speed avg: ", int(sum(list(speed_signals)) / len(speed_signals)), "max:", max(list(speed_signals)))


def create_playback_config(item):
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
    playbackConfig = br.traffic_api_pb2.PlaybackConfig(
        fileDescription=br.system_api_pb2.FileDescription(path=item["path"]),
        namespace=br.common_pb2.NameSpace(name=item["namespace"]),
    )
    return br.traffic_api_pb2.PlaybackInfo(
        playbackConfig=playbackConfig,
        playbackMode=br.traffic_api_pb2.PlaybackMode(mode=item["mode"]),
    )


def run(url, api_key, signal_names):

    """Main function, checking arguments passed to script, setting up stubs, configuration and starting Threads."""
    # Setting up stubs and configuration
    intercept_channel = br.create_channel(url, api_key)

    network_stub = br.network_api_pb2_grpc.NetworkServiceStub(intercept_channel)
    system_stub = br.system_api_pb2_grpc.SystemServiceStub(intercept_channel)
    traffic_stub = br.traffic_api_pb2_grpc.TrafficServiceStub(intercept_channel)

    playbacklist = [
        {
            "namespace": "custom_can",
            "path": "turning-torso-drivecycle.zip",
            "mode": br.traffic_api_pb2.Mode.PLAY,
        }]
    print("Start playing recording")

    try:
        status = traffic_stub.PlayTraffic(
            br.traffic_api_pb2.PlaybackInfos(
                playbackInfo=list(map(create_playback_config, playbacklist))
            )
        )
    except grpc.RpcError as rpc_error:
        if rpc_error.code() == grpc.StatusCode.CANCELLED:
            pass
        elif rpc_error.code() == grpc.StatusCode.UNAVAILABLE:
            pass
        else:
            print(f"Received unknown RPC error: code={rpc_error.code()} message={rpc_error.details()}")
        exit(0)

    #print("Play recording is in status", status.playbackInfo[0].playbackMode)

    global signal_creator
    signal_creator = br.SignalCreator(system_stub)

    # Lists available signals
    configuration = system_stub.GetConfiguration(br.common_pb2.Empty())
    for networkInfo in configuration.networkInfo:
        print(
            "Available signals in namespace ",
            networkInfo.namespace.name,

        )
        res = system_stub.ListSignals(networkInfo.namespace)
        for finfo in res.frame:
            for sinfo in finfo.childInfo:
                print(f" - {sinfo.id.name}")

    client_id = br.common_pb2.ClientId(id="cloud_demo")

    signals_to_subscribe_on = map(lambda signal: signal_creator.signal(signal, "custom_can"), signal_names)

    Thread(
        target=br.act_on_signal,
        args=(
            client_id,
            network_stub,
            signals_to_subscribe_on,
            True,  # True: only report when signal changes
            lambda signals: handle_signals(signals),
            lambda subscripton: (q.put(("cloud_demo", subscripton))),
        ),
    ).start()


def main(argv):
    parser = argparse.ArgumentParser(description="Provide address to RemotiveBroker")

    parser.add_argument(
        "-url",
        "--url",
        type=str,
        help="URL of the RemotiveBroker",
        required=True,
    )

    parser.add_argument(
        "-api-key",
        "--api-key",
        type=str,
        help="API key is required when accessing brokers running in the cloud",
        required=False,
        default="offline",
    )

    parser.add_argument(
        "-signals",
        "--signals",
        required=False,
        help="Comma separated list of signal names to subscribe on",
        default="Speed",
        type=lambda s: [item for item in s.split(',')]
    )

    args = parser.parse_args()
    run(args.url, args.api_key, args.signals)



if __name__ == "__main__":
    main(sys.argv[1:])
