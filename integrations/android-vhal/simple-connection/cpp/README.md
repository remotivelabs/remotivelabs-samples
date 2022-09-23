# Get vechicle traffic from cloud

Start by doing

```
./grpc_connection vhal-robert-beamydemo2-jrjbkq2tja-ez.a.run.app:443 092F8411-2D702818-531F3079-B7836BCD
```

## Build and run from Ubuntu 18
This project can compile in the official _Ubuntu 18.04_ container on _Docker hub_.

    docker pull ubuntu:bionic

Run container in your environment and install the following packets.

```sh
apt install libgrpc++-dev build-essential cmake protobuf-compiler libprotobuf-dev protobuf-compiler-grpc
```

Generate Protobuffer and gRPC stubs:

```sh
protoc  -I proto_files proto_files/common.proto proto_files/network_api.proto --cpp_out=proto_files --grpc_out=proto_files --plugin=protoc-gen-grpc=`which grpc_cpp_plugin`
```

To build
```
mkdir build-dir
cd build-dir
cmake ..
make
```