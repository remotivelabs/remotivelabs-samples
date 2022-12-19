import argparse
import math
import time
import remotivelabs.broker.sync as br

from typing import Generator, Iterable


def selectSubscribeIds(
    frame_infos: Iterable[br.common_pb2.FrameInfo],
    match_signals: list[str],
) -> Generator[br.common_pb2.SignalId, None, None]:

    def isMatch(sig: br.common_pb2.SignalInfo) -> bool:
        return sig.id.name in match_signals

    for fi in frame_infos:
        if isMatch(fi.signalInfo):
            yield fi.signalInfo.id

        for child in fi.childInfo:
            if isMatch(child):
                yield child.id


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


def run(
    url: str,
    x_api_key: str,
    namespace_name: str,
    signals: list[str],
) -> None:

    # gRPC connection to RemotiveBroker
    intercept_channel = br.create_channel(url, x_api_key)
    system_stub = br.system_api_pb2_grpc.SystemServiceStub(intercept_channel)
    network_stub = br.network_api_pb2_grpc.NetworkServiceStub(intercept_channel)

    # Get all signals available on broker
    namespace = br.common_pb2.NameSpace(name=namespace_name)
    allFrames = system_stub.ListSignals(namespace)

    # Generate a list of values ready for subscribe
    subscribeValues = list(selectSubscribeIds(allFrames.frame, signals))
    if len(subscribeValues) == 0:
        print("No signals found. Nothing to do...")
        return

    clientIdName = "MySubscriber_{}".format(math.floor(time.monotonic()))
    clientId: br.common_pb2.ClientId = br.common_pb2.ClientId(id=clientIdName)

    subConfig = br.network_api_pb2.SubscriberConfig(
        clientId=clientId,
        signals=br.network_api_pb2.SignalIds(signalId=subscribeValues),
        onChange=False,
    )

    subscripton = network_stub.SubscribeToSignals(subConfig, timeout=None)
    print("Subscribing on signals...")
    try:
        for response in subscripton:
            for signal in response.signal:
                print( "{} {} {}".format(
                    signal.id.name,
                    signal.id.namespace.name, _get_value_str(signal)))
    except KeyboardInterrupt:
        print("Keyboard interrupt received. Closing scheduler.")


def main():
    parser = argparse.ArgumentParser(description="Provide address to Beambroker")

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
        default="offline",
    )

    parser.add_argument(
        "-n",
        "--namespace",
        help="Namespace to select frames on",
        type=str,
        required=True,
    )

    parser.add_argument(
        "-s",
        "--signal",
        help="Signal to subscribe to",
        required=True,
        type=str,
        action="append",
        default=[],
    )

    args = parser.parse_args()
    run(
        args.url,
        args.x_api_key,
        args.namespace,
        args.signal,
    )


if __name__ == "__main__":
    main()
