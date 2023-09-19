#include "connection.h"
#include <unistd.h>
#include <chrono>
#include <ctime>
#include <array>
#include <math.h>
#include <iostream>
#include <thread>

using namespace grpc;
using namespace base;

GrpcConnection::GrpcConnection(std::shared_ptr<Channel> channel)
    : stub(NetworkService::NewStub(channel))
{
  source = std::make_unique<ClientId>();
  name_space = std::make_unique<NameSpace>();
  source->set_id("my_unique_client_id");
  name_space->set_name("vss");
}

void GrpcConnection::subscriber()
{
  auto signals = new SignalIds();

  // add any number of signals...
  {
    auto handle = signals->add_signalid();
    handle->set_allocated_name(new std::string("Vehicle.Chassis.SteeringWheel.Angle"));
    handle->set_allocated_namespace_(new NameSpace(*name_space));
  }

  {
    auto handle = signals->add_signalid();
    handle->set_allocated_name(new std::string("Vehicle.Speed"));
    handle->set_allocated_namespace_(new NameSpace(*name_space));
  }

  SubscriberConfig sub_info;
  sub_info.set_allocated_clientid(new ClientId(*source));
  sub_info.set_allocated_signals(signals);

  ClientContext ctx;
  Empty empty;

  std::cout << "Subscribing" << std::endl;

  Signals signals_returned;

  std::unique_ptr<ClientReader<Signals>> reader(
      stub->SubscribeToSignals(&ctx, sub_info));
  while (reader->Read(&signals_returned))
  {
    for (int i = 0; i < signals_returned.signal_size(); i++)
    {
      auto name = signals_returned.signal(i).id().name();
      std::cout << name << std::endl;

      auto value_d = signals_returned.signal(i).double_();
      std::cout << value_d << std::endl;

      auto value_i = signals_returned.signal(i).integer();
      std::cout << value_i << std::endl;
    }
  }
  Status status = reader->Finish();

  std::cout << "Subscribing end. Subscribing on invalid signals or stream stopped." << std::endl;
}

void GrpcConnection::publisher()
{

  // TODO we could use startvalue here as default
  // https://github.com/remotivelabs/remotivelabs-apis/blob/main/proto/common.proto#L34
  auto start_value = 12;

  auto N = 10;
  for (auto i = 0; i < N; i = ((i + 1) % N))
  {
    // std::cout << i << std::endl;
    auto signals = new Signals();
    {
      auto signal_id = new SignalId();
      signal_id->set_allocated_name(new std::string("SteeringAngle129"));
      signal_id->set_allocated_namespace_(new NameSpace(*name_space));
      auto handle = signals->add_signal();
      handle->set_allocated_id(signal_id);
      handle->set_integer(start_value + i);
    }
    {
      // append any number of signals here! (duplicate above code)
    }

    PublisherConfig pub_info;
    pub_info.set_allocated_clientid(new ClientId(*source));
    pub_info.set_allocated_signals(signals);
    pub_info.set_frequency(0);
    ClientContext ctx;
    Empty empty;
    stub->PublishSignals(&ctx, pub_info, &empty);

    // TODO we should derive this period from proto buffer,
    // https://github.com/remotivelabs/remotivelabs-apis/blob/main/proto/common.proto#L33
    usleep(30);
  }
}

class MyCustomAuthenticator : public grpc::MetadataCredentialsPlugin
{
public:
  MyCustomAuthenticator(const grpc::string &ticket) : ticket_(ticket) {}

  grpc::Status GetMetadata(
      grpc::string_ref service_url, grpc::string_ref method_name,
      const grpc::AuthContext &channel_auth_context,
      std::multimap<grpc::string, grpc::string> *metadata) override
  {
    metadata->insert(std::make_pair("x-api-key", ticket_));
    return grpc::Status::OK;
  }

private:
  grpc::string ticket_;
};

const char CUSTOM_CERTIFICATE[] = R"(
-----BEGIN CERTIFICATE-----
MIIDdTCCAl2gAwIBAgILBAAAAAABFUtaw5QwDQYJKoZIhvcNAQEFBQAwVzELMAkG
A1UEBhMCQkUxGTAXBgNVBAoTEEdsb2JhbFNpZ24gbnYtc2ExEDAOBgNVBAsTB1Jv
b3QgQ0ExGzAZBgNVBAMTEkdsb2JhbFNpZ24gUm9vdCBDQTAeFw05ODA5MDExMjAw
MDBaFw0yODAxMjgxMjAwMDBaMFcxCzAJBgNVBAYTAkJFMRkwFwYDVQQKExBHbG9i
YWxTaWduIG52LXNhMRAwDgYDVQQLEwdSb290IENBMRswGQYDVQQDExJHbG9iYWxT
aWduIFJvb3QgQ0EwggEiMA0GCSqGSIb3DQEBAQUAA4IBDwAwggEKAoIBAQDaDuaZ
jc6j40+Kfvvxi4Mla+pIH/EqsLmVEQS98GPR4mdmzxzdzxtIK+6NiY6arymAZavp
xy0Sy6scTHAHoT0KMM0VjU/43dSMUBUc71DuxC73/OlS8pF94G3VNTCOXkNz8kHp
1Wrjsok6Vjk4bwY8iGlbKk3Fp1S4bInMm/k8yuX9ifUSPJJ4ltbcdG6TRGHRjcdG
snUOhugZitVtbNV4FpWi6cgKOOvyJBNPc1STE4U6G7weNLWLBYy5d4ux2x8gkasJ
U26Qzns3dLlwR5EiUWMWea6xrkEmCMgZK9FGqkjWZCrXgzT/LCrBbBlDSgeF59N8
9iFo7+ryUp9/k5DPAgMBAAGjQjBAMA4GA1UdDwEB/wQEAwIBBjAPBgNVHRMBAf8E
BTADAQH/MB0GA1UdDgQWBBRge2YaRQ2XyolQL30EzTSo//z9SzANBgkqhkiG9w0B
AQUFAAOCAQEA1nPnfE920I2/7LqivjTFKDK1fPxsnCwrvQmeU79rXqoRSLblCKOz
yj1hTdNGCbM+w6DjY1Ub8rrvrTnhQ7k4o+YviiY776BQVvnGCv04zcQLcFGUl5gE
38NflNUVyRRBnMRddWQVDf9VMOyGj/8N7yy5Y0b2qvzfvGn9LhJIZJrglfCm7ymP
AbEVtQwdpf5pLGkkeB6zpxxxYu7KyJesF12KwvhHhm4qxFYxldBniYUr+WymXUad
DKqC5JlR3XC321Y9YeRq4VzW9v493kHMB65jUr9TU/Qr6cf9tveCX4XSQRjbgbME
HMUfpIBvFSDJ3gyICh3WZlXi/EjJKSZp4A==
-----END CERTIFICATE-----
)";

int main(int argc, char *argv[])
{
  // use local certificate
  grpc::SslCredentialsOptions sslops;
  sslops.pem_root_certs = CUSTOM_CERTIFICATE;

  auto channel_creds_ = ::grpc::SslCredentials(sslops);

  // or use certificate from host
  // auto channel_creds_ = ::grpc::SslCredentials(::grpc::SslCredentialsOptions());

  auto call_creds = grpc::MetadataCredentialsFromPlugin(
      std::unique_ptr<grpc::MetadataCredentialsPlugin>(
          new MyCustomAuthenticator(argv[2])));

  auto compsited_creds = ::grpc::CompositeChannelCredentials(channel_creds_, call_creds);

  grpc::ChannelArguments cargs;

  auto connection = new GrpcConnection(CreateChannel(argv[1], compsited_creds));

  std::thread subscriber(&GrpcConnection::subscriber, connection);
  subscriber.join();

  // std::thread publisher(&GrpcConnection::publisher, connection);
  // publisher.join();

  return 0;
}
