# pylint: disable=W0621

import remotivelabs.broker.sync as br

import pytest

# Server address:
_SERVER_URL = "https://personal-5z42sn9ui4-demo-uo7acw3qiq-ez.a.run.app"
_SERVER_APIKEY = "7925BA43-9FB03240-FF17B0DE-BA0CC228"


class Broker:  # pylint: disable=R0903
    def __init__(self) -> None:
        self.channel = br.create_channel(_SERVER_URL, _SERVER_APIKEY)
        self.network_stub = br.network_api_pb2_grpc.NetworkServiceStub(self.channel)
        self.system_stub = br.system_api_pb2_grpc.SystemServiceStub(self.channel)
        br.upload_folder(self.system_stub, "configuration_test")
        br.reload_configuration(self.system_stub)


# Setup broker with predefined settings
@pytest.fixture
def broker() -> Broker:
    return Broker()


def test_check_license(broker: Broker) -> None:
    """Check valid license"""
    br.check_license(broker.system_stub)


def test_server_info(broker: Broker) -> None:
    """Validate server information"""

    conf = broker.system_stub.GetConfiguration(br.common_pb2.Empty())

    # Major version should be 1
    assert conf.serverVersion.startswith("v1.")

    # Should have 1 namespace
    assert len(conf.networkInfo) == 1
    assert conf.networkInfo[0].namespace.name == "mynamespace"


def test_list_signals(broker: Broker) -> None:
    """List and valitade signals."""

    ns = br.common_pb2.NameSpace(name="mynamespace")
    signals = broker.system_stub.ListSignals(ns)
    assert len(signals.frame) == 1


def test_meta_fields(broker: Broker) -> None:
    """Validate signal meta information."""

    sc = br.SignalCreator(broker.system_stub)
    meta_signal = sc.get_meta("mysignal1", "mynamespace")
    frame = sc.frame_by_signal("mysignal1", "mynamespace")
    assert frame.name == "myframe1"
    meta_frame = sc.get_meta(frame.name, "mynamespace")

    assert meta_signal.getDescription() == "My signal 1"
    assert meta_signal.getMax() == 255.0
    assert meta_signal.getMin() == 0
    assert meta_signal.getUnit() == "My unit"
    assert meta_signal.getSize() == 8
    assert meta_signal.getIsRaw() is False
    assert meta_frame.getIsRaw() is True
    assert meta_signal.getFactor() == 1.0
    assert meta_signal.getOffset() == 0.0
    assert meta_signal.getSenders() == ["NONE"]
    assert meta_frame.getSenders() == ["NONE"]
    assert meta_signal.getReceivers() == ["NONE1", "NONE2"]
