import binascii
import queue
from threading import Thread
import remotivelabs.broker.sync as br


class Broker:

    def __init__(self, url, api_key):
        self.url = url
        self.api_key = api_key
        self.q = queue.Queue()
        """Main function, checking arguments passed to script, setting up stubs, configuration and starting Threads."""
        # Setting up stubs and configuration
        self.intercept_channel = br.create_channel(url, api_key)

        self.network_stub = br.network_api_pb2_grpc.NetworkServiceStub(self.intercept_channel)
        self.system_stub = br.system_api_pb2_grpc.SystemServiceStub(self.intercept_channel)
        self.traffic_stub = br.traffic_api_pb2_grpc.TrafficServiceStub(self.intercept_channel)
        self.signal_creator = br.SignalCreator(self.system_stub)

    def play(self, namespace: str, path: str):
        playback_list = [
            {
                "namespace": namespace,
                "path": path,
                "mode": br.traffic_api_pb2.Mode.PLAY,
            }]

        status = self.traffic_stub.PlayTraffic(
            br.traffic_api_pb2.PlaybackInfos(
                playbackInfo=list(map(self.__create_playback_config, playback_list))
            )
        )

    def list_signal_names(self):
        # Lists available signals
        configuration = self.system_stub.GetConfiguration(br.common_pb2.Empty())

        signal_names = []
        for networkInfo in configuration.networkInfo:
            res = self.system_stub.ListSignals(networkInfo.namespace)
            for finfo in res.frame:
                for sinfo in finfo.childInfo:
                    signal_names.append(sinfo.id.name)
        return signal_names

    def subscribe(self, signals: list, on_frame, changed_values_only: bool = True):
        client_id = br.common_pb2.ClientId(id="cloud_demo")

        signals_to_subscribe_on = \
            map(lambda signal: self.signal_creator.signal(signal, "custom_can"), signals)

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
        ecu, subscription = self.q.get()
        return subscription

    @classmethod
    def connect(cls, url, api_key):
        return Broker(url, api_key)

    def __each_signal(self, signals, callback):
        callback(map(lambda s: {
            'timestamp_nanos': s.timestamp,
            'name': s.id.name,
            'value': self.__get_value(s)
        }, signals))

    @staticmethod
    def __get_value(signal):
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

    @staticmethod
    def __create_playback_config(item):
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


Broker.connect = classmethod(Broker.connect)
