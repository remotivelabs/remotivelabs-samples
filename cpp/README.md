# Stream VSS signals from "cloud.remotivelabs.com"

The following guide contains a small cpp snippet showing how to connect to **RemotiveCloud**.
## Build and run from Ubuntu 18

    git clone https://github.com/remotivelabs/remotivelabs-samples
    cd remotivelabs-samples/cpp 

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
cd my_mouted_folder
protoc  -I proto_files proto_files/common.proto proto_files/network_api.proto --cpp_out=proto_files --grpc_out=proto_files --plugin=protoc-gen-grpc=`which grpc_cpp_plugin`
```

To build
```
cd my_mouted_folder # same folder as above
mkdir build-dir
cd build-dir
cmake ..
make
```


## Start the cloud (if you haven't done so already)

Go here https://cloud.remotivelabs.com/ follow the guide.
- make sure to select "configuration_vss"
- hit play and "got to broker". 
- once in the broker view, make sure to copy **url** and **api_key** you can find them by clicking the lower left address field.
- click the play button.

## Stream the signals to you local cpp snippet

Make sure the credentials match, go to the https://cloud.remotivelabs.com, and start the recording, click play.

```
GRPC_VERBOSITY=debug ./grpc_connection <url_without_https_prefix>:443 <api_key>
# example
GRPC_VERBOSITY=debug ./grpc_connection personal-r3f7mqsm0j-uo7acw3qiq-ez.a.run.app:443 0640E0CE-A4068A11-94CC4AFE-181D5129
```

