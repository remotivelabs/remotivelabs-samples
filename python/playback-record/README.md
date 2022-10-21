# Playback
Playback folder contains one script, **playback.py**. The script can start one or multiple playbacks and holds various functions to listen and/or subscribe to signals. This with intention to give example and inspiration to further development. To get started and to get more details of the examples, continue reading.

## Pre-requisites

As all python samples in this repository, the pip package [remotivelabs-broker](https://pypi.org/project/remotivelabs-broker/) is required. Install all requirements with [pip](https://pypi.org/):

    pip install -r requirements.txt

## Get started
### Options
The script playback.py can be started with options `-h` or `--url <URL>`.
* `--url <URL>` - Points to the ip of your RemotiveBroker installation, if this option is not used the scripts will use ip `127.0.0.1`. For example start the script by typing: `python3 playback.py --url http://192.168.xxx.xxx`
* `-h` - Help, shows available options for script, run `python3 playback.py -h`

### Default instructions
1. Run shell (terminal, powershell, etc.).
2. From [this directory](.) run:

```sh
python playback.py --url <address>
```

### Overview
A bunch of things are going on in this examples and it all starts in the main function `def run(argv):`. Lets break it down.

#### Setting up stubs and configuration
First we start of with setting up a connection to the RemotiveBroker (with the ip that was passed to the script) and then defining the gRPC stubs that will be used. In code it typically looks like this:

```python
intercept_channel = helper.create_channel(url, x_api_key)
network_stub = broker.network_api_pb2_grpc.NetworkServiceStub(intercept_channel)
system_stub = broker.system_api_pb2_grpc.SystemServiceStub(intercept_channel)
helper.check_license(system_stub)
```

#### Configuration
Playback folder contains a sample configuration, [configuration_custom_udp](configuration_custom_udp). The playback script uploads and reloads configuration with the `system_stub` that was defined above. Feel free to use your own.
It will look similar to this:
```
upload_folder(system_stub, "configuration_custom_udp")
reload_configuration(system_stub)
```

#### Upload recording
The file you want to do a playback on first needs to be uploaded.
In the script you have this part: 
```
upload_file(
  system_stub,
  "recordings/traffic.log",
  "recordings/candump_uploaded.log",
)
```
It uploads the file with the `system_stub`, second argument points to the filepath of your file (in the playback folder it exists a sample file `recordings/traffic.log`) and third argument, the path and name of the uploaded file.

#### Playback
Next part of the script creates a list, this list can contain one or several playbacksettings. Each playbacksetting needs to have a `namespace`, a `path` and a `mode`. The script continues with starting all playbacks in the list. In code it look like this:
```
playbacklist = [
  {
    "namespace": "custom_can",
    "path": "recordings/candump_uploaded.log",
    "mode": traffic_api_pb2.Mode.PLAY,
  }
]
# Starts playback
status = traffic_stub.PlayTraffic(
  traffic_api_pb2.PlaybackInfos(
    playbackInfo=list(map(create_playback_config, playbacklist))
  )
)
```

#### Support
If you have any further questions, please reach out!

