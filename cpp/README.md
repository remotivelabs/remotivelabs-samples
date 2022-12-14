# Get vehicle traffic from cloud

## Build and run from Ubuntu 18

from **this** folder do:

This project can compile in the official _Ubuntu 18.04_ container on _Docker hub_.

    docker pull ubuntu:focal

    docker run -it -v $PWD:/my_mouted_folder ubuntu:focal /bin/bash

Run container in your environment and install the following packets.

```sh
apt-get update
apt install libgrpc++-dev build-essential cmake protobuf-compiler libprotobuf-dev protobuf-compiler-grpc
```

Generate Protobuffer and gRPC stubs:

```sh
cd my_mouted_folder/cpp
protoc  -I proto_files proto_files/common.proto proto_files/network_api.proto --cpp_out=proto_files --grpc_out=proto_files --plugin=protoc-gen-grpc=`which grpc_cpp_plugin`
```

To build
```

cd my_mouted_folder/cpp # same folder as above
mkdir build-dir
cd build-dir
cmake ..
make
```


## Start the cloud (if you haven't done so already)

Go here https://remotivelabs.com/get-started/ follow the guide so you have flowing traffic, make sure to hit play. Also make sure to note the **url** and the **api-key**.

## Execute the binary by doing

Make sure the credentials match, go to the https://cloud.remotivelabs.com, and start the recording, click play.

```
GRPC_VERBOSITY=debug ./grpc_connection vhal-robert-beamydemo2-jrjbkq2tja-ez.a.run.app:443 092F8411-2D702818-531F3079-B7836BCD
```

