// Generated by the gRPC C++ plugin.
// If you make any local change, they will be lost.
// source: network_api.proto

#include "network_api.pb.h"
#include "network_api.grpc.pb.h"

#include <functional>
#include <grpcpp/impl/codegen/async_stream.h>
#include <grpcpp/impl/codegen/async_unary_call.h>
#include <grpcpp/impl/codegen/channel_interface.h>
#include <grpcpp/impl/codegen/client_unary_call.h>
#include <grpcpp/impl/codegen/client_callback.h>
#include <grpcpp/impl/codegen/method_handler_impl.h>
#include <grpcpp/impl/codegen/rpc_service_method.h>
#include <grpcpp/impl/codegen/service_type.h>
#include <grpcpp/impl/codegen/sync_stream.h>
namespace base {

static const char* NetworkService_method_names[] = {
  "/base.NetworkService/SubscribeToSignals",
  "/base.NetworkService/PublishSignals",
  "/base.NetworkService/ReadSignals",
};

std::unique_ptr< NetworkService::Stub> NetworkService::NewStub(const std::shared_ptr< ::grpc::ChannelInterface>& channel, const ::grpc::StubOptions& options) {
  (void)options;
  std::unique_ptr< NetworkService::Stub> stub(new NetworkService::Stub(channel));
  return stub;
}

NetworkService::Stub::Stub(const std::shared_ptr< ::grpc::ChannelInterface>& channel)
  : channel_(channel), rpcmethod_SubscribeToSignals_(NetworkService_method_names[0], ::grpc::internal::RpcMethod::SERVER_STREAMING, channel)
  , rpcmethod_PublishSignals_(NetworkService_method_names[1], ::grpc::internal::RpcMethod::NORMAL_RPC, channel)
  , rpcmethod_ReadSignals_(NetworkService_method_names[2], ::grpc::internal::RpcMethod::NORMAL_RPC, channel)
  {}

::grpc::ClientReader< ::base::Signals>* NetworkService::Stub::SubscribeToSignalsRaw(::grpc::ClientContext* context, const ::base::SubscriberConfig& request) {
  return ::grpc::internal::ClientReaderFactory< ::base::Signals>::Create(channel_.get(), rpcmethod_SubscribeToSignals_, context, request);
}

::grpc::ClientAsyncReader< ::base::Signals>* NetworkService::Stub::AsyncSubscribeToSignalsRaw(::grpc::ClientContext* context, const ::base::SubscriberConfig& request, ::grpc::CompletionQueue* cq, void* tag) {
  return ::grpc::internal::ClientAsyncReaderFactory< ::base::Signals>::Create(channel_.get(), cq, rpcmethod_SubscribeToSignals_, context, request, true, tag);
}

::grpc::ClientAsyncReader< ::base::Signals>* NetworkService::Stub::PrepareAsyncSubscribeToSignalsRaw(::grpc::ClientContext* context, const ::base::SubscriberConfig& request, ::grpc::CompletionQueue* cq) {
  return ::grpc::internal::ClientAsyncReaderFactory< ::base::Signals>::Create(channel_.get(), cq, rpcmethod_SubscribeToSignals_, context, request, false, nullptr);
}

::grpc::Status NetworkService::Stub::PublishSignals(::grpc::ClientContext* context, const ::base::PublisherConfig& request, ::base::Empty* response) {
  return ::grpc::internal::BlockingUnaryCall(channel_.get(), rpcmethod_PublishSignals_, context, request, response);
}

void NetworkService::Stub::experimental_async::PublishSignals(::grpc::ClientContext* context, const ::base::PublisherConfig* request, ::base::Empty* response, std::function<void(::grpc::Status)> f) {
  return ::grpc::internal::CallbackUnaryCall(stub_->channel_.get(), stub_->rpcmethod_PublishSignals_, context, request, response, std::move(f));
}

::grpc::ClientAsyncResponseReader< ::base::Empty>* NetworkService::Stub::AsyncPublishSignalsRaw(::grpc::ClientContext* context, const ::base::PublisherConfig& request, ::grpc::CompletionQueue* cq) {
  return ::grpc::internal::ClientAsyncResponseReaderFactory< ::base::Empty>::Create(channel_.get(), cq, rpcmethod_PublishSignals_, context, request, true);
}

::grpc::ClientAsyncResponseReader< ::base::Empty>* NetworkService::Stub::PrepareAsyncPublishSignalsRaw(::grpc::ClientContext* context, const ::base::PublisherConfig& request, ::grpc::CompletionQueue* cq) {
  return ::grpc::internal::ClientAsyncResponseReaderFactory< ::base::Empty>::Create(channel_.get(), cq, rpcmethod_PublishSignals_, context, request, false);
}

::grpc::Status NetworkService::Stub::ReadSignals(::grpc::ClientContext* context, const ::base::SignalIds& request, ::base::Signals* response) {
  return ::grpc::internal::BlockingUnaryCall(channel_.get(), rpcmethod_ReadSignals_, context, request, response);
}

void NetworkService::Stub::experimental_async::ReadSignals(::grpc::ClientContext* context, const ::base::SignalIds* request, ::base::Signals* response, std::function<void(::grpc::Status)> f) {
  return ::grpc::internal::CallbackUnaryCall(stub_->channel_.get(), stub_->rpcmethod_ReadSignals_, context, request, response, std::move(f));
}

::grpc::ClientAsyncResponseReader< ::base::Signals>* NetworkService::Stub::AsyncReadSignalsRaw(::grpc::ClientContext* context, const ::base::SignalIds& request, ::grpc::CompletionQueue* cq) {
  return ::grpc::internal::ClientAsyncResponseReaderFactory< ::base::Signals>::Create(channel_.get(), cq, rpcmethod_ReadSignals_, context, request, true);
}

::grpc::ClientAsyncResponseReader< ::base::Signals>* NetworkService::Stub::PrepareAsyncReadSignalsRaw(::grpc::ClientContext* context, const ::base::SignalIds& request, ::grpc::CompletionQueue* cq) {
  return ::grpc::internal::ClientAsyncResponseReaderFactory< ::base::Signals>::Create(channel_.get(), cq, rpcmethod_ReadSignals_, context, request, false);
}

NetworkService::Service::Service() {
  AddMethod(new ::grpc::internal::RpcServiceMethod(
      NetworkService_method_names[0],
      ::grpc::internal::RpcMethod::SERVER_STREAMING,
      new ::grpc::internal::ServerStreamingHandler< NetworkService::Service, ::base::SubscriberConfig, ::base::Signals>(
          std::mem_fn(&NetworkService::Service::SubscribeToSignals), this)));
  AddMethod(new ::grpc::internal::RpcServiceMethod(
      NetworkService_method_names[1],
      ::grpc::internal::RpcMethod::NORMAL_RPC,
      new ::grpc::internal::RpcMethodHandler< NetworkService::Service, ::base::PublisherConfig, ::base::Empty>(
          std::mem_fn(&NetworkService::Service::PublishSignals), this)));
  AddMethod(new ::grpc::internal::RpcServiceMethod(
      NetworkService_method_names[2],
      ::grpc::internal::RpcMethod::NORMAL_RPC,
      new ::grpc::internal::RpcMethodHandler< NetworkService::Service, ::base::SignalIds, ::base::Signals>(
          std::mem_fn(&NetworkService::Service::ReadSignals), this)));
}

NetworkService::Service::~Service() {
}

::grpc::Status NetworkService::Service::SubscribeToSignals(::grpc::ServerContext* context, const ::base::SubscriberConfig* request, ::grpc::ServerWriter< ::base::Signals>* writer) {
  (void) context;
  (void) request;
  (void) writer;
  return ::grpc::Status(::grpc::StatusCode::UNIMPLEMENTED, "");
}

::grpc::Status NetworkService::Service::PublishSignals(::grpc::ServerContext* context, const ::base::PublisherConfig* request, ::base::Empty* response) {
  (void) context;
  (void) request;
  (void) response;
  return ::grpc::Status(::grpc::StatusCode::UNIMPLEMENTED, "");
}

::grpc::Status NetworkService::Service::ReadSignals(::grpc::ServerContext* context, const ::base::SignalIds* request, ::base::Signals* response) {
  (void) context;
  (void) request;
  (void) response;
  return ::grpc::Status(::grpc::StatusCode::UNIMPLEMENTED, "");
}


}  // namespace base
