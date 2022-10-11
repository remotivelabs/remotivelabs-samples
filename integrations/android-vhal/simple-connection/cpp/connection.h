#include "grpc++/grpc++.h"
#include "proto_files/network_api.grpc.pb.h"

class GrpcConnection
{
public:
    GrpcConnection() = default;
    GrpcConnection(std::shared_ptr<grpc::Channel> channel, int id);
    void subscriber();
    void publisher();

private:
    int id;
    std::unique_ptr<base::NetworkService::Stub> stub;
    std::unique_ptr<base::ClientId> source;
    std::unique_ptr<base::NameSpace> name_space;
};
