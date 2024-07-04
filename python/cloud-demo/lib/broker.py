from __future__ import annotations

import binascii
import queue
from threading import Thread
from typing import Any, Callable

import remotivelabs.broker.sync as br
from typing_extensions import Self


# pylint: disable=R0902
class Broker:
    def __init__(self, url: str, api_key: str | None = None, access_token: str | None = None) -> None:
        self.url = url
        self.api_key = api_key
        self.q: queue.Queue[Any] = queue.Queue()
        """Main function, checking arguments passed to script, setting up stubs, configuration and starting Threads."""
        # Setting up stubs and configuration
        self.intercept_channel = br.create_channel(url, api_key, access_token)

        self.network_stub = br.network_api_pb2_grpc.NetworkServiceStub(self.intercept_channel)
        self.system_stub = br.system_api_pb2_grpc.SystemServiceStub(self.intercept_channel)
        self.traffic_stub = br.traffic_api_pb2_grpc.TrafficServiceStub(self.intercept_channel)
        self.signal_creator = br.SignalCreator(self.system_stub)

    def play(self, namespace: str, path: str) -> None:
        playback_list = [
            {
                "namespace": namespace,
                "path": path,
                "mode": br.traffic_api_pb2.Mode.PLAY,
            }
        ]

        self.traffic_stub.PlayTraffic(
            br.traffic_api_pb2.PlaybackInfos(playbackInfo=list(map(self.__create_playback_config, playback_list)))
        )

    def list_signal_names(self) -> list[str]:
        # Lists available signals
        configuration = self.system_stub.GetConfiguration(br.common_pb2.Empty())

        signal_names = []
        for network_info in configuration.networkInfo:
            res = self.system_stub.ListSignals(network_info.namespace)
            for finfo in res.frame:
                for sinfo in finfo.childInfo:
                    signal_names.append(sinfo.id.name)
        return signal_names

    def subscribe(self, signals: list[br.network_api_pb2.Signal], on_frame: Callable[..., None], changed_values_only: bool = True) -> Any:
        client_id = br.common_pb2.ClientId(id="cloud_demo")

        signals_to_subscribe_on = map(lambda signal: self.signal_creator.signal(signal, "custom_can"), signals)

        Thread(
            target=br.act_on_signal,
            args=(
                client_id,
                self.network_stub,
                signals_to_subscribe_on,
                changed_values_only,  # True: only report when signal changes
                lambda frame: self.__each_signal(frame, on_frame),
                lambda sub: (self.q.put(("cloud_demo", sub))),
            ),
        ).start()
        # Wait for subscription
        _, subscription = self.q.get()
        return subscription

    @classmethod
    def connect(cls, url: str, api_key: str | None = None, access_token: str | None = None) -> Self:
        return Broker(url, api_key, access_token)  # type: ignore

    def __each_signal(self, signals: br.network_api_pb2.Signals, callback: Callable[..., Any]) -> None:
        callback(map(lambda s: {"timestamp_nanos": s.timestamp, "name": s.id.name, "value": self.__get_value(s)}, signals))

    @staticmethod
    def __get_value(signal: br.network_api_pb2.Signal) -> Any:
        if signal.raw != b"":
            return "0x" + binascii.hexlify(signal.raw).decode("ascii")
        if signal.HasField("integer"):
            return signal.integer
        if signal.HasField("double"):
            return signal.double
        if signal.HasField("arbitration"):
            return signal.arbitration

        return "empty"

    @staticmethod
    def __create_playback_config(item: dict[str, Any]) -> br.traffic_api_pb2.PlaybackInfo:
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


Broker.connect = classmethod(Broker.connect)  # type: ignore
