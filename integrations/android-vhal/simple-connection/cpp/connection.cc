// hdasari@volvocars.com

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
  name_space->set_name("ChassiBus");
}

void GrpcConnection::subscriber()
{
  auto signals = new SignalIds();

  // add any number of signals...
  {
    auto handle = signals->add_signalid();
    handle->set_allocated_name(new std::string("SteeringAngle129"));
    handle->set_allocated_namespace_(new NameSpace(*name_space));
  }

  {
    auto handle = signals->add_signalid();
    handle->set_allocated_name(new std::string("DI_uiSpeed"));
    handle->set_allocated_namespace_(new NameSpace(*name_space));
  }

  SubscriberConfig sub_info;
  sub_info.set_allocated_clientid(new ClientId(*source));
  sub_info.set_allocated_signals(signals);

  ClientContext ctx;
  Empty empty;

  std::cout << "Subscribing" << std::endl;

  Signals signalsreturned;

  std::unique_ptr<ClientReader<Signals>> reader(
      stub->SubscribeToSignals(&ctx, sub_info));
  while (reader->Read(&signalsreturned))
  {
    for (int i = 0; i < signalsreturned.signal_size(); i++)
    {
      auto name = signalsreturned.signal(i).id().name();
      std::cout << name << std::endl;

      auto value_d = signalsreturned.signal(i).double_();
      std::cout << value_d << std::endl;

      auto value_i = signalsreturned.signal(i).integer();
      std::cout << value_i << std::endl;
    }
  }
  Status status = reader->Finish();

  std::cout << "Subscribing done" << std::endl;
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

int main(int argc, char *argv[])
{
  auto channel_creds_ = ::grpc::SslCredentials(::grpc::SslCredentialsOptions());

  auto call_creds = grpc::MetadataCredentialsFromPlugin(
      std::unique_ptr<grpc::MetadataCredentialsPlugin>(
          new MyCustomAuthenticator(argv[2])));

  auto compsited_creds = ::grpc::CompositeChannelCredentials(channel_creds_, call_creds);

  grpc::ChannelArguments cargs;

  auto subscriber = new GrpcConnection(CreateCustomChannel(argv[1], compsited_creds, cargs));

  std::thread subscriber_thread(&GrpcConnection::subscriber, subscriber);
  subscriber_thread.join();

  return 0;
}
