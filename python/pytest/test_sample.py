import pytest
import remotivelabs.broker.sync as br

# Server address:
_SERVER_URL = 'http://127.0.0.1:50051'
_SERVER_APIKEY = None


class Broker:
    def __init__(self):
        self.channel = br.create_channel(_SERVER_URL, _SERVER_APIKEY)
        self.network_stub = br.network_api_pb2_grpc.NetworkServiceStub(self.channel)
        self.system_stub = br.system_api_pb2_grpc.SystemServiceStub(self.channel)
        br.upload_folder(self.system_stub, "configuration_test")
        br.reload_configuration(self.system_stub)


# Setup broker with predefined settings
@pytest.fixture
def broker():
    return Broker()

def test_check_license(broker):
    """Check valid license"""
    br.check_license(broker.system_stub)

def test_serverInfo(broker):
    """Validate server information"""

    conf = broker.system_stub.GetConfiguration(br.common_pb2.Empty())

    # Major version should be 1
    assert conf.serverVersion.startswith('v1.')

    # Should have 1 namespace
    assert len(conf.networkInfo) == 1
    assert conf.networkInfo[0].namespace.name == "mynamespace"

def test_listSignals(broker):
    """List and valitade signals."""

    ns = br.common_pb2.NameSpace(name='mynamespace')
    signals = broker.system_stub.ListSignals(ns)
    assert len(signals.frame) == 1

def test_metaFields(broker):
    """Validate signal meta information."""

    sc = br.SignalCreator(broker.system_stub)
    metaSignal = sc.get_meta('mysignal1', 'mynamespace')
    frame = sc.frame_by_signal('mysignal1', 'mynamespace')
    assert frame.name == 'myframe1'
    metaFrame = sc.get_meta(frame.name, 'mynamespace')

    assert metaSignal.getDescription() == "My signal 1"
    assert metaSignal.getMax() == 255.0
    assert metaSignal.getMin() == 0
    assert metaSignal.getUnit() == "My unit"
    assert metaSignal.getSize() == 8
    assert metaSignal.getIsRaw() == False
    assert metaFrame.getIsRaw() == True
    assert metaSignal.getFactor() == 1.0
    assert metaSignal.getOffset() == 0.0
    assert metaSignal.getSenders() == ['NONE']
    assert metaFrame.getSenders() == ['NONE']
    assert metaSignal.getReceivers() == ['NONE1', 'NONE2']

